# FILENAME: pairlist_generator.py
# ACTION: CREATE NEW FILE
# DESCRIPTION: Advanced pairlist generator with filtering and analysis results

#!/usr/bin/env python3
"""
Advanced Pairlist Generator - Create filtered pairlists from analysis results
Version: 1.0.0

Generates pairlists compatible with your format and includes advanced filtering
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime, timezone
import logging

# Add path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.data_handler import VersionedAnalyzer
from utils.pairlist_handler import PairlistHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PairlistGenerator:
    """Advanced pairlist generator with multiple filtering strategies"""
    
    def __init__(self, quote_currency: str = "USDT", user_data_dir: str = None):
        self.quote_currency = quote_currency.upper()
        self.user_data_dir = Path(user_data_dir) if user_data_dir else Path("/home/facepipe/freqtrade/user_data")
        
        # Create timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("generated_pairlists") / f"batch_{timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize handlers
        self.pairlist_handler = PairlistHandler(self.user_data_dir)
        
        # Abbreviation mapping for filenames
        self.abbreviations = {
            'high_volume': 'HV',
            'price_filtered': 'PF', 
            'analysis_based': 'AB',
            'analyzed_top': 'AT',
            'diversified': 'DIV',
            'stable': 'STB',
            'low_volatility': 'LV',
            'sector_balanced': 'SB',
            'top_performers': 'TP',
            'conservative': 'CON',
            'aggressive': 'AGG'
        }
        
    def print_abbreviation_chart(self):
        """Print chart of abbreviations used in filenames"""
        print("\n📋 FILENAME ABBREVIATION CHART")
        print("=" * 50)
        print("Code | Full Name           | Description")
        print("-" * 50)
        print("HV   | High Volume        | Top pairs by 24h volume")
        print("PF   | Price Filtered     | Freqtrade PriceFilter logic")
        print("AB   | Analysis Based     | Based on analyzer results")
        print("AT   | Analyzed Top       | Top scoring analyzed pairs")
        print("DIV  | Diversified        | Sector-balanced portfolio")
        print("STB  | Stable             | Low volatility pairs")
        print("LV   | Low Volatility     | Same as Stable")
        print("SB   | Sector Balanced    | Balanced across sectors")
        print("TP   | Top Performers     | Highest composite scores")
        print("CON  | Conservative       | Low risk, stable pairs")
        print("AGG  | Aggressive         | High volatility, high reward")
        print("-" * 50)
        print("Examples:")
        print("  pairsHV_PF_USDT_20250804_143022.json")
        print("  pairsAT_STB_BTC_20250804_143022.json") 
        print()
        
    def get_abbreviated_filename(self, filter_types: List[str], quote: str) -> str:
        """Generate abbreviated filename based on active filters"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get abbreviations for active filters
        abbrevs = []
        for filter_type in filter_types:
            abbrev = self.abbreviations.get(filter_type, filter_type.upper()[:3])
            if abbrev not in abbrevs:
                abbrevs.append(abbrev)
        
        # Create filename
        filter_part = "_".join(abbrevs)
        filename = f"pairs{filter_part}_{quote}_{timestamp}.json"
        
        return filename
        
    def create_base_config_template(self, pairs: List[str], blacklist: List[str] = None,
                                  config_name: str = "generated", description: str = "") -> Dict:
        """Create base config template in your format"""
        
        blacklist = blacklist or []
        
        return {
            "description": description or f"Generated pairlist for {config_name}",
            "config_name": config_name,
            "created": datetime.now(timezone.utc).isoformat(),
            "exchange": {
                "pair_whitelist": sorted(pairs),
                "pair_blacklist": sorted(blacklist)
            },
            "whitelist_count": len(pairs),
            "blacklist_count": len(blacklist)
        }
    
    def get_exchange_pairs_with_volume(self, min_volume_24h: float = 100) -> List[Dict[str, any]]:
        """Get pairs from exchange with volume data"""
        analyzer = None
        try:
            # Initialize analyzer to get exchange connection
            analyzer = VersionedAnalyzer(quote_currency=self.quote_currency, max_workers=1)
            markets = analyzer.exchange.get_markets()
            
            # Get tickers for volume data
            logger.info("Fetching market data with volume information...")
            tickers = analyzer.exchange.get_tickers()
            
            pairs_with_data = []
            quote_suffix = f"/{self.quote_currency}"
            
            # Adjust minimum volume based on quote currency
            # BTC pairs typically have much lower volume than USDT pairs
            if self.quote_currency == 'BTC':
                adjusted_min_volume = min_volume_24h * 0.001  # Much lower for BTC pairs
            else:
                adjusted_min_volume = min_volume_24h
            
            logger.info(f"Using adjusted minimum volume: {adjusted_min_volume} {self.quote_currency}")
            
            for pair, market_info in markets.items():
                if (pair.endswith(quote_suffix) and 
                    market_info.get('active', False) and
                    market_info.get('spot', True) and
                    not market_info.get('margin', False) and
                    not market_info.get('future', False)):
                    
                    ticker = tickers.get(pair, {})
                    volume_24h = ticker.get('quoteVolume', 0) or 0
                    price = ticker.get('last', 0) or 0
                    
                    if volume_24h >= adjusted_min_volume:
                        pairs_with_data.append({
                            'pair': pair,
                            'volume_24h': volume_24h,
                            'price': price,
                            'market_info': market_info
                        })
            
            logger.info(f"Found {len(pairs_with_data)} pairs with sufficient volume (min: {adjusted_min_volume})")
            return pairs_with_data
            
        except Exception as e:
            logger.error(f"Error fetching exchange data: {e}")
            return []
        finally:
            # Clean up the analyzer and exchange connection
            if analyzer and hasattr(analyzer, 'exchange'):
                try:
                    if hasattr(analyzer.exchange, 'close'):
                        analyzer.exchange.close()
                    # Also clean up any background threads
                    import gc
                    gc.collect()
                except Exception as e:
                    logger.debug(f"Error during cleanup: {e}")
            del analyzer
    
    def generate_high_volume_pairlist(self, min_volume: float = 1000, max_pairs: int = 200) -> Dict:
        """Generate high volume pairlist"""
        # Adjust volume threshold for different quote currencies
        if self.quote_currency == 'BTC':
            adjusted_min_volume = min_volume * 0.001  # Much lower threshold for BTC pairs
        else:
            adjusted_min_volume = min_volume
            
        logger.info(f"Generating high volume pairlist (min: {adjusted_min_volume} {self.quote_currency})")
        
        pairs_data = self.get_exchange_pairs_with_volume(adjusted_min_volume)
        
        # Sort by volume (highest first)
        pairs_data.sort(key=lambda x: x['volume_24h'], reverse=True)
        
        # Take top N pairs
        top_pairs = pairs_data[:max_pairs]
        pairs = [p['pair'] for p in top_pairs]
        
        config = self.create_base_config_template(
            pairs=pairs,
            config_name=f"high_volume_{self.quote_currency.lower()}",
            description=f"High volume pairs (min {adjusted_min_volume} {self.quote_currency} 24h volume, top {len(pairs)} pairs)"
        )
        
        # Add volume metadata
        config['filter_criteria'] = {
            'min_volume_24h': adjusted_min_volume,
            'original_min_volume': min_volume,
            'max_pairs': max_pairs,
            'sort_by': 'volume_desc'
        }
        
        config['pair_metadata'] = {
            p['pair']: {
                'volume_24h': p['volume_24h'],
                'price': p['price']
            } for p in top_pairs
        }
        
        return config
    
    def generate_all_pairlists(self):
        """Generate all types of pairlists including comprehensive ALL pairs list"""
        logger.info(f"🚀 Generating all pairlist types for {self.quote_currency}")
        
        generators = [
            ("ALL Exchange Pairs", lambda: self.generate_all_pairs_pairlist(min_volume=0.001)),
            ("High Volume", lambda: self.generate_high_volume_pairlist(min_volume=1000, max_pairs=200)),
            ("Price Filtered", lambda: self.generate_price_filtered_pairlist(min_price=0.00000100, low_price_ratio=0.01)),
            ("Analysis Based", lambda: self.generate_analysis_based_pairlist(top_n=50, min_score=0.3)),
            ("Diversified", lambda: self.generate_diversified_pairlist()),
            ("Stable", lambda: self.generate_stable_pairlist(max_volatility=0.5, min_volume=500))
        ]
        
        generated_files = []
        
        for name, generator in generators:
            try:
                logger.info(f"\n📋 Generating {name} pairlist...")
                config = generator()
                
                if config and config.get('whitelist_count', 0) > 0:
                    # Create descriptive filename
                    if name == "ALL Exchange Pairs":
                        filename = f"pairsALL_{self.quote_currency.upper()}.json"
                    else:
                        filename = f"pairs{config['config_name'].upper()}.json"
                    
                    output_path = self.save_pairlist(config, filename)
                    if output_path:
                        generated_files.append(output_path)
                else:
                    logger.warning(f"❌ Failed to generate {name} pairlist")
                    
            except Exception as e:
                logger.error(f"❌ Error generating {name} pairlist: {e}")
        
        return generated_files
    
    def generate_price_filtered_pairlist(self, min_price: float = 0.00000100, 
                                       low_price_ratio: float = 0.01, max_pairs: int = 300) -> Dict:
        """Generate price-filtered pairlist using Freqtrade PriceFilter logic"""
        logger.info(f"Generating price-filtered pairlist (min_price: {min_price}, low_price_ratio: {low_price_ratio})")
        
        pairs_data = self.get_exchange_pairs_with_volume(10)  # Basic volume filter
        
        filtered_pairs = []
        
        for pair_data in pairs_data:
            price = pair_data['price']
            
            # PriceFilter logic from Freqtrade
            if price <= 0:
                continue
                
            # Min price filter
            if price < min_price:
                continue
                
            # Low price ratio filter - removes pairs where price is too close to minimum precision
            market_info = pair_data['market_info']
            price_precision = market_info.get('precision', {}).get('price', 8)
            
            if price_precision:
                min_precision = 10 ** (-price_precision)
                if price < min_precision * (1 + low_price_ratio):
                    continue
            
            filtered_pairs.append(pair_data)
        
        # Sort by volume for quality
        filtered_pairs.sort(key=lambda x: x['volume_24h'], reverse=True)
        
        # Take top pairs
        selected_pairs = filtered_pairs[:max_pairs]
        pairs = [p['pair'] for p in selected_pairs]
        
        config = self.create_base_config_template(
            pairs=pairs,
            config_name=f"price_filtered_{self.quote_currency.lower()}",
            description=f"Price-filtered pairs (min_price: {min_price}, low_price_ratio: {low_price_ratio})"
        )
        
        # Add filter metadata
        config['filter_criteria'] = {
            'min_price': min_price,
            'low_price_ratio': low_price_ratio,
            'max_pairs': max_pairs
        }
        
        config['pair_metadata'] = {
            p['pair']: {
                'price': p['price'],
                'volume_24h': p['volume_24h']
            } for p in selected_pairs
        }
        
        return config
    
    def generate_analysis_based_pairlist(self, analysis_file: Path = None, 
                                       top_n: int = 50, min_score: float = 0.3) -> Dict:
        """Generate pairlist based on analyzer results"""
        logger.info("Generating analysis-based pairlist")
        
        # Find latest analysis file if not specified
        if not analysis_file:
            analysis_files = list(Path("outputs").glob("pair_analysis_*.json"))
            if not analysis_files:
                analysis_files = list(Path("user_data/analysis_results").glob("pair_analysis_*.json"))
            
            if not analysis_files:
                logger.error("No analysis files found. Run analyzer first.")
                return {}
            
            analysis_file = max(analysis_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"Using analysis file: {analysis_file}")
        
        try:
            with open(analysis_file) as f:
                analysis_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading analysis file: {e}")
            return {}
        
        results = analysis_data.get('results', [])
        
        # Filter by minimum score and take top N
        good_pairs = [r for r in results if r.get('composite_score', 0) >= min_score]
        good_pairs.sort(key=lambda x: x.get('composite_score', 0), reverse=True)
        
        top_pairs = good_pairs[:top_n]
        pairs = [p['pair'] for p in top_pairs]
        
        config = self.create_base_config_template(
            pairs=pairs,
            config_name=f"analyzed_top_{self.quote_currency.lower()}",
            description=f"Top analyzed pairs (min score: {min_score}, top {len(pairs)} pairs)"
        )
        
        # Add analysis metadata
        config['filter_criteria'] = {
            'min_composite_score': min_score,
            'top_n': top_n,
            'analysis_file': str(analysis_file),
            'analysis_date': analysis_data.get('metadata', {}).get('analysis_date')
        }
        
        config['pair_metadata'] = {
            p['pair']: {
                'composite_score': p.get('composite_score', 0),
                'volatility': p.get('volatility', 0),
                'trend_strength': p.get('trend_strength', 0),
                'volume_score': p.get('volume_score', 0)
            } for p in top_pairs
        }
        
        return config
    
    def generate_diversified_pairlist(self, sectors: Dict[str, List[str]] = None) -> Dict:
        """Generate diversified pairlist across different crypto sectors"""
        logger.info("Generating diversified sector-based pairlist")
        
        # Default sector classification
        if not sectors:
            sectors = {
                "layer1": ["BTC", "ETH", "ADA", "SOL", "AVAX", "DOT", "ATOM", "NEAR", "ALGO"],
                "layer2": ["MATIC", "ARB", "OP", "LRC", "IMX"],
                "defi": ["UNI", "AAVE", "COMP", "SUSHI", "CRV", "YFI", "MKR", "SNX"],
                "gaming": ["AXS", "SAND", "MANA", "GALA", "ENJ", "ALICE", "ILV"],
                "oracle": ["LINK", "BAND", "API3", "TRB"],
                "storage": ["FIL", "STORJ", "AR"],
                "privacy": ["XMR", "ZEC", "SCRT"],
                "exchange": ["BNB", "FTT", "LEO", "CRO"],
                "infrastructure": ["GRT", "LPT", "RLN", "NKN"]
            }
        
        # Use very low volume filter for diversification
        min_vol = 10 if self.quote_currency == 'BTC' else 50
        pairs_data = self.get_exchange_pairs_with_volume(min_vol)
        
        if not pairs_data:
            logger.error("No pairs found with volume data for diversification")
            return {}
        
        diversified_pairs = []
        used_pairs = set()
        
        # Select pairs from each sector
        for sector, tokens in sectors.items():
            sector_pairs = []
            for token in tokens:
                pair = f"{token}/{self.quote_currency}"
                pair_data = next((p for p in pairs_data if p['pair'] == pair), None)
                if pair_data and pair not in used_pairs:
                    sector_pairs.append(pair_data)
                    used_pairs.add(pair)
            
            # Sort by volume and take top pairs from each sector
            sector_pairs.sort(key=lambda x: x['volume_24h'], reverse=True)
            diversified_pairs.extend(sector_pairs[:5])  # Top 5 from each sector
        
        if not diversified_pairs:
            logger.warning("No diversified pairs found, using top volume pairs instead")
            # Fallback to just top volume pairs
            diversified_pairs = pairs_data[:50]
        
        pairs = [p['pair'] for p in diversified_pairs]
        
        config = self.create_base_config_template(
            pairs=pairs,
            config_name=f"diversified_{self.quote_currency.lower()}",
            description=f"Diversified portfolio across {len(sectors)} crypto sectors ({len(pairs)} pairs)"
        )
        
        # Add sector metadata
        config['filter_criteria'] = {
            'sectors': list(sectors.keys()),
            'pairs_per_sector': 5,
            'min_volume_filter': min_vol,
            'quote_currency': self.quote_currency
        }
        
        config['sector_breakdown'] = {}
        for sector, tokens in sectors.items():
            sector_pairs_in_list = [p for p in pairs if any(p.startswith(token + "/") for token in tokens)]
            if sector_pairs_in_list:
                config['sector_breakdown'][sector] = sector_pairs_in_list
        
        return config
    
    def apply_multiple_filters(self, filters: Dict, days: int = 90, timeframe: str = '1d') -> Dict:
        """Apply multiple filters in combination"""
        logger.info("🔄 Applying multiple filters in combination")
        
        # Start with all pairs that meet basic criteria
        pairs_data = self.get_exchange_pairs_with_volume(filters.get('min_volume', 10))
        
        filtered_pairs = pairs_data.copy()
        applied_filters = []
        filter_descriptions = []
        
        # Apply volume filter
        if filters.get('high_volume') and filters.get('min_volume'):
            min_vol = filters['min_volume']
            filtered_pairs = [p for p in filtered_pairs if p['volume_24h'] >= min_vol]
            applied_filters.append('high_volume')
            filter_descriptions.append(f"min volume {min_vol} {self.quote_currency}")
            logger.info(f"  📊 Volume filter: {len(filtered_pairs)} pairs remaining")
        
        # Apply price filter
        if filters.get('price_filter'):
            min_price = filters.get('min_price', 0.00000100)
            low_price_ratio = filters.get('low_price_ratio', 0.01)
            
            price_filtered = []
            for pair_data in filtered_pairs:
                price = pair_data['price']
                
                if price <= 0 or price < min_price:
                    continue
                    
                # Low price ratio filter
                market_info = pair_data['market_info']
                price_precision = market_info.get('precision', {}).get('price', 8)
                
                if price_precision:
                    min_precision = 10 ** (-price_precision)
                    if price < min_precision * (1 + low_price_ratio):
                        continue
                
                price_filtered.append(pair_data)
            
            filtered_pairs = price_filtered
            applied_filters.append('price_filtered')
            filter_descriptions.append(f"price filter (min: {min_price}, ratio: {low_price_ratio})")
            logger.info(f"  💰 Price filter: {len(filtered_pairs)} pairs remaining")
        
        # Apply analysis-based filter
        if filters.get('analysis_based'):
            analysis_pairs = self._get_analysis_filtered_pairs(
                [p['pair'] for p in filtered_pairs], 
                filters.get('min_score', 0.3),
                days,
                timeframe
            )
            
            if analysis_pairs:
                # Filter to only pairs that passed analysis
                filtered_pairs = [p for p in filtered_pairs if p['pair'] in analysis_pairs]
                applied_filters.append('analysis_based')
                filter_descriptions.append(f"analysis score >= {filters.get('min_score', 0.3)}")
                logger.info(f"  📈 Analysis filter: {len(filtered_pairs)} pairs remaining")
        
        # Apply stability filter
        if filters.get('stable'):
            max_vol = filters.get('max_volatility', 0.5)
            stable_pairs = self._get_volatility_filtered_pairs(
                [p['pair'] for p in filtered_pairs], 
                max_vol,
                days,
                timeframe
            )
            
            if stable_pairs:
                filtered_pairs = [p for p in filtered_pairs if p['pair'] in stable_pairs]
                applied_filters.append('stable')
                filter_descriptions.append(f"volatility <= {max_vol}")
                logger.info(f"  📉 Stability filter: {len(filtered_pairs)} pairs remaining")
        
        # Apply diversification
        if filters.get('diversified'):
            diversified_pairs = self._apply_sector_diversification(filtered_pairs)
            if diversified_pairs:
                filtered_pairs = diversified_pairs
                applied_filters.append('diversified')
                filter_descriptions.append("sector diversification")
                logger.info(f"  🎯 Diversification: {len(filtered_pairs)} pairs remaining")
        
        # Sort by volume (quality indicator)
        filtered_pairs.sort(key=lambda x: x['volume_24h'], reverse=True)
        
        # Apply max pairs limit
        max_pairs = filters.get('max_pairs', 200)
        if len(filtered_pairs) > max_pairs:
            filtered_pairs = filtered_pairs[:max_pairs]
            logger.info(f"  🔢 Limited to top {max_pairs} pairs")
        
        # Generate config
        pairs = [p['pair'] for p in filtered_pairs]
        
        # Create descriptive name
        filter_code = "_".join([self.abbreviations.get(f, f.upper()[:3]) for f in applied_filters])
        config_name = f"{filter_code.lower()}_{self.quote_currency.lower()}"
        
        description = f"Multi-filtered pairs: {', '.join(filter_descriptions)}"
        if days != 90 or timeframe != '1d':
            description += f" (analyzed: {days}d, {timeframe})"
        
        config = self.create_base_config_template(
            pairs=pairs,
            config_name=config_name,
            description=description
        )
        
        # Add comprehensive metadata
        config['filter_criteria'] = {
            'applied_filters': applied_filters,
            'parameters': filters,
            'analysis_period': f"{days} days",
            'timeframe': timeframe,
            'total_filters_applied': len(applied_filters)
        }
        
        config['pair_metadata'] = {
            p['pair']: {
                'volume_24h': p['volume_24h'],
                'price': p['price']
            } for p in filtered_pairs
        }
        
        return config, applied_filters
    
    def _get_analysis_filtered_pairs(self, candidate_pairs: List[str], min_score: float, 
                                   days: int, timeframe: str) -> List[str]:
        """Get pairs that meet analysis criteria"""
        try:
            # Look for analysis files that match timeframe and period
            analysis_files = []
            for results_dir in [Path("outputs"), Path("user_data/analysis_results")]:
                if results_dir.exists():
                    analysis_files.extend(results_dir.glob("pair_analysis_*.json"))
            
            if not analysis_files:
                logger.warning("No analysis files found for analysis-based filtering")
                return candidate_pairs  # Return all if no analysis available
            
            # Use most recent analysis file
            analysis_file = max(analysis_files, key=lambda x: x.stat().st_mtime)
            
            with open(analysis_file) as f:
                analysis_data = json.load(f)
            
            results = analysis_data.get('results', [])
            
            # Filter by score and limit to candidate pairs
            good_pairs = [
                r['pair'] for r in results 
                if r.get('composite_score', 0) >= min_score and r['pair'] in candidate_pairs
            ]
            
            return good_pairs
            
        except Exception as e:
            logger.warning(f"Analysis filtering failed: {e}")
            return candidate_pairs
    
    def _get_volatility_filtered_pairs(self, candidate_pairs: List[str], max_volatility: float,
                                     days: int, timeframe: str) -> List[str]:
        """Get pairs that meet volatility criteria"""
        try:
            # Similar to analysis filtering but for volatility
            analysis_files = []
            for results_dir in [Path("outputs"), Path("user_data/analysis_results")]:
                if results_dir.exists():
                    analysis_files.extend(results_dir.glob("pair_analysis_*.json"))
            
            if not analysis_files:
                return candidate_pairs
            
            analysis_file = max(analysis_files, key=lambda x: x.stat().st_mtime)
            
            with open(analysis_file) as f:
                analysis_data = json.load(f)
            
            results = analysis_data.get('results', [])
            
            stable_pairs = [
                r['pair'] for r in results 
                if r.get('volatility', 1.0) <= max_volatility and r['pair'] in candidate_pairs
            ]
            
            return stable_pairs
            
        except Exception as e:
            logger.warning(f"Volatility filtering failed: {e}")
            return candidate_pairs
    
    def _apply_sector_diversification(self, pairs_data: List[Dict]) -> List[Dict]:
        """Apply sector diversification to pairs"""
        sectors = {
            "layer1": ["BTC", "ETH", "ADA", "SOL", "AVAX", "DOT", "ATOM", "NEAR", "ALGO"],
            "layer2": ["MATIC", "ARB", "OP", "LRC", "IMX"],
            "defi": ["UNI", "AAVE", "COMP", "SUSHI", "CRV", "YFI", "MKR", "SNX"],
            "gaming": ["AXS", "SAND", "MANA", "GALA", "ENJ", "ALICE", "ILV"],
            "oracle": ["LINK", "BAND", "API3", "TRB"],
            "storage": ["FIL", "STORJ", "AR"],
            "exchange": ["BNB", "FTT", "CRO", "LEO"],
            "infrastructure": ["GRT", "LPT", "NKN"]
        }
        
        diversified_pairs = []
        used_pairs = set()
        
        # Select top pairs from each sector
        for sector, tokens in sectors.items():
            sector_pairs = []
            for pair_data in pairs_data:
                if pair_data['pair'] not in used_pairs:
                    for token in tokens:
                        if pair_data['pair'].startswith(f"{token}/"):
                            sector_pairs.append(pair_data)
                            used_pairs.add(pair_data['pair'])
                            break
            
            # Sort by volume and take top 3-5 from each sector
            sector_pairs.sort(key=lambda x: x['volume_24h'], reverse=True)
            diversified_pairs.extend(sector_pairs[:4])
        
        return diversified_pairs
    
    def generate_stable_pairlist(self, max_volatility: float = 0.5, min_volume: float = 500) -> Dict:
        """Generate pairlist with stable, lower volatility pairs"""
        logger.info("Generating stable (low volatility) pairlist")
        
        # Look for recent analysis
        analysis_files = list(Path("outputs").glob("pair_analysis_*.json"))
        if not analysis_files:
            analysis_files = list(Path("user_data/analysis_results").glob("pair_analysis_*.json"))
        
        if analysis_files:
            analysis_file = max(analysis_files, key=lambda x: x.stat().st_mtime)
            try:
                with open(analysis_file) as f:
                    analysis_data = json.load(f)
                
                results = analysis_data.get('results', [])
                
                # Filter by volatility
                stable_pairs = [r for r in results if r.get('volatility', 1.0) <= max_volatility]
                stable_pairs.sort(key=lambda x: x.get('volatility', 1.0))  # Lowest volatility first
                
                pairs = [p['pair'] for p in stable_pairs[:100]]  # Top 100 stable pairs
                
            except Exception as e:
                logger.warning(f"Could not load analysis data: {e}, using volume-based selection")
                pairs_data = self.get_exchange_pairs_with_volume(min_volume)
                pairs = [p['pair'] for p in pairs_data[:50]]  # Fallback to volume
        else:
            # Fallback to high-volume pairs (tend to be more stable)
            pairs_data = self.get_exchange_pairs_with_volume(min_volume)
            pairs = [p['pair'] for p in pairs_data[:50]]
        
        config = self.create_base_config_template(
            pairs=pairs,
            config_name=f"stable_{self.quote_currency.lower()}",
            description=f"Stable pairs with volatility <= {max_volatility}"
        )
        
        config['filter_criteria'] = {
            'max_volatility': max_volatility,
            'min_volume': min_volume
        }
        
        return config
    
    def save_pairlist(self, config: Dict, filename: str = None) -> Path:
        """Save pairlist to file"""
        if not filename:
            filename = f"pairs{config['config_name'].upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            logger.info(f"✅ Saved pairlist: {output_path}")
            logger.info(f"   Pairs: {config['whitelist_count']}")
            logger.info(f"   Description: {config['description']}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving pairlist: {e}")
            return None
    
    def generate_all_pairs_pairlist(self, min_volume: float = 0.001) -> Dict:
        """Generate comprehensive pairlist with ALL active exchange pairs - NO volume filtering"""
        logger.info(f"Generating ALL active {self.quote_currency} pairs from exchange (no volume filtering)")
        
        analyzer = None
        try:
            # Initialize analyzer to get exchange connection
            analyzer = VersionedAnalyzer(quote_currency=self.quote_currency, max_workers=1)
            markets = analyzer.exchange.get_markets()
            
            # Get ALL active pairs directly from markets - NO volume filtering
            quote_suffix = f"/{self.quote_currency}"
            all_active_pairs = []
            
            logger.info("Scanning all markets for active pairs (ignoring volume completely)...")
            
            for pair, market_info in markets.items():
                if (pair.endswith(quote_suffix) and 
                    market_info.get('active', False) and
                    market_info.get('spot', True) and
                    not market_info.get('margin', False) and
                    not market_info.get('future', False)):
                    
                    all_active_pairs.append(pair)
            
            logger.info(f"Found {len(all_active_pairs)} active {self.quote_currency} pairs (before volume check)")
            
            # Now get volume data ONLY for sorting - don't filter anything out
            pairs_with_data = []
            pairs_with_volume_count = 0
            
            try:
                logger.info("Getting volume data for sorting (not filtering)...")
                tickers = analyzer.exchange.get_tickers()
                
                for pair in all_active_pairs:
                    ticker = tickers.get(pair, {})
                    volume_24h = ticker.get('quoteVolume', 0) or 0
                    price = ticker.get('last', 0) or 0
                    
                    pairs_with_data.append({
                        'pair': pair,
                        'volume_24h': volume_24h,
                        'price': price
                    })
                    
                    if volume_24h > 0:
                        pairs_with_volume_count += 1
                
                # Sort by volume (highest first) but KEEP ALL PAIRS
                pairs_with_data.sort(key=lambda x: x['volume_24h'], reverse=True)
                final_pairs = [p['pair'] for p in pairs_with_data]
                
                logger.info(f"Final result: {len(final_pairs)} pairs total, {pairs_with_volume_count} have volume > 0")
                
            except Exception as e:
                logger.warning(f"Could not get volume data: {e}, using alphabetical sort")
                final_pairs = sorted(all_active_pairs)
                pairs_with_volume_count = 0
                pairs_with_data = []
            
            # Create config with ALL pairs
            config = self.create_base_config_template(
                pairs=final_pairs,
                config_name=f"all_pairs_{self.quote_currency.lower()}",
                description=f"ALL active {self.quote_currency} pairs from exchange ({len(final_pairs)} total pairs, {pairs_with_volume_count} with volume data)"
            )
            
            # Add comprehensive metadata
            config['filter_criteria'] = {
                'includes_all_active_pairs': True,
                'volume_filtering': 'NONE - includes zero volume pairs',
                'total_active_pairs': len(final_pairs),
                'pairs_with_volume_data': pairs_with_volume_count,
                'pairs_with_zero_volume': len(final_pairs) - pairs_with_volume_count,
                'sort_by': 'volume_desc_but_includes_all'
            }
            
            # Add volume statistics if available
            if pairs_with_data:
                volumes = [p['volume_24h'] for p in pairs_with_data if p['volume_24h'] > 0]
                if volumes:
                    config['volume_statistics'] = {
                        'pairs_with_volume': len(volumes),
                        'pairs_without_volume': len(final_pairs) - len(volumes),
                        'highest_volume': max(volumes),
                        'lowest_volume': min(volumes),
                        'average_volume': sum(volumes) / len(volumes),
                        'total_volume': sum(volumes)
                    }
                
                # Include metadata for all pairs (even zero volume)
                config['pair_metadata'] = {
                    p['pair']: {
                        'volume_24h': p['volume_24h'],
                        'price': p['price'],
                        'has_volume': p['volume_24h'] > 0
                    } for p in pairs_with_data
                }
            
            return config
            
        except Exception as e:
            logger.error(f"Error generating all pairs list: {e}")
            return {}
        finally:
            # Clean up the analyzer and exchange connection
            if analyzer and hasattr(analyzer, 'exchange'):
                try:
                    if hasattr(analyzer.exchange, 'close'):
                        analyzer.exchange.close()
                    import gc
                    gc.collect()
                except Exception as e:
                    logger.debug(f"Error during cleanup: {e}")
            del analyzer
        """Generate all types of pairlists"""
        logger.info(f"🚀 Generating all pairlist types for {self.quote_currency}")
        
        generators = [
            ("High Volume", lambda: self.generate_high_volume_pairlist(min_volume=1000, max_pairs=200)),
            ("Price Filtered", lambda: self.generate_price_filtered_pairlist(min_price=0.00000100, low_price_ratio=0.01)),
            ("Analysis Based", lambda: self.generate_analysis_based_pairlist(top_n=50, min_score=0.3)),
            ("Diversified", lambda: self.generate_diversified_pairlist()),
            ("Stable", lambda: self.generate_stable_pairlist(max_volatility=0.5, min_volume=500))
        ]
        
        generated_files = []
        
        for name, generator in generators:
            try:
                logger.info(f"\n📋 Generating {name} pairlist...")
                config = generator()
                
                if config and config.get('whitelist_count', 0) > 0:
                    filename = f"pairs{config['config_name'].upper()}.json"
                    output_path = self.save_pairlist(config, filename)
                    if output_path:
                        generated_files.append(output_path)
                else:
                    logger.warning(f"❌ Failed to generate {name} pairlist")
                    
            except Exception as e:
                logger.error(f"❌ Error generating {name} pairlist: {e}")
        
        return generated_files

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Advanced Pairlist Generator with Multi-Filter Support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all pairlist types
  python pairlist_generator.py --quote USDT --all
  
  # Multi-filter combination
  python pairlist_generator.py --quote USDT --high-volume --min-volume 1000 --price-filter --min-price 0.001 --days 21 --timeframe 1d
  
  # Analysis + stability filter
  python pairlist_generator.py --quote BTC --analysis-based --stable --min-score 0.4 --max-volatility 0.3 --days 30
  
  # High volume + diversified
  python pairlist_generator.py --quote USDT --high-volume --diversified --min-volume 2000 --max-pairs 100
        """
    )
    
    parser.add_argument('--quote', type=str, default='USDT', help='Quote currency (default: USDT)')
    parser.add_argument('--user-data-dir', type=str, default='/home/facepipe/freqtrade/user_data', 
                       help='Freqtrade user_data directory')
    
    # Analysis parameters
    parser.add_argument('--days', type=int, default=90, help='Days of data for analysis filters (default: 90)')
    parser.add_argument('--timeframe', type=str, default='1d', 
                       choices=['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
                       help='Timeframe for analysis filters (default: 1d)')
    
    # Generation types (can be combined)
    parser.add_argument('--all', action='store_true', help='Generate all pairlist types including comprehensive ALL pairs')
    parser.add_argument('--all-pairs', action='store_true', help='Generate comprehensive list of ALL exchange pairs')
    parser.add_argument('--high-volume', action='store_true', help='Apply high volume filter')
    parser.add_argument('--price-filter', action='store_true', help='Apply price filter')
    parser.add_argument('--analysis-based', action='store_true', help='Apply analysis-based filter')
    parser.add_argument('--diversified', action='store_true', help='Apply diversification filter')
    parser.add_argument('--stable', action='store_true', help='Apply stability filter')
    
    # Filter parameters
    parser.add_argument('--min-volume', type=float, default=1000, help='Minimum 24h volume (default: 1000)')
    parser.add_argument('--min-price', type=float, default=0.00000100, help='Minimum price filter (default: 0.00000100)')
    parser.add_argument('--low-price-ratio', type=float, default=0.01, help='Low price ratio filter (default: 0.01)')
    parser.add_argument('--min-score', type=float, default=0.3, help='Minimum composite score (default: 0.3)')
    parser.add_argument('--max-volatility', type=float, default=0.5, help='Maximum volatility for stable pairs (default: 0.5)')
    parser.add_argument('--max-pairs', type=int, default=200, help='Maximum number of pairs in result (default: 200)')
    
    # Output options
    parser.add_argument('--show-abbreviations', action='store_true', help='Show abbreviation chart and exit')
    
    return parser.parse_args()

def main():
    """Main function with multi-filter support"""
    args = parse_args()
    
    if args.show_abbreviations:
        generator = PairlistGenerator()
        generator.print_abbreviation_chart()
        return 0
    
    print("🚀 Advanced Multi-Filter Pairlist Generator")
    print("=" * 60)
    
    generator = PairlistGenerator(
        quote_currency=args.quote,
        user_data_dir=args.user_data_dir
    )
    
    # Show abbreviation chart
    generator.print_abbreviation_chart()
    
    print(f"📁 Output directory: {generator.output_dir}")
    print(f"💱 Quote currency: {args.quote}")
    print(f"📊 Analysis period: {args.days} days, {args.timeframe} timeframe")
    print()
    
    generated_files = []
    
    try:
        if args.all:
            # Generate all standard types including comprehensive ALL pairs
            generated_files = generator.generate_all_pairlists()
        elif args.all_pairs:
            # Generate just the comprehensive ALL pairs list
            print("🌍 Generating ALL exchange pairs...")
            config = generator.generate_all_pairs_pairlist(min_volume=0.001)
            if config and config.get('whitelist_count', 0) > 0:
                filename = f"pairsALL_{args.quote.upper()}.json"
                output_path = generator.save_pairlist(config, filename)
                if output_path:
                    generated_files.append(output_path)
            else:
                print("❌ No pairs found for comprehensive list")
                return 1
        else:
            # Check if any filters are specified
            filter_flags = [args.high_volume, args.price_filter, args.analysis_based, 
                          args.diversified, args.stable]
            
            if not any(filter_flags):
                print("❌ No filters specified. Use --all or specify filters like --high-volume")
                print("   Use --help to see all options")
                return 1
            
            # Build filter configuration
            filters = {
                'high_volume': args.high_volume,
                'price_filter': args.price_filter,
                'analysis_based': args.analysis_based,
                'diversified': args.diversified,
                'stable': args.stable,
                'min_volume': args.min_volume,
                'min_price': args.min_price,
                'low_price_ratio': args.low_price_ratio,
                'min_score': args.min_score,
                'max_volatility': args.max_volatility,
                'max_pairs': args.max_pairs
            }
            
            print("🔄 Active filters:")
            if args.high_volume:
                print(f"   📊 High Volume: >= {args.min_volume} {args.quote}")
            if args.price_filter:
                print(f"   💰 Price Filter: >= {args.min_price}, ratio {args.low_price_ratio}")
            if args.analysis_based:
                print(f"   📈 Analysis Based: score >= {args.min_score}")
            if args.stable:
                print(f"   📉 Stability: volatility <= {args.max_volatility}")
            if args.diversified:
                print(f"   🎯 Diversified: sector balance")
            print()
            
            # Apply multiple filters
            config, applied_filters = generator.apply_multiple_filters(filters, args.days, args.timeframe)
            
            if config and config.get('whitelist_count', 0) > 0:
                # Generate filename with abbreviations
                filename = generator.get_abbreviated_filename(applied_filters, args.quote)
                output_path = generator.save_pairlist(config, filename)
                if output_path:
                    generated_files.append(output_path)
            else:
                print("❌ No pairs matched the specified filters")
                return 1
        
        # Display summary
        print(f"\n✅ Generated {len(generated_files)} pairlist file(s):")
        for file_path in generated_files:
            if file_path:
                # Load and show summary
                try:
                    with open(file_path) as f:
                        data = json.load(f)
                    print(f"   📄 {file_path.name}")
                    print(f"      └─ {data['whitelist_count']} pairs: {data['description']}")
                except:
                    print(f"   📄 {file_path.name} (generated)")
        
        print(f"\n📁 All files saved to: {generator.output_dir}")
        print(f"💡 To use: copy desired files to {generator.user_data_dir}/")
        
        # Show copy command
        print(f"\n📋 Quick copy command:")
        print(f"   cp {generator.output_dir}/*.json {generator.user_data_dir}/")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())