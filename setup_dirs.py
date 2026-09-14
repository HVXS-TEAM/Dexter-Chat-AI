#!/usr/bin/env python3
"""Helper to create the missing domain directories with __init__.py files."""
import os

BASE_DIR = "dexter-calc"

for rel in ["dexter_calc/finance", "dexter_calc/banque"]:
    abs_dir = os.path.join(BASE_DIR, rel)
    os.makedirs(abs_dir, exist_ok=True)
    init_path = os.path.join(abs_dir, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("")
    print(f"OK {rel}")
