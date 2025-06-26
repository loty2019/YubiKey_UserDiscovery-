#!/usr/bin/env python3
"""Lookup ⇆ reverse-lookup YubiKey tokens against a CSV “log” file."""

import csv
import os
import re
import sys

DEFAULT_CSV = "log.csv"

# ── Optional colour support ────────────────────────────────────────────────────
try:
    from colorama import Fore, Style, init as color_init
    color_init()
    RED, GREEN, CYAN, RESET = Fore.RED, Fore.GREEN, Fore.CYAN, Style.RESET_ALL
except ImportError:            # colourama not installed
    RED = GREEN = CYAN = RESET = ""

# ── Modhex map ────────────────────────────────────────────────────────────────
NUMERIC_TO_MODHEX = {
    '0': 'c', '1': 'b', '2': 'd', '3': 'e', '4': 'f',
    '5': 'g', '6': 'h', '7': 'i', '8': 'j', '9': 'k',
}

# ── Helper functions ──────────────────────────────────────────────────────────
def resolve_csv_path() -> str:
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        return sys.argv[1]
    path = input(f"{CYAN}📄  Drag & drop CSV or press Enter for {DEFAULT_CSV}:{RESET} ").strip()
    return path or DEFAULT_CSV

def convert_numeric_token_to_modhex(numeric_token: str) -> str:
    digits = numeric_token[4:12]
    modhex = ''.join(NUMERIC_TO_MODHEX[d] for d in digits)
    return numeric_token[:4] + modhex                        # keep 'ubnu'

def load_csv_rows(path: str):
    with open(path, newline='', encoding='utf-8') as fp:
        reader = csv.reader(fp)
        next(reader, None)                                   # skip header
        return list(reader)

# ── CSV setup ────────────────────────────────────────────────────────────────
CSV_FILE = resolve_csv_path()
try:
    ROWS = load_csv_rows(CSV_FILE)
except FileNotFoundError:
    print(f"{RED}⛔  CSV file '{CSV_FILE}' not found. Exiting.{RESET}")
    sys.exit(1)

# ── Choose lookup direction ───────────────────────────────────────────────────
print(f"{CYAN}🔁  Choose lookup mode:{RESET}")
print("  1) 🔑  OTP  → USER (default)")
print("  2) 👤  USER → OTP  (reverse)")
mode = input("Select 1 or 2: ").strip()
reverse = (mode == "2")

OTP_RE = re.compile(r"^ubnu(\d{8})")          # ubnu + 8 digits (first 12 chars)

# ── Main loop ─────────────────────────────────────────────────────────────────
try:
    while True:
        if reverse:
            prompt = f"{CYAN}👤  Enter username (or q to quit):{RESET} "
            query = input(prompt).strip()
            if query.lower() in {"", "q", "quit", "exit"}:
                print("👋  Good-bye!")
                break

            matches = [row for row in ROWS if len(row) >= 5 and row[4].strip().lower() == query.lower()]
            if matches:
                for row in matches:
                    print(f"{GREEN}✅  User {row[4]} owns token: {row[3]} 🎉{RESET}")
            else:
                print(f"{RED}❌  No token found for user “{query}”. 🤔{RESET}")
            print()  # spacer
        else:
            prompt = f"{CYAN}🔐  Hold press the YubiKey until OTP appears (q to quit):{RESET} "
            raw = input(prompt).strip()
            if raw.lower() in {"", "q", "quit", "exit"}:
                print("👋  Good-bye!")
                break

            if not OTP_RE.match(raw):
                print(f"{RED}⛔  OTP must start with 'ubnu' and have 8 digits.{RESET}")
                continue

            token_modhex = convert_numeric_token_to_modhex(raw[:12])
            print(f"{CYAN}🔄  Converted token:{RESET} {token_modhex}")

            user = next((row[4] for row in ROWS
                         if len(row) >= 5 and row[3].strip().lower() == token_modhex), None)
            if user:
                print(f"{GREEN}✅  Token belongs to user: {user} 🎉{RESET}")
            else:
                print(f"{RED}❌  No match found in '{CSV_FILE}'. 🤔{RESET}")
            print()
except KeyboardInterrupt:
    print("\n👋  Interrupted. Good-bye!")
