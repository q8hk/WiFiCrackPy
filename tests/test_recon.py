import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import WiFiCrackPy


def test_recon_flag_parsing():
    parser = WiFiCrackPy.build_parser()
    args = parser.parse_args(["-r"])
    assert args.recon is True
    args = parser.parse_args(["--recon"])
    assert args.recon is True


def test_recon_writes_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dummy_network = {
        "ssid": "TestNet",
        "bssid": "AA:BB:CC:DD:EE:FF",
        "channel": "6",
        "security": "WPA2",
        "rssi": "-40",
    }

    monkeypatch.setattr(WiFiCrackPy, "scan_networks", lambda target=None: dummy_network)

    def fail_attack(*args, **kwargs):
        raise AssertionError("Attack logic should not run during recon.")

    monkeypatch.setattr(WiFiCrackPy, "capture_network", fail_attack)
    monkeypatch.setattr(WiFiCrackPy, "crack_capture", fail_attack)

    exit_code = WiFiCrackPy.main(["--recon"])
    assert exit_code == 0

    logs = list((tmp_path / "logs").glob("recon_*"))
    assert logs, "Recon should write a log file."


def test_recon_conflict_with_attack_flags():
    exit_code = WiFiCrackPy.main(["--recon", "-m", "1"])
    assert exit_code == 2
