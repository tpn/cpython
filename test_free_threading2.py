import _threadpool
import threading
import sys

class AtomicCounter:
    def __init__(self, initial_value=0):
        self._value = initial_value
        self._lock = threading.Lock()

    def increment(self, amount=1):
        with self._lock:
            self._value += amount
            return self._value

    def decrement(self, amount=1):
        with self._lock:
            self._value -= amount
            return self._value

    @property
    def value(self):
        with self._lock:
            return self._value

def main():
    print(f"Main thread: {threading.get_ident()}")
    
    # Check if we are running with GIL disabled (Python 3.13+ free-threaded build)
    is_free_threaded = False
    if hasattr(sys, "_is_gil_enabled"):
        is_free_threaded = not sys._is_gil_enabled()
    
    print(f"Free-threading enabled: {is_free_threaded}")

    CONCURRENCY = 4
    
    pool = _threadpool.ThreadPool()
    pool.set_thread_maximum(CONCURRENCY)
    pool.set_thread_minimum(CONCURRENCY)

    results = [None] * CONCURRENCY

    decrementer = AtomicCounter(initial_value=CONCURRENCY)
    incrementer = AtomicCounter()

    # Created a "finished" event.
    finished = threading.Event()

    def work_callback():
        work_id = threading.get_ident()
        tid = incrementer.increment()
        did = decrementer.decrement()
        print(f'work_id: {work_id} tid: {tid}, did: {did}')
        if did == 0:
            print(f'work_id: {work_id} finished, tid: {tid}, did: {did}')
            finished.set()
        results[tid-1] = work_id
    
    works = []
    for i in range(CONCURRENCY):
        work = _threadpool.Work(pool, work_callback)
        works.append(work)
        print(f"Submitting work {i}")
        work.submit()
    
    print("Waiting for work to complete...")
    finished.wait()
    
    print("All work completed")
    print(f'results: {results}')

    pool.shutdown()

if __name__ == "__main__":
    main()
