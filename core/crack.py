# core/crack.py
import subprocess
from core.utils import print_progress
import os

class HashcatCracker:
    def __init__(self, hashcat_path, wordlist_path):
        self.hashcat_path = hashcat_path
        self.wordlist_path = wordlist_path
        if not os.path.exists(self.wordlist_path):
            print(f"Warning: Default wordlist not found at {self.wordlist_path}")

    def crack(self, hc22000_file):
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

        if mode == 1:
            cmd = [self.hashcat_path, '-m', '22000', hc22000_file, self.wordlist_path, '-O']
        elif mode == 2:
            wordlist = input("Enter path to wordlist: ")
            cmd = [self.hashcat_path, '-m', '22000', hc22000_file, wordlist, '-O']
        elif mode == 3:
            pattern = input("Enter brute-force mask (e.g. ?d?d?d?d?d?d?d?d): ")
            cmd = [self.hashcat_path, '-m', '22000', '-a', '3', hc22000_file, pattern, '-O']
        else:
            print("Run hashcat manually on:", hc22000_file)
            return

        print_progress(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)
        print_progress("Cracking session complete.")
