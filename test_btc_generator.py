# FILENAME: test_btc_generator.py  
# ACTION: CREATE NEW FILE
# DESCRIPTION: Test BTC pairlist generation with proper volume thresholds

#!/usr/bin/env python3
"""
Test BTC Pairlist Generation
"""
import sys
import logging
from pathlib import Path

# Add path for imports
sys.path.insert(0, str(Path(__file__).parent))

from pairlist_generator import PairlistGenerator

def test_btc_volume():
    """Test BTC pair volume detection"""
    print("🧪 Testing BTC Pair Volume Detection")
    print("=" * 50)
    
    generator = None
    try:
        generator = PairlistGenerator(quote_currency='BTC')
        
        # Test with very low volume threshold for BTC
        print("📊 Fetching BTC pairs with volume data...")
        pairs_data = generator.get_exchange_pairs_with_volume(0.1)  # Very low threshold
        
        print(f"✅ Found {len(pairs_data)} BTC pairs with volume")
        
        if pairs_data:
            # Show top 10 by volume
            sorted_pairs = sorted(pairs_data, key=lambda x: x['volume_24h'], reverse=True)[:10]
            print(f"\n📈 Top 10 BTC pairs by volume:")
            for i, pair_data in enumerate(sorted_pairs, 1):
                print(f"  {i:2d}. {pair_data['pair']:<15} Vol: {pair_data['volume_24h']:.6f} BTC")
        
        return len(pairs_data) > 0
        
    except Exception as e:
        print(f"❌ Error in volume test: {e}")
        return False
    finally:
        # Force cleanup
        if generator:
            del generator
        import gc
        gc.collect()

def test_btc_generation():
    """Test BTC pairlist generation"""
    print("\n🚀 Testing BTC Pairlist Generation")
    print("=" * 50)
    
    generator = None
    try:
        generator = PairlistGenerator(quote_currency='BTC')
        
        # Test high volume generation
        print("📊 Generating high volume BTC pairlist...")
        config = generator.generate_high_volume_pairlist(min_volume=1, max_pairs=50)
        if config and config.get('whitelist_count', 0) > 0:
            print(f"✅ Generated {config['whitelist_count']} high volume BTC pairs")
            print(f"   Sample pairs: {config['exchange']['pair_whitelist'][:5]}")
        else:
            print("❌ Failed to generate high volume BTC pairs")
            return False
        
        # Test diversified generation
        print("\n🎯 Generating diversified BTC pairlist...")
        config = generator.generate_diversified_pairlist()
        if config and config.get('whitelist_count', 0) > 0:
            print(f"✅ Generated {config['whitelist_count']} diversified BTC pairs")
            print(f"   Sample pairs: {config['exchange']['pair_whitelist'][:5]}")
            
            # Show sector breakdown
            if 'sector_breakdown' in config:
                print("   Sector breakdown:")
                for sector, pairs in config['sector_breakdown'].items():
                    if pairs:
                        print(f"     {sector}: {len(pairs)} pairs")
        else:
            print("❌ Failed to generate diversified BTC pairs")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error in generation test: {e}")
        return False
    finally:
        # Force cleanup
        if generator:
            del generator
        import gc
        gc.collect()

def main():
    """Run BTC pairlist tests"""
    print("🧪 BTC Pairlist Generator Test Suite")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    tests = [
        ("Volume Detection", test_btc_volume),
        ("Pairlist Generation", test_btc_generation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! BTC pairlist generation is working.")
        print("\n🚀 Try generating BTC pairlists:")
        print("   python pairlist_generator.py --quote BTC --all")
        print("   python pairlist_generator.py --quote BTC --high-volume --min-volume 0.5")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())