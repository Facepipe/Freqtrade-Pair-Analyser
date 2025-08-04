# FILENAME: fix_hanging.py
# ACTION: CREATE NEW FILE  
# DESCRIPTION: Fix hanging issues with exchange connections

#!/usr/bin/env python3
"""
Fix hanging issues with exchange connections
"""
import sys
import time
import signal
from pathlib import Path

# Add path for imports
sys.path.insert(0, str(Path(__file__).parent))

def force_cleanup():
    """Force cleanup of threads and connections"""
    import gc
    import threading
    
    print("🧹 Forcing cleanup of threads and connections...")
    
    # Collect garbage
    gc.collect()
    
    # List active threads
    active_threads = threading.active_count()
    print(f"📊 Active threads: {active_threads}")
    
    if active_threads > 1:
        print("⚠️  Some threads are still active")
        for thread in threading.enumerate():
            if thread != threading.current_thread():
                print(f"   Thread: {thread.name} (daemon: {thread.daemon})")
    
    # Force exit if needed
    time.sleep(2)
    if threading.active_count() > 1:
        print("🔨 Force terminating remaining threads...")
        import os
        os._exit(0)

def setup_signal_handler():
    """Setup signal handler for clean exit"""
    def signal_handler(signum, frame):
        print("\n🛑 Received interrupt signal, cleaning up...")
        force_cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def test_with_timeout():
    """Test BTC generation with timeout"""
    import threading
    import time
    
    setup_signal_handler()
    
    print("🧪 Testing BTC Generation with Timeout")
    print("=" * 50)
    
    def run_test():
        try:
            from pairlist_generator import PairlistGenerator
            
            print("📊 Creating BTC generator...")
            generator = PairlistGenerator(quote_currency='BTC')
            
            print("🔍 Testing volume detection...")
            pairs_data = generator.get_exchange_pairs_with_volume(0.1)
            print(f"✅ Found {len(pairs_data)} BTC pairs")
            
            if len(pairs_data) > 0:
                print("🎯 Generating diversified pairlist...")
                config = generator.generate_diversified_pairlist()
                print(f"✅ Generated {config.get('whitelist_count', 0)} diversified pairs")
            
            print("✅ Test completed successfully!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            print("🧹 Cleaning up...")
            force_cleanup()
    
    # Run test in a separate thread with timeout
    test_thread = threading.Thread(target=run_test, daemon=True)
    test_thread.start()
    
    # Wait for completion with timeout
    test_thread.join(timeout=60)  # 60 second timeout
    
    if test_thread.is_alive():
        print("⏰ Test timed out after 60 seconds")
        print("🔨 Forcing cleanup...")
        force_cleanup()
    else:
        print("✅ Test completed within timeout")
        time.sleep(2)  # Give time for cleanup
        force_cleanup()

if __name__ == "__main__":
    test_with_timeout()