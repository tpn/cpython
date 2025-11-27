/*
 * Support for Windows Thread Pool API
 */

#ifndef Py_BUILD_CORE_BUILTIN
#  define Py_BUILD_CORE_MODULE 1
#endif

#include "Python.h"

#define WINDOWS_LEAN_AND_MEAN
#include <windows.h>
#include <threadpoolapiset.h>

/*
 * Map Windows error codes to subclasses of OSError
 */
static PyObject *
SetFromWindowsErr(DWORD err)
{
    PyObject *exception_type;

    if (err == 0)
        err = GetLastError();
    switch (err) {
        case ERROR_ACCESS_DENIED:
            exception_type = PyExc_PermissionError;
            break;
        case ERROR_INVALID_PARAMETER:
            exception_type = PyExc_ValueError;
            break;
        default:
            exception_type = PyExc_OSError;
    }
    return PyErr_SetExcFromWindowsErr(exception_type, err);
}

/*
 * Callback data structure to bridge C callbacks to Python
 */
typedef struct {
    PyObject *callback;
    PyObject *context;
} CallbackData;

/*
 * ThreadPool object
 */
typedef struct {
    PyObject_HEAD
    PTP_POOL pool;
} ThreadPoolObject;

/*
 * Work object
 */
typedef struct {
    PyObject_HEAD
    PTP_WORK work;
    PyObject *callback;
    PyObject *context;
    ThreadPoolObject *pool_obj;
    CallbackData *callback_data;
} WorkObject;

static PyTypeObject *ThreadPoolType = NULL;
static PyTypeObject *WorkType = NULL;

/*
 * C callback function that bridges to Python
 * 
 * This function is called from Windows thread pool threads,
 * so we need to be very careful about GIL management.
 */
static VOID CALLBACK
WorkCallback(PTP_CALLBACK_INSTANCE Instance, PVOID Context, PTP_WORK Work)
{
    CallbackData *data = (CallbackData*)Context;
    PyObject *result = NULL;
    PyGILState_STATE gstate;
    PyThreadState *tstate = NULL;
    int gil_acquired = 0;
    
    if (data == NULL || data->callback == NULL) {
        return;
    }
    
    // For free-threading builds, we need to handle thread state more carefully
    // First, try the standard approach
    tstate = PyGILState_GetThisThreadState();
    if (tstate == NULL) {
        // Thread doesn't have a thread state, try to acquire GIL differently
        // This is a fallback for threads not created by Python
        gstate = PyGILState_Ensure();
        gil_acquired = 1;
    } else {
        // Thread already has state, just ensure GIL
        gstate = PyGILState_Ensure();
        gil_acquired = 1;
    }
    
    if (!gil_acquired) {
        // Could not acquire GIL, skip callback execution
        return;
    }
    
    // Double-check that we have a valid thread state
    if (PyErr_Occurred()) {
        PyErr_Clear();
    }
    
    // Call the Python callback with proper error handling
    if (data->context && data->context != Py_None) {
        result = PyObject_CallOneArg(data->callback, data->context);
    } else {
        result = PyObject_CallNoArgs(data->callback);
    }
    
    // Handle any exceptions that occurred
    if (result == NULL) {
        // Print the exception and clear it
        if (PyErr_Occurred()) {
            PyErr_Print();
            PyErr_Clear();
        }
    } else {
        Py_DECREF(result);
    }
    
    // Release the GIL
    if (gil_acquired) {
        PyGILState_Release(gstate);
    }
}

/*
 * ThreadPool methods
 */

static PyObject *
ThreadPool_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    ThreadPoolObject *self;
    PTP_POOL pool;

    if (!PyArg_ParseTuple(args, ""))
        return NULL;

    pool = CreateThreadpool(NULL);
    if (pool == NULL) {
        return SetFromWindowsErr(0);
    }

    self = (ThreadPoolObject *)type->tp_alloc(type, 0);
    if (self == NULL) {
        CloseThreadpool(pool);
        return NULL;
    }

    self->pool = pool;
    return (PyObject *)self;
}

static void
ThreadPool_dealloc(ThreadPoolObject *self)
{
    if (self->pool != NULL) {
        CloseThreadpool(self->pool);
    }
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *
ThreadPool_set_thread_maximum(ThreadPoolObject *self, PyObject *args)
{
    DWORD max_threads;
    
    if (!PyArg_ParseTuple(args, "k", &max_threads))
        return NULL;
    
    SetThreadpoolThreadMaximum(self->pool, max_threads);
    Py_RETURN_NONE;
}

static PyObject *
ThreadPool_set_thread_minimum(ThreadPoolObject *self, PyObject *args)
{
    DWORD min_threads;
    
    if (!PyArg_ParseTuple(args, "k", &min_threads))
        return NULL;
    
    BOOL result = SetThreadpoolThreadMinimum(self->pool, min_threads);
    return PyBool_FromLong(result);
}

static PyMethodDef ThreadPool_methods[] = {
    {"set_thread_maximum", (PyCFunction)ThreadPool_set_thread_maximum, METH_VARARGS, "Set maximum threads"},
    {"set_thread_minimum", (PyCFunction)ThreadPool_set_thread_minimum, METH_VARARGS, "Set minimum threads"},
    {NULL}
};

static PyTypeObject ThreadPoolType_def = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_threadpool.ThreadPool",
    .tp_doc = "Windows Thread Pool",
    .tp_basicsize = sizeof(ThreadPoolObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = ThreadPool_new,
    .tp_dealloc = (destructor)ThreadPool_dealloc,
    .tp_methods = ThreadPool_methods,
};

/*
 * Work methods
 */

static PyObject *
Work_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    WorkObject *self;
    PyObject *pool;
    PyObject *callback;
    PyObject *context = NULL;
    ThreadPoolObject *pool_obj;
    PTP_WORK work;
    TP_CALLBACK_ENVIRON callback_env;
    CallbackData *callback_data;

    if (!PyArg_ParseTuple(args, "OO|O", &pool, &callback, &context))
        return NULL;

    // Validate pool argument
    if (!PyObject_TypeCheck(pool, &ThreadPoolType_def)) {
        PyErr_SetString(PyExc_TypeError, "pool must be a ThreadPool instance");
        return NULL;
    }
    pool_obj = (ThreadPoolObject *)pool;

    // Validate callback argument
    if (!PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "callback must be callable");
        return NULL;
    }

    // Allocate callback data
    callback_data = PyMem_Malloc(sizeof(CallbackData));
    if (callback_data == NULL) {
        return PyErr_NoMemory();
    }

    callback_data->callback = Py_NewRef(callback);
    callback_data->context = context ? Py_NewRef(context) : NULL;

    // Initialize callback environment and associate with pool
    InitializeThreadpoolEnvironment(&callback_env);
    SetThreadpoolCallbackPool(&callback_env, pool_obj->pool);

    // Create the work object
    work = CreateThreadpoolWork(WorkCallback, callback_data, &callback_env);
    if (work == NULL) {
        Py_DECREF(callback_data->callback);
        Py_XDECREF(callback_data->context);
        PyMem_Free(callback_data);
        DestroyThreadpoolEnvironment(&callback_env);
        return SetFromWindowsErr(0);
    }

    self = (WorkObject *)type->tp_alloc(type, 0);
    if (self == NULL) {
        CloseThreadpoolWork(work);
        Py_DECREF(callback_data->callback);
        Py_XDECREF(callback_data->context);
        PyMem_Free(callback_data);
        DestroyThreadpoolEnvironment(&callback_env);
        return NULL;
    }

    self->work = work;
    self->callback = Py_NewRef(callback);
    self->context = context ? Py_NewRef(context) : NULL;
    self->pool_obj = (ThreadPoolObject *)Py_NewRef(pool);
    self->callback_data = callback_data;

    return (PyObject *)self;
}

static void
Work_dealloc(WorkObject *self)
{
    if (self->work != NULL) {
        // Wait for any pending work to complete before closing
        WaitForThreadpoolWorkCallbacks(self->work, TRUE);
        CloseThreadpoolWork(self->work);
    }

    // Clean up callback data
    if (self->callback_data != NULL) {
        Py_XDECREF(self->callback_data->callback);
        Py_XDECREF(self->callback_data->context);
        PyMem_Free(self->callback_data);
    }

    Py_XDECREF(self->callback);
    Py_XDECREF(self->context);
    Py_XDECREF(self->pool_obj);

    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *
Work_submit(WorkObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;
    
    SubmitThreadpoolWork(self->work);
    Py_RETURN_NONE;
}

static PyObject *
Work_wait(WorkObject *self, PyObject *args)
{
    int cancel_pending = 0;
    
    if (!PyArg_ParseTuple(args, "|i", &cancel_pending))
        return NULL;
    
    Py_BEGIN_ALLOW_THREADS
    WaitForThreadpoolWorkCallbacks(self->work, cancel_pending ? TRUE : FALSE);
    Py_END_ALLOW_THREADS
    
    Py_RETURN_NONE;
}

static int
Work_traverse(WorkObject *self, visitproc visit, void *arg)
{
    Py_VISIT(self->callback);
    Py_VISIT(self->context);
    Py_VISIT(self->pool_obj);
    return 0;
}

static int
Work_clear(WorkObject *self)
{
    Py_CLEAR(self->callback);
    Py_CLEAR(self->context);
    Py_CLEAR(self->pool_obj);
    return 0;
}

static PyMethodDef Work_methods[] = {
    {"submit", (PyCFunction)Work_submit, METH_VARARGS, "Submit work"},
    {"wait", (PyCFunction)Work_wait, METH_VARARGS, "Wait for completion"},
    {NULL}
};

static PyTypeObject WorkType_def = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_threadpool.Work",
    .tp_doc = "Windows Thread Pool Work Item",
    .tp_basicsize = sizeof(WorkObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_new = Work_new,
    .tp_dealloc = (destructor)Work_dealloc,
    .tp_traverse = (traverseproc)Work_traverse,
    .tp_clear = (inquiry)Work_clear,
    .tp_methods = Work_methods,
};

static PyMethodDef threadpool_functions[] = {
    {NULL}
};

static int
threadpool_exec(PyObject *module)
{
    // Initialize type objects
    if (PyType_Ready(&ThreadPoolType_def) < 0)
        return -1;
    
    if (PyType_Ready(&WorkType_def) < 0)
        return -1;
    
    // Add types to module
    Py_INCREF(&ThreadPoolType_def);
    if (PyModule_AddObject(module, "ThreadPool", (PyObject *)&ThreadPoolType_def) < 0) {
        Py_DECREF(&ThreadPoolType_def);
        return -1;
    }
    
    Py_INCREF(&WorkType_def);
    if (PyModule_AddObject(module, "Work", (PyObject *)&WorkType_def) < 0) {
        Py_DECREF(&WorkType_def);
        return -1;
    }
    
    // Set global references for type checking
    ThreadPoolType = &ThreadPoolType_def;
    WorkType = &WorkType_def;
    
    return 0;
}

static PyModuleDef_Slot threadpool_slots[] = {
    {Py_mod_exec, threadpool_exec},
#ifdef Py_MOD_GIL_NOT_USED
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, NULL}
};

static struct PyModuleDef threadpool_module = {
    PyModuleDef_HEAD_INIT,
    "_threadpool",
    "Windows Thread Pool API support",
    0,
    threadpool_functions,
    threadpool_slots,
};

PyMODINIT_FUNC
PyInit__threadpool(void)
{
    return PyModuleDef_Init(&threadpool_module);
}