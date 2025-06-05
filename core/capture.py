# core/capture.py
import platform
import subprocess
import os
import shutil
from core.utils import print_progress

class HandshakeCapturer:
    def __init__(self, interface, dry_run=False):
        self.os = platform.system().lower()
        self.interface = interface
        self.dry_run = dry_run
        self.runner = self._mock_run if dry_run else subprocess.run

    def capture(self, network):
        ssid = network['ssid']
        bssid = network['bssid']
        channel = network['channel']
        print_progress(f"Preparing to capture handshake for {ssid} ({bssid}) on channel {channel}")

        # Create directory for this SSID's captures
        ssid_name = ssid.replace(' ', '_')
        capture_dir = f"captures/{ssid_name}"
        os.makedirs(capture_dir, exist_ok=True)

        pcap_file = f"{capture_dir}/{ssid_name}.pcap"
        hc22000_file = f"{capture_dir}/{ssid_name}.hc22000"

        if self.os == "darwin":
            zizzania = os.path.expanduser('~/zizzania/src/zizzania')
            self.runner(['sudo', zizzania, '-i', self.interface, '-b', bssid, '-q', '-w', pcap_file])
        elif self.os == "linux":
            # Use zizzania if available, else fallback to tcpdump
            if shutil.which('zizzania'):
                self.runner(['sudo', 'zizzania', '-i', self.interface, '-b', bssid, '-q', '-w', pcap_file])
            else:
                self.runner(['sudo', 'tcpdump', '-i', self.interface, '-w', pcap_file, 'ether proto 0x888e'])
        elif self.os == "windows":
            self.runner(['dumpcap', '-i', self.interface, '-w', pcap_file])
        else:
            raise RuntimeError("Unsupported OS for capture.")

        print_progress("Converting capture to hashcat format...")
        self.runner(['hcxpcapngtool', '-o', hc22000_file, pcap_file])
        print_progress("Handshake conversion complete.")
        return hc22000_file

    def _mock_run(self, cmd, *args, **kwargs):
        print(f"Mock subprocess.run: {cmd}")
