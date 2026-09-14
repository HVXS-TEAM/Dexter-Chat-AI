#!/usr/bin/env python3
"""Create a simple docker-compose test file"""
from pathlib import Path

path = Path('docker-compose-test.yml')
content = """services:
  test:
    image: alpine:latest
    command: echo hello
"""
path.write_text(content, encoding='utf-8', newline='\n')
print('docker-compose-test.yml created successfully')
