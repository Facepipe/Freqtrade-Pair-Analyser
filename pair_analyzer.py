#!/usr/bin/env python3
"""
Freqtrade Pair Analyzer Pro - Main Entry Point
Version: 2.0.0 - Fixed to use working VersionedAnalyzer
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the WORKING analyzer from data_handler, not analyzer_core
from utils.data_handler import VersionedAnalyzer

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
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Freqtrade Pair Analyzer Pro - Advanced cryptocurrency pair analysis tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pair_analyzer.py --quote USDT --workers 4 --timeframe 1h
  python pair_analyzer.py --quote USDT --workers 8 --timeframe 15m --top-pairs 20
        """
    )
    
    parser.add_argument(
        '--quote', 
        type=str, 
        required=True, 
        help='Quote currency (e.g. USDT, BTC, ETH)'
    )
    
    parser.add_argument(
        '--workers', 
        type=int, 
        default=4, 
        choices=range(1, 17),
        metavar='[1-16]',
        help='Number of parallel workers (default: 4, max: 16)'
    )
    
    parser.add_argument(
        '--timeframe', 
        type=str, 
        default='1d',
        choices=['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w'],
        help='Timeframe for analysis (default: 1d)'
    )
    
    # Support both --top-pairs and --top_pairs for compatibility
    parser.add_argument(
        '--top-pairs', '--top_pairs',
        type=int, 
        dest='top_pairs',
        default=10,
        help='Number of top pairs to display (default: 10)'
    )
    
    # Support both --least-pairs and --least_pairs for compatibility  
    parser.add_argument(
        '--least-pairs', '--least_pairs',
        type=int,
        dest='least_pairs', 
        default=10,
        help='Number of least volatile pairs to display (default: 10)'
    )
    
    parser.add_argument(
        '--days', 
        type=int, 
        default=90,
        help='Number of days of data to analyze (default: 90)'
    )
    
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()

def print_results_summary(results: List[Dict], failed_pairs: List[str], args):
    """Print a comprehensive results summary"""
    print("\n" + "="*80)
    print("FREQTRADE PAIR ANALYZER - RESULTS SUMMARY")
    print("="*80)
    
    print(f"\nConfiguration:")
    print(f"  Quote Currency: {args.quote}")
    print(f"  Timeframe: {args.timeframe}")
    print(f"  Days Analyzed: {args.days}")
    print(f"  Workers Used: {args.workers}")
    
    print(f"\nAnalysis Results:")
    print(f"  Total Pairs Processed: {len(results) + len(failed_pairs)}")
    print(f"  Successful Analyses: {len(results)}")
    print(f"  Failed Analyses: {len(failed_pairs)}")
    
    if results:
        print(f"\nTop {min(args.top_pairs, len(results))} Pairs by Composite Score:")
        for i, result in enumerate(results[:args.top_pairs], 1):
            score = result.get('composite_score', 0)
            volatility = result.get('volatility', 0)
            trend = result.get('trend_strength', 0)
            volume = result.get('volume_score', 0)
            print(f"  {i:2d}. {result['pair']:<15} "
                  f"Score: {score:.3f} | "
                  f"Vol: {volatility:.3f} | "
                  f"Trend: {trend:.1f} | "
                  f"Volume: {volume:.1f}")
        
        # Show least volatile pairs if requested
        if args.least_pairs > 0 and len(results) > args.least_pairs:
            print(f"\nLeast Volatile {args.least_pairs} Pairs:")
            least_volatile = sorted(results, key=lambda x: x.get('volatility', 0))[:args.least_pairs]
            for i, result in enumerate(least_volatile, 1):
                score = result.get('composite_score', 0)
                volatility = result.get('volatility', 0)
                trend = result.get('trend_strength', 0)
                print(f"  {i:2d}. {result['pair']:<15} "
                      f"Score: {score:.3f} | "
                      f"Vol: {volatility:.3f} | "
                      f"Trend: {trend:.1f}")
    
    if failed_pairs:
        print(f"\nPairs with Issues ({len(failed_pairs)}):")
        for i, pair in enumerate(failed_pairs[:10], 1):  # Show first 10
            print(f"  {i:2d}. {pair}")
        if len(failed_pairs) > 10:
            print(f"  ... and {len(failed_pairs) - 10} more")
    
    print("\n" + "="*80)

def main():
    """Main execution function"""
    try:
        args = parse_args()
        
        # Set logging level based on verbose flag
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info("Starting analysis process")
        logger.info(f"Arguments: {vars(args)}")
        
        # Initialize analyzer with the quote currency and workers
        logger.info("Initializing analyzer...")
        analyzer = VersionedAnalyzer(
            quote_currency=args.quote,
            max_workers=args.workers
        )
        
        # Update analyzer parameters based on command line args
        analyzer.timeframe = args.timeframe
        analyzer.days_to_analyze = args.days
        
        logger.info(f"Starting analysis for {args.quote} pairs with timeframe {args.timeframe}...")
        
        # Run the analysis (this is the working implementation)
        results, failed_pairs = analyzer.run_analysis()
        
        # Save results
        if results or failed_pairs:
            logger.info("Saving results...")
            report = analyzer.save_results(results, failed_pairs)
            
            # Display summary
            print_results_summary(results, failed_pairs, args)
            
            logger.info("Analysis completed successfully!")
            return 0
        else:
            logger.error("No pairs were processed successfully")
            return 1
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error during analysis: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())