# core/utils.py
import shutil
import sys
from datetime import datetime
import os

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
