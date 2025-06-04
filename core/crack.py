# core/crack.py
import subprocess
from core.utils import print_progress
import os
from pathlib import Path

class HashcatCracker:
    def __init__(self, hashcat_path, wordlist_path, dry_run=False):
        self.hashcat_path = hashcat_path
        self.wordlist_path = wordlist_path
        self.dry_run = dry_run
        self.runner = self._mock_run if dry_run else subprocess.run
        if not os.path.exists(self.wordlist_path):
            print(f"Warning: Default wordlist not found at {self.wordlist_path}")
        
        # Create results directory if it doesn't exist
        self.results_dir = Path('results')
        self.results_dir.mkdir(exist_ok=True)

    def crack(self, hc22000_file):
        # Extract SSID from filename
        ssid = Path(hc22000_file).stem
        result_file = self.results_dir / f"{ssid}_cracked.txt"
        
        print_progress(f"Beginning crack for {hc22000_file}")
        print("Attack modes:")
        print("  1. Dictionary attack (using default wordlist)")
        print("  2. Dictionary attack (custom wordlist)")
        print("  3. Brute-force attack")
        print("  4. Manual (custom hashcat)")

        try:
            mode = int(input("Select attack mode [1-4]: "))
        except Exception:
            print("Invalid selection.")
            return

        # Base hashcat command with output file
        base_cmd = [
            self.hashcat_path,
            '-m', '22000',
            '--outfile', str(result_file),
            '--outfile-format', '3',
            hc22000_file,
            '-O'
        ]

        if mode == 1:
            cmd = base_cmd + [self.wordlist_path]
        elif mode == 2:
            wordlist = input("Enter path to wordlist: ")
            cmd = base_cmd + [wordlist]
        elif mode == 3:
            pattern = input("Enter brute-force mask (e.g. ?d?d?d?d?d?d?d?d): ")
            cmd = base_cmd + ['-a', '3', pattern]
        else:
            print(f"Run hashcat manually on: {hc22000_file}")
            print(f"Results will be saved to: {result_file}")
            return

        print_progress(f"Running: {' '.join(cmd)}")
        self.runner(cmd)
        
        if os.path.exists(result_file) and os.path.getsize(result_file) > 0:
            print_progress(f"Cracking completed! Results saved to: {result_file}")
        else:
            print_progress("Cracking completed but no password found.")

    def _mock_run(self, cmd, *args, **kwargs):
        print(f"Mock subprocess.run: {cmd}")
