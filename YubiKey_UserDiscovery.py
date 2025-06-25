#!/usr/bin/env python3
"""Identify the owner of a YubiKey OTP from a CSV “log” file."""

import csv
import os
import re
import sys

DEFAULT_CSV = "log.csv"

# Optional color support
try:
    from colorama import Fore, Style, init as color_init
    color_init()
    RED, GREEN, CYAN, RESET = Fore.RED, Fore.GREEN, Fore.CYAN, Style.RESET_ALL
except ImportError:
    RED = GREEN = CYAN = RESET = ""

NUMERIC_TO_MODHEX = {
    '0': 'c', '1': 'b', '2': 'd', '3': 'e', '4': 'f',
    '5': 'g', '6': 'h', '7': 'i', '8': 'j', '9': 'k',
}

def resolve_csv_path() -> str:
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        return sys.argv[1]
    path = input(f"{CYAN}📄  Drag and drop the CSV file here, or press Enter for {DEFAULT_CSV}:{RESET} ").strip()
    return path or DEFAULT_CSV

CSV_FILE = resolve_csv_path()

OTP_RE = re.compile(r"^ubnu(\d{8})")        # ubnu + 8 digits

def convert_numeric_token_to_modhex(numeric_token: str) -> str:
    digits = numeric_token[4:12]
    modhex = ''.join(NUMERIC_TO_MODHEX[d] for d in digits)
    return numeric_token[:4] + modhex

def find_user_by_token(modhex_token: str):
    try:
        with open(CSV_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 5 and row[3].strip().lower() == modhex_token:
                    return row[4]
    except FileNotFoundError:
        print(f"{RED}⛔  CSV file '{CSV_FILE}' not found.{RESET}")
    except Exception as exc:
        print(f"{RED}⛔  Error reading CSV: {exc}{RESET}")
    return None

def main() -> None:
    try:
        while True:
            raw = input(f"{CYAN}🔐  Hold press the YubiKey until OTP code appears:{RESET} ").strip()
            if raw.lower() in {"", "q", "quit", "exit"}:
                print("👋  Good-bye!")
                break

            if not OTP_RE.match(raw):
                print(f"{RED}⛔  OTP must start with 'ubnu' followed by eight digits.{RESET}")
                continue

            token_modhex = convert_numeric_token_to_modhex(raw[:12])
            print(f"{CYAN}🔄  Converted token:{RESET} {token_modhex}")

            user = find_user_by_token(token_modhex)
            if user:
                print(f"{GREEN}✅  Token belongs to user: {user} 🎉{RESET}")
            else:
                print(f"{RED}❌  No match found in '{CSV_FILE}'. 🤔{RESET}")
            print()  # blank line between scans
    except KeyboardInterrupt:
        print("\n👋  Interrupted. Good-bye!")

if __name__ == "__main__":
    main()
