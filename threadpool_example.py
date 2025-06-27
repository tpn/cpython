#!/usr/bin/env python3
"""
Example usage of the Windows Thread Pool API Python module.

This demonstrates creating thread pools, submitting work items,
and managing concurrent execution.
"""

import _threadpool
import time
import threading

def worker_function(data=None):
    """Simple worker function that prints a message and sleeps."""
    thread_id = threading.get_ident()
    print(f"Worker executing on thread {thread_id} with data: {data}")
    time.sleep(1)  # Simulate some work
    print(f"Worker on thread {thread_id} completed")

def cpu_intensive_task(n):
    """CPU-intensive task for testing."""
    result = 0
    for i in range(n):
        result += i * i
    thread_id = threading.get_ident()
    print(f"CPU task completed on thread {thread_id}, result: {result}")
    return result

def main():
    print("Windows Thread Pool API Example")
    print("=" * 40)
    
    # Create a new thread pool
    print("Creating thread pool...")
    pool = _threadpool.ThreadPool()
    
    # Configure thread pool parameters
    print("Configuring thread pool...")
    pool.set_thread_minimum(2)  # At least 2 threads
    pool.set_thread_maximum(8)  # At most 8 threads
    
    # Example 1: Simple work items with different data
    print("\nExample 1: Simple work items")
    work_items = []
    
    for i in range(5):
        work = _threadpool.Work(pool, worker_function, f"Task {i+1}")
        work_items.append(work)
        work.submit()
    
    # Wait for all work to complete
    for work in work_items:
        work.wait()
    
    print("All simple work items completed!")
    
    # Example 2: CPU-intensive tasks
    print("\nExample 2: CPU-intensive tasks")
    cpu_work_items = []
    
    for i in range(3):
        n = 1000000 * (i + 1)  # Different workloads
        work = _threadpool.Work(pool, lambda: cpu_intensive_task(n))
        cpu_work_items.append(work)
        work.submit()
    
    # Wait for CPU tasks
    for work in cpu_work_items:
        work.wait()
    
    print("All CPU-intensive tasks completed!")
    
    # Example 3: Batch processing
    print("\nExample 3: Batch processing with context")
    batch_size = 10
    batch_work = []
    
    def process_batch_item(item_id):
        print(f"Processing batch item {item_id}")
        time.sleep(0.5)
        print(f"Batch item {item_id} processed")
    
    for i in range(batch_size):
        work = _threadpool.Work(pool, process_batch_item, i)
        batch_work.append(work)
        work.submit()
    
    # Wait for batch processing
    for work in batch_work:
        work.wait()
    
    print("Batch processing completed!")
    
    print("\nAll examples completed successfully!")

if __name__ == "__main__":
    main() 