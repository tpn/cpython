#!/usr/bin/env python3
"""
Simple test for the Windows Thread Pool API module.
This tests the simplified version without Argument Clinic.
"""

import sys
import time
import threading

def test_basic_import():
    """Test basic module import"""
    try:
        import _threadpool
        print("✓ Module imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import module: {e}")
        return False

def test_threadpool_creation():
    """Test ThreadPool creation"""
    try:
        import _threadpool
        pool = _threadpool.ThreadPool()
        print("✓ ThreadPool created successfully")
        return pool
    except Exception as e:
        print(f"✗ Failed to create ThreadPool: {e}")
        return None

def test_work_creation(pool):
    """Test Work object creation"""
    try:
        import _threadpool
        
        def simple_callback():
            print(f"Callback executed on thread {threading.get_ident()}")
        
        work = _threadpool.Work(pool, simple_callback)
        print("✓ Work object created successfully")
        return work
    except Exception as e:
        print(f"✗ Failed to create Work object: {e}")
        return None

def test_work_execution(work):
    """Test work execution"""
    try:
        print("Submitting work...")
        work.submit()
        print("Waiting for work to complete...")
        work.wait()
        print("✓ Work executed successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to execute work: {e}")
        return False

def test_with_context():
    """Test work with context data"""
    try:
        import _threadpool
        
        pool = _threadpool.ThreadPool()
        results = []
        
        def callback_with_data(data):
            thread_id = threading.get_ident()
            results.append((data, thread_id))
            print(f"Callback with data '{data}' on thread {thread_id}")
        
        # Create multiple work items with different data
        work_items = []
        for i in range(3):
            work = _threadpool.Work(pool, callback_with_data, f"Task-{i}")
            work_items.append(work)
        
        # Submit all work
        for work in work_items:
            work.submit()
        
        # Wait for all work to complete
        for work in work_items:
            work.wait()
        
        print(f"✓ Context test completed. Results: {results}")
        return len(results) == 3
    except Exception as e:
        print(f"✗ Context test failed: {e}")
        return False

def test_thread_pool_configuration():
    """Test thread pool configuration"""
    try:
        import _threadpool
        
        pool = _threadpool.ThreadPool()
        
        # Test setting minimum threads
        result = pool.set_thread_minimum(2)
        print(f"Set minimum threads result: {result}")
        
        # Test setting maximum threads
        pool.set_thread_maximum(8)
        print("✓ Thread pool configuration successful")
        return True
    except Exception as e:
        print(f"✗ Thread pool configuration failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Simple Windows Thread Pool API Test")
    print("=" * 40)
    
    # Test 1: Import
    if not test_basic_import():
        print("Cannot proceed without successful import")
        return
    
    print()
    
    # Test 2: ThreadPool creation
    pool = test_threadpool_creation()
    if pool is None:
        print("Cannot proceed without ThreadPool")
        return
    
    print()
    
    # Test 3: Thread pool configuration
    test_thread_pool_configuration()
    print()
    
    # Test 4: Work creation
    work = test_work_creation(pool)
    if work is None:
        print("Cannot proceed without Work object")
        return
    
    print()
    
    # Test 5: Work execution
    test_work_execution(work)
    print()
    
    # Test 6: Context data
    test_with_context()
    print()
    
    print("All tests completed!")

if __name__ == "__main__":
    main() 