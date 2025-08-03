"""
Robust Config Handler with Comprehensive Error Handling
Version History:
• v1.4.0 - Fixed path resolution for pair_analyzer subdirectory structure
• v1.3.0 - Added directory creation and permission checks
"""
import json
from pathlib import Path
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Version information
VERSION = "1.4.0"

def check_directory_permissions(path: Path) -> bool:
    """Check if we have write permissions to a directory"""
    try:
        test_file = path / '.permission_test'
        test_file.touch()
        test_file.unlink()
        return True
    except (PermissionError, OSError) as e:
        logger.debug(f"Permission check failed for {path}: {str(e)}")
        return False

def get_project_root() -> Path:
    """Return the freqtrade project root with specific handling for pair_analyzer structure"""
    current_dir = Path.cwd()
    
    # Priority order for finding freqtrade root
    possible_roots = []
    
    # If we're in pair_analyzer subdirectory, go up one level
    if current_dir.name == 'pair_analyzer':
        possible_roots.append(current_dir.parent)
    
    # Add other common locations
    possible_roots.extend([
        current_dir,  # Current directory
        Path('/home/facepipe/freqtrade'),  # Your specific path
        Path.home() / 'freqtrade',  # Home freqtrade
        Path(__file__).parent.parent.parent,  # Relative to this file
    ])
    
    # Also check environment variable
    if os.getenv('FREQTRADE_DIR'):
        possible_roots.insert(0, Path(os.getenv('FREQTRADE_DIR')))
    
    logger.debug(f"Searching for freqtrade root in: {[str(p) for p in possible_roots]}")
    
    for path in possible_roots:
        if path and path.exists():
            user_data = path / 'user_data'
            if user_data.exists():
                logger.info(f"Found freqtrade root at: {path}")
                if check_directory_permissions(user_data):
                    return path
                else:
                    logger.warning(f"Found user_data at {path} but lacks write permissions")
    
    # Final fallback
    logger.warning("Could not find freqtrade root, using current directory")
    return current_dir

def load_config(quote_currency: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration with comprehensive error handling and defaults
    """
    logger.info(f"Loading configuration (v{VERSION})...")
    
    # Get the freqtrade root directory
    freqtrade_root = get_project_root()
    user_data_dir = freqtrade_root / 'user_data'
    private_dir = user_data_dir / 'private'
    
    logger.info(f"Using freqtrade root: {freqtrade_root}")
    logger.info(f"User data directory: {user_data_dir}")
    
    # Create required directories
    for directory in [user_data_dir, private_dir]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            if not check_directory_permissions(directory):
                logger.warning(f"Limited permissions for {directory}")
        except Exception as e:
            logger.error(f"Failed to create/access directory {directory}: {str(e)}")
    
    # Look for configuration files in priority order
    config_locations = [
        private_dir / 'config-private.json',
        user_data_dir / 'config.json',
        freqtrade_root / 'config.json',
        Path.home() / '.freqtrade' / 'config.json',
    ]
    
    # Add environment variable path if set
    if os.getenv('FREQTRADE_CONFIG'):
        config_locations.insert(0, Path(os.getenv('FREQTRADE_CONFIG')))
    
    config_data = None
    used_path = None
    
    logger.debug(f"Searching for config in: {[str(p) for p in config_locations]}")
    
    # Try all possible config locations
    for config_path in config_locations:
        try:
            if config_path and config_path.exists():
                logger.debug(f"Trying to load config from: {config_path}")
                with open(config_path) as f:
                    config_data = json.load(f)
                used_path = config_path
                logger.info(f"✓ Loaded config from: {config_path}")
                break
        except (json.JSONDecodeError, PermissionError, FileNotFoundError) as e:
            logger.debug(f"Failed to load config from {config_path}: {str(e)}")
            continue
    
    # If no config found, create a minimal one
    if config_data is None:
        logger.warning("No configuration file found, creating minimal config")
        config_data = create_minimal_config(user_data_dir / 'config.json')
        used_path = user_data_dir / 'config.json'
    
    # Set default stake currency
    stake_currency = quote_currency or config_data.get('stake_currency') or 'USDT'
    
    # Validate exchange configuration
    if 'exchange' not in config_data or 'name' not in config_data.get('exchange', {}):
        logger.warning("No exchange configuration found, using binance as default")
        config_data['exchange'] = {'name': 'binance'}
    
    # Build final config with absolute paths
    data_dir = user_data_dir / 'data'
    strategies_dir = user_data_dir / 'strategies'
    
    final_config = {
        'runmode': config_data.get('runmode', 'dry_run'),
        'exchange': {
            'name': config_data['exchange']['name'],
            'key': config_data['exchange'].get('key', ''),
            'secret': config_data['exchange'].get('secret', ''),
            'ccxt_config': {
                'enableRateLimit': True,
                **config_data['exchange'].get('ccxt_config', {})
            },
            'ccxt_async_config': config_data['exchange'].get('ccxt_async_config', {})
        },
        'stake_currency': stake_currency,
        'dry_run': config_data.get('dry_run', True),
        'dataformat': config_data.get('dataformat', 'json'),
        'datadir': str(data_dir),
        'user_data_dir': str(user_data_dir),
        'strategy_path': str(strategies_dir),
        '_config_source': str(used_path),
        '_config_version': VERSION,
        '_freqtrade_root': str(freqtrade_root)
    }
    
    # Create data and strategies directories
    for dir_path in [data_dir, strategies_dir]:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create directory {dir_path}: {e}")
    
    # Log configuration details
    logger.info(f"Configuration summary:")
    logger.info(f"  Exchange: {final_config['exchange']['name']}")
    logger.info(f"  Stake currency: {final_config['stake_currency']}")
    logger.info(f"  Data directory: {final_config['datadir']}")
    logger.info(f"  Dry run: {final_config['dry_run']}")
    
    return final_config

def create_minimal_config(config_path: Path) -> Dict[str, Any]:
    """Create a minimal working configuration"""
    logger.info(f"Creating minimal config at: {config_path}")
    
    minimal_config = {
        "dry_run": True,
        "stake_currency": "USDT",
        "exchange": {
            "name": "binance",
            "ccxt_config": {
                "enableRateLimit": True
            }
        },
        "dataformat": "json"
    }
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(minimal_config, f, indent=2)
        logger.info(f"✓ Created minimal config at: {config_path}")
    except Exception as e:
        logger.error(f"Failed to create minimal config: {e}")
    
    return minimal_config