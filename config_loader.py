"""Configuration loader for the translation system."""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration class that loads and validates settings from YAML file."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration from YAML file.
        
        Args:
            config_path: Path to the configuration YAML file
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please copy config.example.yaml to config.yaml and update it with your settings."
            )
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        self._validate()
    
    def _validate(self) -> None:
        """Validate configuration structure and values."""
        required_keys = ['google_cloud', 'languages', 'audio', 'translation']
        for key in required_keys:
            if key not in self._config:
                raise ValueError(f"Missing required configuration section: {key}")
        
        # Validate Google Cloud credentials
        creds_path = self._config['google_cloud'].get('credentials_path')
        if not creds_path:
            raise ValueError("google_cloud.credentials_path is required")
        if not os.path.exists(creds_path):
            raise FileNotFoundError(
                f"Google Cloud credentials file not found: {creds_path}"
            )
        
        # Validate languages
        if 'source' not in self._config['languages']:
            raise ValueError("languages.source is required")
        if 'target' not in self._config['languages']:
            raise ValueError("languages.target is required")
        
        # Set defaults for audio settings
        audio_config = self._config.get('audio', {})
        self._config['audio'] = {
            'input_device': audio_config.get('input_device'),
            'input_device_inbound': audio_config.get('input_device_inbound'),
            'output_device': audio_config.get('output_device'),
            'sample_rate': audio_config.get('sample_rate', 16000),
            'chunk_size': audio_config.get('chunk_size', 4096),
        }
        
        # Set defaults for translation settings
        translation_config = self._config.get('translation', {})
        self._config['translation'] = {
            'model': translation_config.get('model', 'nmt'),
            'voice_ru': translation_config.get('voice_ru', 'ru-RU-Wavenet-D'),
            'voice_uk': translation_config.get('voice_uk', 'uk-UA-Wavenet-A'),
        }
    
    @property
    def google_cloud_credentials(self) -> str:
        """Get path to Google Cloud credentials file."""
        return self._config['google_cloud']['credentials_path']
    
    @property
    def source_language(self) -> str:
        """Get source language code."""
        return self._config['languages']['source']
    
    @property
    def target_language(self) -> str:
        """Get target language code."""
        return self._config['languages']['target']
    
    @property
    def audio_config(self) -> Dict[str, Any]:
        """Get audio configuration."""
        return self._config['audio']
    
    @property
    def translation_config(self) -> Dict[str, Any]:
        """Get translation configuration."""
        return self._config['translation']
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key path (e.g., 'audio.sample_rate')."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
