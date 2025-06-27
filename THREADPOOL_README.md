# Windows Thread Pool API Module

## Overview

This module (`_threadpool`) exposes the Windows Thread Pool API as native Python APIs, allowing Python developers to efficiently manage and execute concurrent work items using the operating system's thread pool infrastructure.

## Features

- **ThreadPool**: Create and manage Windows thread pools
- **Work**: Submit callable Python functions as work items to thread pools
- **Automatic GIL Management**: The module properly handles Python's Global Interpreter Lock (GIL) when executing callbacks
- **Memory Management**: Proper cleanup of resources and Python objects
- **Error Handling**: Windows errors are mapped to appropriate Python exceptions

## Classes

### ThreadPool

Represents a Windows thread pool that can execute work items concurrently.

#### Constructor
```python
pool = _threadpool.ThreadPool()
```

#### Methods

- `set_thread_maximum(max_threads)`: Set the maximum number of threads in the pool
- `set_thread_minimum(min_threads)`: Set the minimum number of threads in the pool

### Work

Represents a work item that can be submitted to a thread pool for execution.

#### Constructor
```python
work = _threadpool.Work(pool, callback, context=None)
```

Parameters:
- `pool`: A ThreadPool instance
- `callback`: A callable Python object (function, method, etc.)
- `context`: Optional data to pass to the callback (default: None)

#### Methods

- `submit()`: Submit the work item to the thread pool for execution
- `wait(cancel_pending=False)`: Wait for all callbacks to complete
  - `cancel_pending`: If True, cancels pending callbacks

## Usage Examples

### Basic Usage

```python
import _threadpool
import time

def worker_task(data):
    print(f"Processing: {data}")
    time.sleep(1)
    print(f"Completed: {data}")

# Create thread pool
pool = _threadpool.ThreadPool()
pool.set_thread_minimum(2)
pool.set_thread_maximum(8)

# Create and submit work
work = _threadpool.Work(pool, worker_task, "Important Task")
work.submit()

# Wait for completion
work.wait()
```

### Multiple Work Items

```python
import _threadpool

def process_item(item_id):
    # Process item
    result = item_id * 2
    print(f"Processed item {item_id}, result: {result}")

pool = _threadpool.ThreadPool()
work_items = []

# Submit multiple work items
for i in range(10):
    work = _threadpool.Work(pool, process_item, i)
    work.submit()
    work_items.append(work)

# Wait for all to complete
for work in work_items:
    work.wait()
```

### CPU-Intensive Tasks

```python
import _threadpool

def cpu_task():
    # CPU-intensive computation
    result = sum(i * i for i in range(1000000))
    return result

pool = _threadpool.ThreadPool()
pool.set_thread_maximum(4)  # Limit for CPU-bound tasks

# Submit CPU tasks
cpu_work = []
for _ in range(4):
    work = _threadpool.Work(pool, cpu_task)
    work.submit()
    cpu_work.append(work)

# Wait for completion
for work in cpu_work:
    work.wait()
```

## Benefits

### Performance
- **Lower Overhead**: Windows thread pools reuse threads, reducing the overhead of thread creation and destruction
- **Better Resource Management**: The OS manages thread lifecycle efficiently
- **Scalability**: Thread pools can dynamically adjust the number of threads based on workload

### Integration with Free-Threading Python
- **GIL Compatibility**: The module is designed to work with Python's free-threading support
- **True Parallelism**: When used with free-threading builds, Python code can achieve true parallelism
- **Resource Efficiency**: Better utilization of multi-core systems

## Technical Details

### Implementation Notes

1. **Callback Bridging**: The module uses a C callback function to bridge between Windows API callbacks and Python callables
2. **GIL Management**: Properly acquires and releases the GIL when calling Python code from worker threads
3. **Memory Safety**: Uses proper reference counting and cleanup to prevent memory leaks
4. **Error Handling**: Windows error codes are translated to appropriate Python exceptions

### Architecture

```
Python Code
    ↓
_threadpool Module (C Extension)
    ↓
Windows Thread Pool API
    ↓
Operating System Threads
```

### Thread Safety

- Thread pools and work objects are designed to be used from multiple threads
- The module handles synchronization internally
- Python callbacks should be thread-safe if shared data is accessed

## Requirements

- Windows Vista or later (Windows Thread Pool API requires Vista+)
- Python 3.12+ (for free-threading support)
- Windows development environment with access to `threadpoolapiset.h`

## Building

The module should be built as part of the CPython build process:

1. Place `threadpoolmodule.c` in the `Modules/` directory
2. Update the build configuration to include the module
3. Ensure linking with `kernel32.lib` for thread pool functions

## Error Handling

The module maps Windows error codes to Python exceptions:

- `ERROR_ACCESS_DENIED` → `PermissionError`
- `ERROR_INVALID_PARAMETER` → `ValueError`
- Other errors → `OSError`

## Best Practices

1. **Pool Configuration**: Set appropriate minimum and maximum thread counts based on your workload
2. **Work Item Size**: Balance between work item granularity and overhead
3. **Resource Cleanup**: Always wait for work completion before destroying pools
4. **Exception Handling**: Handle exceptions in your callback functions to prevent thread termination
5. **Thread-Safe Code**: Ensure your callbacks are thread-safe when accessing shared resources

## Comparison with Other Threading Approaches

| Approach | Thread Creation Overhead | Resource Management | Scalability | Python Integration |
|----------|-------------------------|--------------------|--------------|--------------------|
| `threading.Thread` | High | Manual | Limited | Native |
| `concurrent.futures.ThreadPoolExecutor` | Medium | Automatic | Good | Native |
| `_threadpool` (this module) | Low | OS-managed | Excellent | Native with OS benefits |

The Windows Thread Pool API provides the best performance and resource management for Windows-specific applications, especially when combined with Python's free-threading capabilities. 