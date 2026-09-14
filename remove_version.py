#!/usr/bin/env python3
"""Remove obsolete version attribute from docker-compose.yml"""
from pathlib import Path

path = Path('docker-compose.yml')
content = path.read_text(encoding='utf-8')
# Remove version line and following blank line
lines = content.split('\n')
new_lines = []
skip_next_blank = False
for line in lines:
    if line.strip().startswith('version:'):
        skip_next_blank = True
        continue
    if skip_next_blank and line.strip() == '':
        skip_next_blank = False
        continue
    new_lines.append(line)
new_content = '\n'.join(new_lines).strip() + '\n'
path.write_text(new_content, encoding='utf-8')
print('Version attribute removed successfully')
