#!/usr/bin/env python3
"""Check YAML files for encoding issues"""
from pathlib import Path

base_dir = Path.cwd()

for yaml_file in base_dir.rglob('*.yml'):
    try:
        content = yaml_file.read_text(encoding='utf-8')
        raw = yaml_file.read_bytes()
        # Check for BOM or non-UTF-8 bytes
        has_bom = raw[:3] == b'\xef\xbb\xbf'
        non_ascii = [b for b in raw if b > 127]
        crlf = b'\r\n' in raw
        print(f"{yaml_file.name}: size={len(raw)}, BOM={has_bom}, non-ASCII={len(non_ascii)}, CRLF={crlf}")
        if crlf:
            print(f"  -> Converting to LF...")
            yaml_file.write_text(content.replace('\r\n', '\n').replace('\r', '\n'), encoding='utf-8', newline='\n')
    except Exception as e:
        print(f"{yaml_file.name}: ERROR - {e}")
