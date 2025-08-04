# FILENAME: utils/pairlist_handler.py
# ACTION: CREATE NEW FILE
# DESCRIPTION: Handles loading pairs from Freqtrade config files

"""
Pairlist Handler - Load pairs from Freqtrade config files
Version: 1.0.0

This module handles loading pairlists from various Freqtrade configuration sources
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Union
import re

logger = logging.getLogger(__name__)

class PairlistHandler:
    """
    Handler for loading and managing pairlists from Freqtrade configurations
    """
    
    def __init__(self, user_data_dir: Path = None):
        self.user_data_dir = user_data_dir or Path("/home/facepipe/freqtrade/user_data")
        self.config_cache = {}
        logger.info(f"PairlistHandler initialized with user_data_dir: {self.user_data_dir}")
    
    def find_config_files(self) -> List[Path]:
        """Find all potential config files in user_data directory"""
        config_files = []
        
        # Common config file patterns
        patterns = [
            "config*.json",
            "strategy*.json", 
            "*config*.json",
            "private/*.json"
        ]
        
        for pattern in patterns:
            config_files.extend(self.user_data_dir.glob(pattern))
        
        # Also check subdirectories
        for subdir in ["configs", "strategies", "private"]:
            subdir_path = self.user_data_dir / subdir
            if subdir_path.exists():
                config_files.extend(subdir_path.glob("*.json"))
        
        # Remove duplicates and sort
        unique_configs = list(set(config_files))
        unique_configs.sort()
        
        logger.info(f"Found {len(unique_configs)} config files")
        return unique_configs
    
    def load_config_file(self, config_path: Path) -> Optional[Dict]:
        """Load and parse a single config file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Cache the config
            self.config_cache[str(config_path)] = config
            logger.debug(f"Loaded config: {config_path.name}")
            return config
            
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            logger.warning(f"Could not load config {config_path}: {e}")
            return None
    
    def extract_pairs_from_config(self, config: Dict, config_name: str = "") -> Set[str]:
        """Extract all pairs from a config dictionary"""
        pairs = set()
        
        # Direct pair_whitelist (top level)
        if 'pair_whitelist' in config:
            whitelist = config['pair_whitelist']
            if isinstance(whitelist, list):
                # Clean up escaped slashes and normalize pairs
                clean_pairs = [pair.replace('\\/', '/') for pair in whitelist]
                pairs.update(clean_pairs)
                logger.debug(f"Found {len(clean_pairs)} pairs in top-level pair_whitelist of {config_name}")
        
        # Exchange pair_whitelist (most common in your format)
        if 'exchange' in config and isinstance(config['exchange'], dict):
            if 'pair_whitelist' in config['exchange']:
                exchange_pairs = config['exchange']['pair_whitelist']
                if isinstance(exchange_pairs, list):
                    # Clean up escaped slashes and normalize pairs
                    clean_pairs = [pair.replace('\\/', '/') for pair in exchange_pairs]
                    pairs.update(clean_pairs)
                    logger.debug(f"Found {len(clean_pairs)} pairs in exchange.pair_whitelist of {config_name}")
        
        # Pairlist configurations (for dynamic pairlists)
        if 'pairlists' in config:
            for pairlist in config['pairlists']:
                if isinstance(pairlist, dict):
                    # StaticPairList with embedded pairs
                    if pairlist.get('method') == 'StaticPairList':
                        if 'config' in pairlist and 'pair_whitelist' in pairlist['config']:
                            static_pairs = pairlist['config']['pair_whitelist']
                            clean_pairs = [pair.replace('\\/', '/') for pair in static_pairs]
                            pairs.update(clean_pairs)
                            logger.debug(f"Found {len(clean_pairs)} pairs in StaticPairList of {config_name}")
        
        # Strategy-specific pairs (for strategy configs)
        if 'strategy' in config and isinstance(config['strategy'], dict):
            if 'pair_whitelist' in config['strategy']:
                strategy_pairs = config['strategy']['pair_whitelist']
                if isinstance(strategy_pairs, list):
                    clean_pairs = [pair.replace('\\/', '/') for pair in strategy_pairs]
                    pairs.update(clean_pairs)
                    logger.debug(f"Found {len(clean_pairs)} pairs in strategy config of {config_name}")
        
        # Log pair extraction summary
        if pairs:
            logger.info(f"Extracted {len(pairs)} pairs from {config_name}")
            if logger.isEnabledFor(logging.DEBUG):
                sample_pairs = list(pairs)[:5]
                logger.debug(f"Sample pairs from {config_name}: {sample_pairs}")
        
        return pairs
    
    def get_pairs_by_quote_currency(self, pairs: Set[str], quote_currency: str) -> List[str]:
        """Filter pairs by quote currency"""
        quote_pairs = []
        quote_suffix = f"/{quote_currency.upper()}"
        
        for pair in pairs:
            if pair.endswith(quote_suffix):
                quote_pairs.append(pair)
        
        return sorted(quote_pairs)
    
    def load_all_pairlists(self, quote_currency: str = None) -> Dict[str, List[str]]:
        """
        Load pairlists from all config files
        
        Returns:
            Dict with config names as keys and pair lists as values
        """
        all_pairlists = {}
        config_files = self.find_config_files()
        
        if not config_files:
            logger.warning("No config files found")
            return all_pairlists
        
        for config_path in config_files:
            config = self.load_config_file(config_path)
            if config is None:
                continue
            
            config_name = config_path.stem
            pairs = self.extract_pairs_from_config(config, config_name)
            
            if pairs:
                if quote_currency:
                    # Filter by quote currency
                    filtered_pairs = self.get_pairs_by_quote_currency(pairs, quote_currency)
                    if filtered_pairs:
                        all_pairlists[config_name] = filtered_pairs
                else:
                    # Include all pairs
                    all_pairlists[config_name] = sorted(list(pairs))
        
        logger.info(f"Loaded pairlists from {len(all_pairlists)} configs")
        return all_pairlists
    
    def get_combined_pairlist(self, quote_currency: str = None, 
                            exclude_configs: List[str] = None) -> List[str]:
        """
        Get a combined list of all unique pairs from all configs
        
        Args:
            quote_currency: Filter by quote currency
            exclude_configs: List of config names to exclude
            
        Returns:
            Sorted list of unique pairs
        """
        all_pairlists = self.load_all_pairlists(quote_currency)
        exclude_configs = exclude_configs or []
        
        combined_pairs = set()
        
        for config_name, pairs in all_pairlists.items():
            if config_name not in exclude_configs:
                combined_pairs.update(pairs)
        
        result = sorted(list(combined_pairs))
        logger.info(f"Combined pairlist contains {len(result)} unique pairs")
        return result
    
    def get_pairlist_by_config(self, config_name: str, quote_currency: str = None) -> List[str]:
        """
        Get pairlist from a specific config file
        
        Args:
            config_name: Name of the config file (without .json extension)
            quote_currency: Filter by quote currency
            
        Returns:
            List of pairs from the specified config
        """
        all_pairlists = self.load_all_pairlists(quote_currency)
        
        # Try exact match first
        if config_name in all_pairlists:
            return all_pairlists[config_name]
        
        # Try partial match
        for name, pairs in all_pairlists.items():
            if config_name.lower() in name.lower():
                logger.info(f"Using partial match: {name} for requested {config_name}")
                return pairs
        
        logger.warning(f"Config '{config_name}' not found")
        return []
    
    def list_available_configs(self, quote_currency: str = None) -> Dict[str, int]:
        """
        List all available configs with pair counts
        
        Returns:
            Dict with config names as keys and pair counts as values
        """
        all_pairlists = self.load_all_pairlists(quote_currency)
        
        config_summary = {}
        for config_name, pairs in all_pairlists.items():
            config_summary[config_name] = len(pairs)
        
        return config_summary
    
    def analyze_pairlist_overlap(self, quote_currency: str = None) -> Dict:
        """
        Analyze overlap between different pairlists
        
        Returns:
            Analysis of pair overlap between configs
        """
        all_pairlists = self.load_all_pairlists(quote_currency)
        
        if len(all_pairlists) < 2:
            return {"message": "Need at least 2 configs to analyze overlap"}
        
        # Find common pairs across all configs
        config_names = list(all_pairlists.keys())
        common_pairs = set(all_pairlists[config_names[0]])
        
        for config_name in config_names[1:]:
            common_pairs &= set(all_pairlists[config_name])
        
        # Find unique pairs for each config
        unique_pairs = {}
        for config_name, pairs in all_pairlists.items():
            others_pairs = set()
            for other_name, other_pairs in all_pairlists.items():
                if other_name != config_name:
                    others_pairs.update(other_pairs)
            
            unique_pairs[config_name] = list(set(pairs) - others_pairs)
        
        analysis = {
            "total_configs": len(all_pairlists),
            "common_pairs": sorted(list(common_pairs)),
            "common_count": len(common_pairs),
            "unique_pairs": unique_pairs,
            "config_sizes": {name: len(pairs) for name, pairs in all_pairlists.items()}
        }
        
        return analysis
    
    def export_pairlist(self, pairs: List[str], output_path: Path, 
                       format_type: str = "json") -> bool:
        """
        Export a pairlist to a file
        
        Args:
            pairs: List of pairs to export
            output_path: Path to save the file
            format_type: Format ('json', 'txt', 'csv')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == "json":
                with open(output_path, 'w') as f:
                    json.dump({"pair_whitelist": pairs}, f, indent=2)
            
            elif format_type == "txt":
                with open(output_path, 'w') as f:
                    f.write('\n'.join(pairs))
            
            elif format_type == "csv":
                with open(output_path, 'w') as f:
                    f.write("pair\n")
                    f.write('\n'.join(pairs))
            
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            logger.info(f"Exported {len(pairs)} pairs to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export pairlist: {e}")
            return False