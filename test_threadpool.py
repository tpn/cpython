#!/usr/bin/env python3
"""
Test suite for the Windows Thread Pool API module.

This file demonstrates usage patterns and tests edge cases.
"""

import _threadpool
import time
import threading
import gc
import sys

def test_basic_functionality():
    """Test basic thread pool creation and work submission."""
    print("Testing basic functionality...")
    
    # Create thread pool
    pool = _threadpool.ThreadPool()
    
    # Configure pool
    result = pool.set_thread_minimum(1)
    assert result == True, "set_thread_minimum should succeed"
    
    pool.set_thread_maximum(4)  # Should not fail
    
    # Simple callback
    results = []
    def simple_callback():
        results.append(threading.get_ident())
    
    # Create and submit work
    work = _threadpool.Work(pool, simple_callback)
    work.submit()
    work.wait()
    
    assert len(results) == 1, "Callback should have been called once"
    print("✓ Basic functionality test passed")

def test_callback_with_context():
    """Test callbacks with context data."""
    print("Testing callbacks with context...")
    
    pool = _threadpool.ThreadPool()
    results = []
    
    def callback_with_context(data):
        results.append(data)
    
    # Test with different data types
    test_data = [42, "hello", [1, 2, 3], {"key": "value"}]
    work_items = []
    
    for data in test_data:
        work = _threadpool.Work(pool, callback_with_context, data)
        work.submit()
        work_items.append(work)
    
    # Wait for all work
    for work in work_items:
        work.wait()
    
    assert len(results) == len(test_data), f"Expected {len(test_data)} results, got {len(results)}"
    assert all(data in results for data in test_data), "All test data should be present in results"
    print("✓ Callback with context test passed")

def test_exception_handling():
    """Test exception handling in callbacks."""
    print("Testing exception handling...")
    
    pool = _threadpool.ThreadPool()
    
    def failing_callback():
        raise ValueError("This is a test exception")
    
    # Submit work that will fail
    work = _threadpool.Work(pool, failing_callback)
    work.submit()
    
    # This should not raise an exception in the main thread
    try:
        work.wait()
        print("✓ Exception handling test passed")
    except Exception as e:
        print(f"✗ Exception handling test failed: {e}")

def test_multiple_submissions():
    """Test submitting the same work multiple times."""
    print("Testing multiple submissions...")
    
    pool = _threadpool.ThreadPool()
    counter = []
    lock = threading.Lock()
    
    def counting_callback():
        with lock:
            counter.append(1)
    
    work = _threadpool.Work(pool, counting_callback)
    
    # Submit the same work multiple times
    num_submissions = 5
    for _ in range(num_submissions):
        work.submit()
    
    work.wait()
    
    # Note: The behavior here depends on the implementation
    # The same work object might be executed multiple times
    print(f"Counter has {len(counter)} entries after {num_submissions} submissions")
    print("✓ Multiple submissions test completed")

def test_concurrent_execution():
    """Test concurrent execution of multiple work items."""
    print("Testing concurrent execution...")
    
    pool = _threadpool.ThreadPool()
    pool.set_thread_minimum(4)
    pool.set_thread_maximum(4)
    
    start_times = []
    end_times = []
    lock = threading.Lock()
    
    def concurrent_callback(worker_id):
        with lock:
            start_times.append((worker_id, time.time()))
        
        # Simulate work
        time.sleep(0.5)
        
        with lock:
            end_times.append((worker_id, time.time()))
    
    # Submit multiple work items
    work_items = []
    num_workers = 4
    
    start_time = time.time()
    for i in range(num_workers):
        work = _threadpool.Work(pool, concurrent_callback, i)
        work.submit()
        work_items.append(work)
    
    # Wait for all work
    for work in work_items:
        work.wait()
    
    total_time = time.time() - start_time
    
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Start times: {sorted(start_times, key=lambda x: x[1])}")
    print(f"End times: {sorted(end_times, key=lambda x: x[1])}")
    
    # With 4 concurrent threads, total time should be ~0.5 seconds, not ~2 seconds
    if total_time < 1.0:
        print("✓ Concurrent execution test passed")
    else:
        print(f"⚠ Concurrent execution might not be working optimally (took {total_time:.2f}s)")

def test_resource_cleanup():
    """Test proper resource cleanup."""
    print("Testing resource cleanup...")
    
    # Create many pools and work items to test cleanup
    for i in range(10):
        pool = _threadpool.ThreadPool()
        
        def dummy_callback():
            pass
        
        work = _threadpool.Work(pool, dummy_callback)
        work.submit()
        work.wait()
        
        # Let objects go out of scope
        del work
        del pool
    
    # Force garbage collection
    gc.collect()
    
    print("✓ Resource cleanup test completed")

def test_edge_cases():
    """Test various edge cases."""
    print("Testing edge cases...")
    
    pool = _threadpool.ThreadPool()
    
    # Test with None context (should work)
    def callback_none_context(data):
        assert data is None
    
    work = _threadpool.Work(pool, callback_none_context, None)
    work.submit()
    work.wait()
    
    # Test with no context argument
    def callback_no_args():
        pass
    
    work = _threadpool.Work(pool, callback_no_args)
    work.submit()
    work.wait()
    
    print("✓ Edge cases test passed")

def test_type_validation():
    """Test type validation for arguments."""
    print("Testing type validation...")
    
    pool = _threadpool.ThreadPool()
    
    # Test invalid pool type
    try:
        work = _threadpool.Work("not a pool", lambda: None)
        print("✗ Should have raised TypeError for invalid pool")
    except TypeError:
        print("✓ Correctly rejected invalid pool type")
    
    # Test invalid callback type
    try:
        work = _threadpool.Work(pool, "not callable")
        print("✗ Should have raised TypeError for invalid callback")
    except TypeError:
        print("✓ Correctly rejected invalid callback type")

def benchmark_performance():
    """Benchmark thread pool performance."""
    print("Benchmarking performance...")
    
    pool = _threadpool.ThreadPool()
    pool.set_thread_maximum(8)
    
    def light_work():
        # Very light work to measure overhead
        x = sum(range(100))
        return x
    
    num_tasks = 1000
    start_time = time.time()
    
    work_items = []
    for _ in range(num_tasks):
        work = _threadpool.Work(pool, light_work)
        work.submit()
        work_items.append(work)
    
    for work in work_items:
        work.wait()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Executed {num_tasks} light tasks in {total_time:.3f} seconds")
    print(f"Average time per task: {(total_time / num_tasks) * 1000:.3f} ms")

def main():
    """Run all tests."""
    print("Windows Thread Pool API Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_callback_with_context,
        test_exception_handling,
        test_multiple_submissions,
        test_concurrent_execution,
        test_resource_cleanup,
        test_edge_cases,
        test_type_validation,
        benchmark_performance,
    ]
    
    for test in tests:
        try:
            test()
            print()
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("Test suite completed!")

if __name__ == "__main__":
    main() 