# main.py
import argparse
import sys
from core.utils import print_disclaimer, log_usage, check_dependencies, prompt_select, print_progress
from core.scanner import NetworkScanner
from core.capture import HandshakeCapturer
from core.crack import HashcatCracker
from core.settings import Settings

def main():
    settings = Settings()
    
    DEPENDENCIES = {
        "hashcat": settings.get('paths', 'hashcat'),
        "hcxtools": settings.get('paths', 'hcxtools')
    }

    parser = argparse.ArgumentParser(
        description="WiFiCrackPy - Educational WPA/WPA2 handshake capture and crack tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--interface', type=str, help='Wi-Fi interface to use')
    parser.add_argument('--check-deps', action='store_true', help='Check required dependencies and exit')
    parser.add_argument('--dry-run', action='store_true', help='Run with mocked commands and dummy data')
    args = parser.parse_args()

    if args.check_deps:
        check_dependencies(DEPENDENCIES)
        sys.exit(0)

    print_disclaimer()
    if not check_dependencies(DEPENDENCIES):
        sys.exit(1)

    if args.dry_run:
        networks = [{
            'ssid': 'TestNet',
            'bssid': 'AA:BB:CC:DD:EE:FF',
            'channel': '6',
            'security': 'WPA2'
        }]
        print_progress("Using dummy network data for dry run")
        network = networks[0]
    else:
        scanner = NetworkScanner()
        networks = scanner.scan()
        if not networks:
            print("No networks found.")
            sys.exit(1)
        choice = prompt_select([n['ssid'] for n in networks], "Select a network to capture handshake: ")
        network = networks[choice]

    iface = None
    if args.dry_run:
        iface = 'wlan0'
    else:
        iface = scanner.interface if not args.interface else args.interface

    capturer = HandshakeCapturer(iface, dry_run=args.dry_run)
    hc22000_file = capturer.capture(network)
    print_progress(f"Handshake saved as {hc22000_file}")

    cracker = HashcatCracker(
        hashcat_path=settings.hashcat_path,
        wordlist_path=settings.default_wordlist,
        dry_run=args.dry_run
    )
    cracker.crack(hc22000_file)

    log_usage("Session complete.")

if __name__ == "__main__":
    main()
