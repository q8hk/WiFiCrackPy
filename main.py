# main.py
import argparse
import sys
from core.utils import (
    print_disclaimer,
    log_usage,
    check_dependencies,
    prompt_select,
    print_progress,
    write_recon_log,
    build_recon_report,
)
from core.scanner import NetworkScanner
from core.capture import HandshakeCapturer
from core.crack import HashcatCracker
from core.settings import Settings

TOOL_NAME = "WiFiCrackPy"
TOOL_VERSION = ""


def build_parser():
    settings = Settings()

    dependencies = {
        "hashcat": settings.get('paths', 'hashcat'),
        "hcxtools": settings.get('paths', 'hcxtools')
    }
    parser = argparse.ArgumentParser(
        description="WiFiCrackPy - Educational WPA/WPA2 handshake capture and crack tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--interface', type=str, help='Wi-Fi interface to use')
    parser.add_argument('--check-deps', action='store_true', help='Check required dependencies and exit')
    parser.add_argument('--dry-run', action='store_true', help='Run with mocked commands and dummy data')
    parser.add_argument('--target', type=str, help='Target network identifier (index, SSID, or BSSID)')
    parser.add_argument('-r', '--recon', action='store_true', help='Recon mode (information gathering only)')
    return parser, dependencies


def select_network(networks, target=None):
    if target:
        if target.isdigit():
            index = int(target)
            if 1 <= index <= len(networks):
                return networks[index - 1]
            return None
        lowered = target.lower()
        for network in networks:
            if str(network.get("ssid", "")).lower() == lowered or str(network.get("bssid", "")).lower() == lowered:
                return network
        return None

    choice = prompt_select([n['ssid'] for n in networks], "Select a network to capture handshake: ")
    return networks[choice]


def run_recon(network, argv):
    report = build_recon_report(TOOL_NAME, TOOL_VERSION, network, argv)
    print(report)
    log_path = write_recon_log(network, argv, tool_name=TOOL_NAME, tool_version=TOOL_VERSION)
    print_progress(f"Recon log saved to {log_path}")


def main(argv=None):
    parser, dependencies = build_parser()
    args = parser.parse_args(argv)
    settings = Settings()

    if args.check_deps:
        check_dependencies(dependencies)
        sys.exit(0)

    print_disclaimer()
    if not args.recon and not check_dependencies(dependencies):
        sys.exit(1)

    if args.dry_run:
        networks = [{
            'ssid': 'TestNet',
            'bssid': 'AA:BB:CC:DD:EE:FF',
            'channel': '6',
            'security': 'WPA2',
            'rssi': '-40'
        }]
        print_progress("Using dummy network data for dry run")
    else:
        scanner = NetworkScanner()
        networks = scanner.scan()
        if not networks:
            print("No networks found.")
            sys.exit(1)

    network = select_network(networks, target=args.target)
    if not network:
        print("Target not found. Provide a valid --target or select one from the scan list.")
        sys.exit(1)

    if args.recon:
        run_recon(network, sys.argv if argv is None else [sys.argv[0], *argv])
        sys.exit(0)

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
