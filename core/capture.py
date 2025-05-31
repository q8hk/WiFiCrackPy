# core/capture.py
import platform
import subprocess
import os
from core.utils import print_progress

class HandshakeCapturer:
    def __init__(self, interface):
        self.os = platform.system().lower()
        self.interface = interface

    def capture(self, network):
        ssid = network['ssid']
        bssid = network['bssid']
        channel = network['channel']
        print_progress(f"Preparing to capture handshake for {ssid} ({bssid}) on channel {channel}")

        pcap_file = f"results/{ssid.replace(' ', '_')}.pcap"
        hc22000_file = f"results/{ssid.replace(' ', '_')}.hc22000"

        if self.os == "darwin":
            zizzania = os.path.expanduser('~/zizzania/src/zizzania')
            subprocess.run(['sudo', zizzania, '-i', self.interface, '-b', bssid, '-q', '-w', pcap_file])
        elif self.os == "linux":
            # Use zizzania if available, else fallback to tcpdump
            if shutil.which('zizzania'):
                subprocess.run(['sudo', 'zizzania', '-i', self.interface, '-b', bssid, '-q', '-w', pcap_file])
            else:
                subprocess.run(['sudo', 'tcpdump', '-i', self.interface, '-w', pcap_file, 'ether proto 0x888e']) # 802.1X packets
        elif self.os == "windows":
            subprocess.run(['dumpcap', '-i', self.interface, '-w', pcap_file])
        else:
            raise RuntimeError("Unsupported OS for capture.")

        print_progress("Converting capture to hashcat format...")
        subprocess.run(['hcxpcapngtool', '-o', hc22000_file, pcap_file])
        print_progress("Handshake conversion complete.")
        return hc22000_file
