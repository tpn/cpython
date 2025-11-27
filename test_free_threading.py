import _threadpool
import time
import threading
import sys

def work_callback():
    print(f"Work executing on thread {threading.get_ident()}")
    time.sleep(1)
    print(f"Work finished on thread {threading.get_ident()}")

def main():
    print(f"Main thread: {threading.get_ident()}")
    
    # Check if we are running with GIL disabled (Python 3.13+ free-threaded build)
    is_free_threaded = False
    if hasattr(sys, "_is_gil_enabled"):
        is_free_threaded = not sys._is_gil_enabled()
    
    print(f"Free-threading enabled: {is_free_threaded}")
    
    pool = _threadpool.ThreadPool()
    pool.set_thread_maximum(4)
    pool.set_thread_minimum(2)
    
    works = []
    for i in range(4):
        work = _threadpool.Work(pool, work_callback)
        works.append(work)
        print(f"Submitting work {i}")
        work.submit()
    
    print("Waiting for work to complete...")
    for work in works:
        work.wait()
    
    print("All work completed")

if __name__ == "__main__":
    main()
