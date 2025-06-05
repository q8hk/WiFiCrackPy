# core/utils.py
import shutil
import sys
from datetime import datetime
import os
import platform
import subprocess

def print_disclaimer():
    disclaimer = """
\033[93m
==================================================================================
    WiFiCrackPy is intended for EDUCATIONAL and AUTHORIZED SECURITY TESTING ONLY!
    Unauthorized use is ILLEGAL. Do not use this tool against networks you do not
    own or have explicit, written permission to test.

    By typing AGREE you accept all responsibility.
==================================================================================
\033[0m
    """
    ans = input(disclaimer + "\nType AGREE to proceed: ")
    if ans.strip().upper() != 'AGREE':
        print("\nYou must AGREE to the terms to use this tool. Exiting.")
        sys.exit(1)
    log_usage("User accepted disclaimer.")

def log_usage(event: str):
    os.makedirs("results", exist_ok=True)
    with open("results/.usage_log", "a") as f:
        f.write(f"{datetime.now().isoformat()} {event}\n")

def check_dependencies(deps: dict) -> bool:
    missing = []
    for tool, cmd in deps.items():
        if shutil.which(cmd) is None:
            missing.append(tool)
    if missing:
        print("\033[91mMissing dependencies:\033[0m", ", ".join(missing))
        print("Please install them as per README instructions.")
        return False
    return True

def print_table(rows, headers):
    try:
        from prettytable import PrettyTable
        table = PrettyTable(headers)
        for row in rows:
            table.add_row(row)
        print(table)
    except ImportError:
        # fallback to plain print
        print(headers)
        for row in rows:
            print(row)

def prompt_select(options, prompt="Select an option: "):
    while True:
        for idx, opt in enumerate(options, 1):
            print(f"{idx}. {opt}")
        try:
            choice = int(input(prompt))
            if 1 <= choice <= len(options):
                return choice - 1
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")

def color(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

def print_progress(message):
    print(color(f"[+] {message}", "92"))


def find_seclists_wordlist(filename="rockyou.txt"):
    """Attempt to locate a common SecLists wordlist."""
    # 1) Environment variable takes priority
    env_dir = os.environ.get("SECLISTS_DIR")
    if env_dir:
        candidate = os.path.join(env_dir, filename)
        if os.path.exists(candidate):
            return candidate

    # 2) Check configured path from settings.yml
    try:
        from core.settings import Settings
        settings = Settings()
        cfg_candidate = os.path.join(settings.wordlists_path, filename)
        if os.path.exists(cfg_candidate):
            return cfg_candidate
    except Exception:
        # Settings may not be initialised correctly - ignore
        pass

    # 3) Fallback to common system locations
    common_dirs = [
        "/usr/share/wordlists",
        "/usr/share/seclists/Passwords",
        "/usr/local/share/seclists/Passwords",
        "/opt/seclists/Passwords",
        os.path.expanduser("~/SecLists/Passwords"),
    ]
    os_name = platform.system().lower()
    if os_name == "darwin":
        common_dirs.append("/opt/homebrew/share/seclists/Passwords")
    elif os_name == "windows":
        common_dirs.extend([
            r"C:\\Tools\\SecLists\\Passwords",
            r"C:\\SecLists\\Passwords",
        ])

    for base in common_dirs:
        path = os.path.join(base, filename)
        if os.path.exists(path):
            return path
    return None


def prompt_download_seclists(dest="SecLists"):
    """Offer to clone a shallow copy of SecLists and return rockyou path."""
    ans = input("rockyou.txt not found. Download SecLists now? [y/N]: ")
    if ans.strip().lower().startswith("y"):
        repo = "https://github.com/danielmiessler/SecLists.git"
        try:
            subprocess.run(["git", "clone", "--depth", "1", repo, dest], check=True)
            for root, _, files in os.walk(dest):
                if "rockyou.txt" in files:
                    return os.path.join(root, "rockyou.txt")
        except subprocess.CalledProcessError:
            print("Failed to clone SecLists repository.")
    return None
