"""
Robust Config Handler with Comprehensive Error Handling
Version History:
• v1.3.0 - Added directory creation and permission checks
• v1.2.0 - Added flexible path resolution and better stake currency handling
• v1.1.0 - Improved error handling and config validation
• v1.0.0 - Initial version with basic config loading
"""
import json
from pathlib import Path
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Version information
VERSION = "1.3.0"
CHANGELOG = {
    "1.3.0": "Added directory creation and permission checks",
    "1.2.0": "Added flexible path resolution and better stake currency handling",
    "1.1.0": "Improved error handling and config validation",
    "1.0.0": "Initial version with basic config loading"
}

def check_directory_permissions(path: Path) -> bool:
    """Check if we have write permissions to a directory"""
    try:
        test_file = path / '.permission_test'
        test_file.touch()
        test_file.unlink()
        return True
    except (PermissionError, OSError) as e:
        logger.warning(f"Permission check failed for {path}: {str(e)}")
        return False

def get_project_root() -> Path:
    """Return the project root folder with multiple fallback options"""
    possible_roots = [
        Path(__file__).parent.parent.parent,  # Default structure
        Path(__file__).parent.parent,         # One level up
        Path.home() / 'freqtrade',            # Common freqtrade location
        Path.cwd(),                           # Current working directory
        Path('/home/facepipe/freqtrade'),     # Explicit path
        Path(os.getenv('FREQTRADE_DIR', ''))  # From environment variable
    ]
    
    for path in possible_roots:
        if path and (path / 'user_data').exists():
            if check_directory_permissions(path / 'user_data'):
                return path
            logger.warning(f"Found user_data at {path} but lacks write permissions")
    return Path.cwd()  # Final fallback

def load_config(quote_currency: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration with comprehensive error handling and defaults
    
    Args:
        quote_currency: Optional quote currency to override config
    
    Returns:
        Dictionary containing complete configuration
    
    Raises:
        FileNotFoundError: If no valid config file can be found
        ValueError: If config is missing required fields
        PermissionError: If required directories cannot be created
    """
    logger.info(f"Loading configuration (v{VERSION})...")
    
    # Create and verify required directories
    user_data_dir = get_project_root() / 'user_data'
    private_dir = user_data_dir / 'private'
    
    for directory in [user_data_dir, private_dir]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            if not check_directory_permissions(directory):
                raise PermissionError(f"Insufficient permissions for {directory}")
        except Exception as e:
            logger.error(f"Failed to create/access directory {directory}: {str(e)}")
            raise
    
    config_locations = [
        private_dir / 'config-private.json',
        user_data_dir / 'config.json',
        Path.home() / '.freqtrade' / 'config.json',
        Path.cwd() / 'config.json',
        Path(os.getenv('FREQTRADE_CONFIG', ''))  # From environment variable
    ]
    
    config_data = None
    used_path = None
    
    # Try all possible config locations
    for config_path in config_locations:
        try:
            if config_path and config_path.exists():
                with open(config_path) as f:
                    config_data = json.load(f)
                used_path = config_path
                logger.info(f"Loaded config from: {config_path}")
                break
        except (json.JSONDecodeError, PermissionError) as e:
            logger.warning(f"Failed to load config from {config_path}: {str(e)}")
            continue
    
    if config_data is None:
        error_msg = "No valid configuration file found. Tried locations:\n"
        error_msg += "\n".join(f"• {str(p)}" for p in config_locations if p)
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Set default stake currency if not provided
    stake_currency = quote_currency or config_data.get('stake_currency') or 'USDT'
    
    # Validate minimal required exchange configuration
    required_exchange_keys = ['name']
    if not all(k in config_data.get('exchange', {}) for k in required_exchange_keys):
        missing = [k for k in required_exchange_keys 
                  if k not in config_data.get('exchange', {})]
        raise ValueError(f"Missing required exchange keys: {missing}")
    
    # Build final config with sensible defaults
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
        'datadir': str(user_data_dir / 'data'),
        'user_data_dir': str(user_data_dir),
        'strategy_path': str(user_data_dir / 'strategies'),
        '_config_source': str(used_path),
        '_config_version': VERSION
    }
    
    # Create additional required directories
    for dir_key in ['datadir', 'strategy_path']:
        dir_path = Path(final_config[dir_key])
        dir_path.mkdir(parents=True, exist_ok=True)
        if not check_directory_permissions(dir_path):
            logger.warning(f"Potential permission issues with {dir_path}")
    
    # Warn about missing API keys if not in dry_run mode
    if not final_config['dry_run'] and (not final_config['exchange']['key'] or not final_config['exchange']['secret']):
        logger.warning("Running in live mode without API keys! Trading will be disabled.")
    
    logger.info(f"Configuration loaded successfully (v{VERSION})")
    return final_config