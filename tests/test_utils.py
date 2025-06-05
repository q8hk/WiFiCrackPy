import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.utils import find_seclists_wordlist, find_seclists_file


def test_find_seclists_env(tmp_path, monkeypatch):
    seclists = tmp_path / "SecLists" / "Passwords"
    seclists.mkdir(parents=True)
    rockyou = seclists / "rockyou.txt"
    rockyou.write_text("dummy")

    monkeypatch.setenv("SECLISTS_DIR", str(seclists))
    assert find_seclists_wordlist() == str(rockyou)


def test_find_seclists_file_env(tmp_path, monkeypatch):
    base = tmp_path / "SecLists" / "Passwords" / "WiFi-WPA"
    base.mkdir(parents=True)
    wordlist = base / "probable-v2-wpa-top62.txt"
    wordlist.write_text("dummy")

    monkeypatch.setenv("SECLISTS_DIR", str(tmp_path / "SecLists" / "Passwords"))
    result = find_seclists_file("WiFi-WPA/probable-v2-wpa-top62.txt")
    assert result == str(wordlist)
