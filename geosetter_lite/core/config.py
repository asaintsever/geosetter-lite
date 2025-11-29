"""Configuration management for GeoSetter Lite application"""

import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """Manages application configuration with YAML persistence"""
    
    DEFAULT_CONFIG = {
        'ai_settings': {
            'similarity_threshold': 0.85,
            'model_cache_dir': str(Path.home() / '.cache' / 'geosetter_lite'),
        },
        'app_settings': {
            'last_directory': str(Path.home()),
            'exiftool_create_backups': True,
        }
    }
    
    CONFIG_DIR = Path.home() / '.geosetter_lite'
    CONFIG_FILE = CONFIG_DIR / 'config.yaml'
    
    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Load configuration from YAML file or return defaults"""
        try:
            if cls.CONFIG_FILE.exists():
                with open(cls.CONFIG_FILE, 'r') as f:
                    config = yaml.safe_load(f)
                    # Merge with defaults to ensure all keys exist
                    return cls._merge_with_defaults(config)
            else:
                return cls.get_default()
        except Exception as e:
            print(f"Error loading config: {e}")
            return cls.get_default()
    
    @classmethod
    def save(cls, config: Dict[str, Any]) -> None:
        """Save configuration to YAML file"""
        try:
            # Ensure config directory exists
            cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(cls.CONFIG_FILE, 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    @classmethod
    def get_default(cls) -> Dict[str, Any]:
        """Return default configuration"""
        import copy
        return copy.deepcopy(cls.DEFAULT_CONFIG)
    
    @classmethod
    def _merge_with_defaults(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with defaults to ensure all keys exist"""
        result = cls.get_default()
        
        # Update with loaded values
        if config:
            for section, values in config.items():
                if section in result and isinstance(values, dict):
                    result[section].update(values)
                else:
                    result[section] = values
        
        return result
    
    @classmethod
    def get_ai_settings(cls) -> Dict[str, Any]:
        """Get AI-specific settings"""
        config = cls.load()
        return config.get('ai_settings', cls.DEFAULT_CONFIG['ai_settings'])
    
    @classmethod
    def set_ai_settings(cls, ai_settings: Dict[str, Any]) -> None:
        """Update AI settings and save"""
        config = cls.load()
        config['ai_settings'] = ai_settings
        cls.save(config)
    
    @classmethod
    def get_app_settings(cls) -> Dict[str, Any]:
        """Get application settings"""
        import copy
        config = cls.load()
        return copy.deepcopy(config.get('app_settings', cls.DEFAULT_CONFIG['app_settings']))
    
    @classmethod
    def set_app_settings(cls, app_settings: Dict[str, Any]) -> None:
        """Update application settings and save"""
        config = cls.load()
        config['app_settings'] = app_settings
        cls.save(config)

