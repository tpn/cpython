#!/usr/bin/env python3
"""
Debug test for the Windows Thread Pool API module.
This version uses minimal Python callbacks to isolate GIL issues.
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
        import traceback
        traceback.print_exc()
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
        import traceback
        traceback.print_exc()
        return None

def test_work_creation_only():
    """Test Work object creation without execution"""
    try:
        import _threadpool
        
        def simple_callback():
            print("This should not run yet")
        
        pool = _threadpool.ThreadPool()
        work = _threadpool.Work(pool, simple_callback)
        print("✓ Work object created successfully (not executed)")
        return work
    except Exception as e:
        print(f"✗ Failed to create Work object: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_minimal_callback():
    """Test with the simplest possible callback"""
    try:
        import _threadpool
        
        # Counter to track if callback was called
        call_count = [0]
        
        def minimal_callback():
            call_count[0] += 1
            # Don't print anything to avoid GIL issues
        
        pool = _threadpool.ThreadPool()
        work = _threadpool.Work(pool, minimal_callback)
        
        print("Submitting minimal work...")
        work.submit()
        
        print("Waiting for work to complete...")
        work.wait()
        
        print(f"✓ Minimal callback test completed. Call count: {call_count[0]}")
        return True
    except Exception as e:
        print(f"✗ Minimal callback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run debug tests"""
    print("Debug Windows Thread Pool API Test")
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
    
    # Test 3: Work creation (no execution)
    work = test_work_creation_only()
    if work is None:
        print("Cannot proceed without Work object")
        return
    
    print()
    
    # Test 4: Minimal callback
    test_minimal_callback()
    
    print()
    print("Debug tests completed!")

if __name__ == "__main__":
    main() 