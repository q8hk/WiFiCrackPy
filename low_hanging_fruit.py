#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path

from core.settings import Settings
from core.utils import find_seclists_file, print_progress


def locate_wordlist(custom):
    if custom and os.path.exists(custom):
        return custom
    path = find_seclists_file("WiFi-WPA/probable-v2-wpa-top4800.txt")
    if path:
        return path
    return None


def is_cracked(hcfile, hashcat):
    res = subprocess.run([hashcat, '-m', '22000', '--show', hcfile], capture_output=True, text=True)
    return res.stdout.strip()


def run_hashcat(cmd, session):
    restore = Path(f'{session}.restore')
    if restore.exists():
        print_progress(f"Resuming session {session}")
        subprocess.run([cmd[0], '--restore', '--session', session], check=True)
    else:
        subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description='Automate low hanging fruit WPA cracking')
    parser.add_argument('capture', help='Path to .hc22000 file')
    parser.add_argument('--wordlist', help='WiFi-WPA wordlist')
    parser.add_argument('--rule', default='best64.rule', help='Hashcat rule file')
    parser.add_argument('--hashcat', default=Settings().hashcat_path, help='Hashcat binary')
    parser.add_argument('--progress', default='results/lhf_progress.json', help='Progress file')
    args = parser.parse_args()

    wordlist = locate_wordlist(args.wordlist)
    if not wordlist:
        print('WiFi-WPA wordlist not found')
        return

    progress_path = Path(args.progress)
    progress_path.parent.mkdir(exist_ok=True)
    progress = {'stage': 0}
    if progress_path.exists():
        progress = json.loads(progress_path.read_text())

    stages = [
        {
            'name': 'wordlist',
            'session': 'lhf_dict',
            'cmd': [args.hashcat, '-m', '22000', '-a', '0', args.capture, wordlist,
                    '-r', args.rule, '--session', 'lhf_dict', '--potfile-path', 'results/hashcat.potfile']
        },
        {
            'name': 'bf8',
            'session': 'lhf_bf8',
            'cmd': [args.hashcat, '-m', '22000', '-a', '3', args.capture,
                    '?d?d?d?d?d?d?d?d', '--session', 'lhf_bf8', '--potfile-path', 'results/hashcat.potfile']
        },
        {
            'name': 'bf9',
            'session': 'lhf_bf9',
            'cmd': [args.hashcat, '-m', '22000', '-a', '3', args.capture,
                    '?d?d?d?d?d?d?d?d?d', '--session', 'lhf_bf9', '--potfile-path', 'results/hashcat.potfile']
        },
        {
            'name': 'bf10',
            'session': 'lhf_bf10',
            'cmd': [args.hashcat, '-m', '22000', '-a', '3', args.capture,
                    '?d?d?d?d?d?d?d?d?d?d', '--session', 'lhf_bf10', '--potfile-path', 'results/hashcat.potfile']
        },
        {
            'name': 'bf11',
            'session': 'lhf_bf11',
            'cmd': [args.hashcat, '-m', '22000', '-a', '3', args.capture,
                    '?d?d?d?d?d?d?d?d?d?d?d', '--session', 'lhf_bf11', '--potfile-path', 'results/hashcat.potfile']
        },
        {
            'name': 'bf12',
            'session': 'lhf_bf12',
            'cmd': [args.hashcat, '-m', '22000', '-a', '3', args.capture,
                    '?d?d?d?d?d?d?d?d?d?d?d?d', '--session', 'lhf_bf12', '--potfile-path', 'results/hashcat.potfile']
        },
    ]

    for idx in range(progress.get('stage', 0), len(stages)):
        stage = stages[idx]
        print_progress(f"Starting {stage['name']} stage")
        run_hashcat(stage['cmd'], stage['session'])
        if is_cracked(args.capture, args.hashcat):
            print_progress(f"Password found during {stage['name']} stage!")
            progress['stage'] = len(stages)
            progress_path.write_text(json.dumps(progress))
            return
        progress['stage'] = idx + 1
        progress_path.write_text(json.dumps(progress))

    print_progress('All stages completed without success')


if __name__ == '__main__':
    main()
