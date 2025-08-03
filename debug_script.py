#!/usr/bin/env python3
"""
Simple test script to verify the analyzer is working
Run this from your pair_analyzer directory
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all imports work"""
    logger.info("Testing imports...")
    
    try:
        import freqtrade
        logger.info("✓ Freqtrade imported successfully")
    except ImportError as e:
        logger.error(f"✗ Freqtrade import failed: {e}")
        return False
    
    try:
        from utils.config_handler import load_config
        logger.info("✓ Config handler imported successfully")
    except ImportError as e:
        logger.error(f"✗ Config handler import failed: {e}")
        return False
    
    try:
        from utils.data_handler import VersionedAnalyzer
        logger.info("✓ VersionedAnalyzer imported successfully")
    except ImportError as e:
        logger.error(f"✗ VersionedAnalyzer import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    logger.info("Testing configuration...")
    
    try:
        from utils.config_handler import load_config
        config = load_config('USDT')
        logger.info("✓ Configuration loaded successfully")
        logger.info(f"  Exchange: {config['exchange']['name']}")
        logger.info(f"  Data directory: {config['datadir']}")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration loading failed: {e}")
        return False

def test_exchange():
    """Test exchange connection"""
    logger.info("Testing exchange connection...")
    
    try:
        from utils.config_handler import load_config
        from freqtrade.resolvers import ExchangeResolver
        
        config = load_config('USDT')
        exchange = ExchangeResolver.load_exchange(config, validate=False)
        logger.info(f"✓ Exchange connected: {exchange.name}")
        
        markets = exchange.get_markets()
        logger.info(f"✓ Markets loaded: {len(markets)} pairs")
        
        # Count USDT pairs
        usdt_pairs = [p for p in markets if p.endswith('/USDT') and markets[p].get('active', False)]
        logger.info(f"✓ Active USDT pairs: {len(usdt_pairs)}")
        
        if usdt_pairs:
            logger.info(f"  Sample pairs: {usdt_pairs[:5]}")
            return True
        else:
            logger.warning("No active USDT pairs found")
            return False
            
    except Exception as e:
        logger.error(f"✗ Exchange connection failed: {e}")
        return False

def test_analyzer():
    """Test the analyzer initialization"""
    logger.info("Testing analyzer initialization...")
    
    try:
        from utils.data_handler import VersionedAnalyzer
        
        analyzer = VersionedAnalyzer(quote_currency='USDT', max_workers=1)
        logger.info(f"✓ Analyzer initialized: v{analyzer.version}")
        
        # Test getting valid pairs
        pairs = analyzer._get_valid_pairs()
        logger.info(f"✓ Found {len(pairs)} valid pairs")
        
        if pairs:
            logger.info(f"  Sample pairs: {pairs[:5]}")
            return True
        else:
            logger.warning("No valid pairs found")
            return False
            
    except Exception as e:
        logger.error(f"✗ Analyzer initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("FREQTRADE PAIR ANALYZER - TEST SUITE")
    logger.info("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Exchange Connection", test_exchange),
        ("Analyzer", test_analyzer)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            result = test_func()
            results.append(result)
            logger.info(f"{'✓ PASSED' if result else '✗ FAILED'}: {test_name}")
        except Exception as e:
            logger.error(f"✗ ERROR in {test_name}: {e}")
            results.append(False)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    passed = sum(results)
    total = len(results)
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✓ All tests passed! Your analyzer should work correctly.")
        logger.info("Try running: python pair_analyzer.py --quote USDT --workers 2")
    else:
        logger.error("✗ Some tests failed. Check the errors above.")
        
        # Provide specific guidance
        if not results[0]:  # Imports failed
            logger.error("Fix: Install missing dependencies with: pip install freqtrade talib pandas numpy")
        if not results[1]:  # Config failed
            logger.error("Fix: Check your freqtrade configuration files")
        if not results[2]:  # Exchange failed
            logger.error("Fix: Check your internet connection and exchange configuration")
        if not results[3]:  # Analyzer failed
            logger.error("Fix: Check the analyzer logs above for specific errors")

if __name__ == "__main__":
    main()