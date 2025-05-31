# core/scanner.py
import platform
import subprocess
import re
from core.utils import print_table, print_progress

class NetworkScanner:
    def __init__(self):
        self.os = platform.system().lower()
        self.interface = self.detect_interface()

    def detect_interface(self):
        if self.os == "darwin":
            output = subprocess.check_output(['networksetup', '-listallhardwareports']).decode()
            match = re.search(r"Hardware Port: Wi-Fi\nDevice: (en\d+)", output)
            if match:
                iface = match.group(1)
                print_progress(f"Detected Wi-Fi interface: {iface}")
                return iface
        elif self.os == "linux":
            output = subprocess.check_output(['iwconfig']).decode()
            match = re.search(r"^(\w+).*IEEE 802.11", output, re.MULTILINE)
            if match:
                iface = match.group(1)
                print_progress(f"Detected Wi-Fi interface: {iface}")
                return iface
        elif self.os == "windows":
            output = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces']).decode(errors='ignore')
            match = re.search(r"Name\s+:\s+([^\r\n]+)", output)
            if match:
                iface = match.group(1)
                print_progress(f"Detected Wi-Fi interface: {iface}")
                return iface
        raise RuntimeError("Could not detect Wi-Fi interface. Use -i to specify manually.")

    def scan(self):
        print_progress("Scanning for Wi-Fi networks...")
        if self.os == "darwin":
            airport = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
            output = subprocess.check_output(['sudo', airport, '-s']).decode().split('\n')
            networks = self.parse_macos(output)
        elif self.os == "linux":
            output = subprocess.check_output(['sudo', 'iwlist', self.interface, 'scanning']).decode()
            networks = self.parse_linux(output)
        elif self.os == "windows":
            output = subprocess.check_output(['netsh', 'wlan', 'show', 'networks', 'mode=Bssid']).decode(errors='ignore')
            networks = self.parse_windows(output)
        else:
            raise RuntimeError("Unsupported OS for scanning.")

        rows = [[i+1, n['ssid'], n['bssid'], n['channel'], n['security']] for i, n in enumerate(networks)]
        print_table(rows, ["#", "SSID", "BSSID", "Channel", "Security"])
        return networks

    def parse_macos(self, scan_output):
        # skip header line
        networks = []
        for line in scan_output[1:]:
            if not line.strip():
                continue
            try:
                ssid = " ".join(line.split()[:-6])
                bssid = line.split()[-6]
                rssi = line.split()[-5]
                channel = line.split()[-4].split(",")[0]
                security = line.split()[-1]
                networks.append({"ssid": ssid, "bssid": bssid, "channel": channel, "security": security})
            except Exception:
                continue
        return networks

    def parse_linux(self, output):
        networks = []
        for cell in output.split("Cell ")[1:]:
            try:
                ssid = re.search(r'ESSID:"(.*?)"', cell).group(1)
                bssid = re.search(r"Address: ([0-9A-Fa-f:]{17})", cell).group(1)
                channel = re.search(r"Channel:(\d+)", cell).group(1)
                security = "WPA2" if "WPA2" in cell else ("WPA" if "WPA" in cell else "OPEN")
                networks.append({"ssid": ssid, "bssid": bssid, "channel": channel, "security": security})
            except Exception:
                continue
        return networks

    def parse_windows(self, output):
        networks = []
        ssid, bssid, channel, security = None, None, None, None
        for line in output.splitlines():
            if "SSID" in line and "BSSID" not in line:
                if ssid:
                    networks.append({"ssid": ssid, "bssid": bssid, "channel": channel, "security": security})
                ssid = line.split(":", 1)[1].strip()
                bssid, channel, security = None, None, None
            elif "BSSID" in line:
                bssid = line.split(":", 1)[1].strip()
            elif "Channel" in line:
                channel = line.split(":", 1)[1].strip()
            elif "Authentication" in line:
                security = line.split(":", 1)[1].strip()
        if ssid:
            networks.append({"ssid": ssid, "bssid": bssid, "channel": channel, "security": security})
        return networks
