# FILENAME: pair_analyzer.py
# ACTION: REPLACE EXISTING FILE (backup will be created automatically)
# DESCRIPTION: Enhanced main analyzer with pairlist support

#!/usr/bin/env python3
"""
Freqtrade Pair Analyzer Pro - Enhanced with Pairlist Support
Version: 2.1.0 - Added config-based pairlist analysis
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the WORKING analyzer from data_handler
from utils.data_handler import VersionedAnalyzer
from utils.pairlist_handler import PairlistHandler

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
    """Parse command line arguments with pairlist support"""
    parser = argparse.ArgumentParser(
        description='Freqtrade Pair Analyzer Pro - Advanced cryptocurrency pair analysis tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all pairs from exchange
  python pair_analyzer.py --quote USDT --timeframe 1h
  
  # Analyze pairs from a specific config
  python pair_analyzer.py --quote USDT --config strategy1 --timeframe 15m
  
  # Analyze combined pairs from all configs
  python pair_analyzer.py --quote USDT --use-configs --timeframe 4h
  
  # List available pairlists
  python pair_analyzer.py --list-configs --quote USDT
  
  # Analyze overlap between configs
  python pair_analyzer.py --analyze-overlap --quote USDT
        """
    )
    
    # Existing arguments
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
    
    # NEW: Pairlist-related arguments
    parser.add_argument(
        '--config',
        type=str,
        help='Use pairs from specific config file (e.g. "strategy1", "config-btc")'
    )
    
    parser.add_argument(
        '--use-configs',
        action='store_true',
        help='Use combined pairs from all available config files'
    )
    
    parser.add_argument(
        '--exclude-configs',
        type=str,
        nargs='+',
        help='Config names to exclude when using --use-configs'
    )
    
    parser.add_argument(
        '--list-configs',
        action='store_true',
        help='List all available config files with pair counts'
    )
    
    parser.add_argument(
        '--analyze-overlap',
        action='store_true',
        help='Analyze pair overlap between different configs'
    )
    
    parser.add_argument(
        '--export-pairlist',
        type=str,
        help='Export analyzed pairs to file (specify output path)'
    )
    
    parser.add_argument(
        '--user-data-dir',
        type=str,
        default='/home/facepipe/freqtrade/user_data',
        help='Path to freqtrade user_data directory (default: /home/facepipe/freqtrade/user_data)'
    )
    
    return parser.parse_args()

def list_available_configs(pairlist_handler: PairlistHandler, quote_currency: str):
    """List all available configurations with pair counts"""
    print("\n" + "="*60)
    print("AVAILABLE PAIRLIST CONFIGURATIONS")
    print("="*60)
    
    configs = pairlist_handler.list_available_configs(quote_currency)
    
    if not configs:
        print(f"❌ No configs found with {quote_currency} pairs")
        return
    
    print(f"\nFound {len(configs)} configs with {quote_currency} pairs:\n")
    
    total_unique_pairs = len(pairlist_handler.get_combined_pairlist(quote_currency))
    
    for config_name, pair_count in sorted(configs.items()):
        print(f"  📋 {config_name:<25} : {pair_count:>3} pairs")
    
    print(f"\n📊 Total unique pairs across all configs: {total_unique_pairs}")
    print("\n💡 Usage examples:")
    print(f"    python pair_analyzer.py --quote {quote_currency} --config {list(configs.keys())[0]}")
    print(f"    python pair_analyzer.py --quote {quote_currency} --use-configs")

def analyze_pairlist_overlap(pairlist_handler: PairlistHandler, quote_currency: str):
    """Analyze and display pairlist overlap between configs"""
    print("\n" + "="*60)
    print("PAIRLIST OVERLAP ANALYSIS")
    print("="*60)
    
    analysis = pairlist_handler.analyze_pairlist_overlap(quote_currency)
    
    if "message" in analysis:
        print(f"ℹ️  {analysis['message']}")
        return
    
    print(f"\n📊 Analysis Summary:")
    print(f"  Total configs: {analysis['total_configs']}")
    print(f"  Common pairs (in all configs): {analysis['common_count']}")
    
    print(f"\n📋 Config sizes:")
    for config_name, size in analysis['config_sizes'].items():
        print(f"  {config_name:<25} : {size:>3} pairs")
    
    if analysis['common_pairs']:
        print(f"\n🤝 Common pairs across all configs ({len(analysis['common_pairs'])}):")
        for i, pair in enumerate(analysis['common_pairs'][:10], 1):
            print(f"  {i:2d}. {pair}")
        if len(analysis['common_pairs']) > 10:
            print(f"  ... and {len(analysis['common_pairs']) - 10} more")
    
    print(f"\n🔹 Unique pairs per config:")
    for config_name, unique_pairs in analysis['unique_pairs'].items():
        if unique_pairs:
            print(f"  {config_name}: {len(unique_pairs)} unique pairs")
            for pair in unique_pairs[:3]:
                print(f"    • {pair}")
            if len(unique_pairs) > 3:
                print(f"    ... and {len(unique_pairs) - 3} more")
        else:
            print(f"  {config_name}: No unique pairs")

def print_results_summary(results: List[Dict], failed_pairs: List[str], args, pair_source: str):
    """Print a comprehensive results summary with pair source info"""
    print("\n" + "="*80)
    print("FREQTRADE PAIR ANALYZER - RESULTS SUMMARY")
    print("="*80)
    
    print(f"\nConfiguration:")
    print(f"  Quote Currency: {args.quote}")
    print(f"  Timeframe: {args.timeframe}")
    print(f"  Days Analyzed: {args.days}")
    print(f"  Workers Used: {args.workers}")
    print(f"  Pair Source: {pair_source}")
    
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
        for i, pair in enumerate(failed_pairs[:10], 1):
            print(f"  {i:2d}. {pair}")
        if len(failed_pairs) > 10:
            print(f"  ... and {len(failed_pairs) - 10} more")
    
    print("\n" + "="*80)

def main():
    """Main execution function with pairlist support"""
    try:
        args = parse_args()
        
        # Set logging level based on verbose flag
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info("Starting Freqtrade Pair Analyzer Pro v2.1.0")
        logger.info(f"Arguments: {vars(args)}")
        
        # Initialize pairlist handler
        user_data_dir = Path(args.user_data_dir)
        pairlist_handler = PairlistHandler(user_data_dir)
        
        # Handle informational commands
        if args.list_configs:
            list_available_configs(pairlist_handler, args.quote)
            return 0
        
        if args.analyze_overlap:
            analyze_pairlist_overlap(pairlist_handler, args.quote)
            return 0
        
        # Determine which pairs to analyze
        pairs_to_analyze = None
        pair_source = "Exchange (all active pairs)"
        
        if args.config:
            # Use specific config
            pairs_to_analyze = pairlist_handler.get_pairlist_by_config(args.config, args.quote)
            pair_source = f"Config: {args.config}"
            if not pairs_to_analyze:
                logger.error(f"No pairs found in config '{args.config}' for {args.quote}")
                return 1
        
        elif args.use_configs:
            # Use combined configs
            exclude_configs = args.exclude_configs or []
            pairs_to_analyze = pairlist_handler.get_combined_pairlist(args.quote, exclude_configs)
            pair_source = f"All configs (excluding: {exclude_configs})" if exclude_configs else "All configs"
            if not pairs_to_analyze:
                logger.error(f"No pairs found in any configs for {args.quote}")
                return 1
        
        # Log pair source information
        if pairs_to_analyze:
            logger.info(f"Using pairs from: {pair_source}")
            logger.info(f"Pairs to analyze: {len(pairs_to_analyze)}")
            if args.verbose:
                logger.debug(f"Pair list: {pairs_to_analyze[:10]}{'...' if len(pairs_to_analyze) > 10 else ''}")
        
        # Initialize analyzer
        logger.info("Initializing analyzer...")
        analyzer = VersionedAnalyzer(
            quote_currency=args.quote,
            max_workers=args.workers
        )
        
        # Update analyzer parameters
        analyzer.timeframe = args.timeframe
        analyzer.days_to_analyze = args.days
        
        # Override the pair selection if we have specific pairs
        if pairs_to_analyze:
            # Monkey patch the _get_valid_pairs method to return our pairs
            original_get_valid_pairs = analyzer._get_valid_pairs
            analyzer._get_valid_pairs = lambda: pairs_to_analyze
            logger.info(f"Overriding pair selection with {len(pairs_to_analyze)} pairs from {pair_source}")
        
        logger.info(f"Starting analysis for {args.quote} pairs with timeframe {args.timeframe}...")
        
        # Run the analysis
        results, failed_pairs = analyzer.run_analysis()
        
        # Save results
        if results or failed_pairs:
            logger.info("Saving results...")
            report = analyzer.save_results(results, failed_pairs)
            
            # Add pairlist metadata to report
            if 'metadata' in report:
                report['metadata']['pair_source'] = pair_source
                report['metadata']['pairlist_config'] = args.config if args.config else None
                report['metadata']['used_configs'] = args.use_configs
            
            # Export pairlist if requested
            if args.export_pairlist and results:
                export_pairs = [r['pair'] for r in results]
                export_path = Path(args.export_pairlist)
                if pairlist_handler.export_pairlist(export_pairs, export_path, "json"):
                    logger.info(f"Exported {len(export_pairs)} pairs to {export_path}")
            
            # Display summary
            print_results_summary(results, failed_pairs, args, pair_source)
            
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