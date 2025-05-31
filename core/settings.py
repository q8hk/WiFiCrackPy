import os
import yaml
from pathlib import Path

class Settings:
    _instance = None
    _settings = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._load_settings()
        return cls._instance
    
    def _load_settings(self):
        settings_path = Path(__file__).parent.parent / 'settings.yml'
        
        # Create default settings if file doesn't exist
        if not settings_path.exists():
            self._create_default_settings(settings_path)
        
        with open(settings_path, 'r') as f:
            self._settings = yaml.safe_load(f)
    
    def _create_default_settings(self, path):
        default_settings = {
            'paths': {
                'hashcat': 'hashcat',
                'wordlists': 'C:/Tools/SecLists/Passwords',
                'hcxtools': 'hcxpcapngtool'
            },
            'hashcat': {
                'default_wordlist': 'rockyou.txt',
                'attack_mode': 0,
                'hash_mode': 22000
            },
            'capture': {
                'timeout': 300,
                'channel_hop_interval': 2
            }
        }
        
        with open(path, 'w') as f:
            yaml.dump(default_settings, f, default_flow_style=False)
    
    def get(self, *keys):
        """Get a setting value using dot notation"""
        value = self._settings
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value
    
    @property
    def hashcat_path(self):
        return self.get('paths', 'hashcat')
    
    @property
    def wordlists_path(self):
        return self.get('paths', 'wordlists')
    
    @property
    def default_wordlist(self):
        return os.path.join(
            self.wordlists_path,
            self.get('hashcat', 'default_wordlist')
        )