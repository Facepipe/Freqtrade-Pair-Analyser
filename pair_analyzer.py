#!/usr/bin/env python3
"""
Freqtrade Pair Analyzer Pro - Main Entry Point
Version History:
• v1.3.1 - Updated to work with fixed analyzer_core
• v1.3.0 - Supports automatic data downloading
"""
import argparse
import logging
from typing import List, Dict
from analyzer_core import VersionedAnalyzer

# Configure logging
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler('pair_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Freqtrade Pair Analyzer')
    parser.add_argument('--quote', type=str, required=True, help='Quote currency (e.g. USDT, BTC)')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers (default: 4)')
    return parser.parse_args()

if __name__ == '__main__':
    try:
        args = parse_args()
        
        logger.info("Starting analysis process")
        analyzer = VersionedAnalyzer(
            quote_currency=args.quote,
            max_workers=args.workers
        )
        
        # Run analysis (automatically handles data downloading)
        results, failed_pairs = analyzer.run_analysis()
        report = analyzer.save_results(results, failed_pairs)
        
        # Display results
        print("\nAnalysis Summary:")
        print(f"Total pairs analyzed: {len(results) + len(failed_pairs)}")
        print(f"Successful pairs: {len(results)}")
        print(f"Pairs with issues: {len(failed_pairs)}")
        
        if report['top_pairs']:
            print("\nTop 10 Pairs:")
            for i, pair in enumerate(report['top_pairs'], 1):
                print(f"{i}. {pair}")
        else:
            print("\nNo valid pairs found - check logs for details")
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise