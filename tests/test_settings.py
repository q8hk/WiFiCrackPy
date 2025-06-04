import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml
from core.settings import Settings


def load_yaml_settings():
    settings_path = Path(__file__).resolve().parents[1] / 'settings.yml'
    with open(settings_path, 'r') as f:
        return yaml.safe_load(f)


def test_settings_paths():
    data = load_yaml_settings()
    settings = Settings()
    assert settings.hashcat_path == data['paths']['hashcat']


def test_default_wordlist():
    data = load_yaml_settings()
    settings = Settings()
    expected = os.path.join(data['paths']['wordlists'], data['hashcat']['default_wordlist'])
    assert settings.default_wordlist == expected
