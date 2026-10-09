#!/usr/bin/env python3
"""Check every production Survival map command against retail fastfile names."""
from pathlib import Path
import re
root = Path(__file__).resolve().parents[4]
files = ['ports/ios/app/engine_app.mm', 'ports/ios/survival/survival_engine.cpp']
commands = []
for name in files:
    source = (root / name).read_text()
    if name.endswith('engine_app.mm'):
        source = '\n'.join(line for line in source.splitlines() if 'fs_game mods/specops_survival' in line)
    commands.extend((name, target) for target in re.findall(r'devmap ([a-z0-9_]+)', source))
assert len(commands) == 3, f'Expected startup, retry and mode-switch commands: {commands}'
# Original PC data has bog_a.ff and bog_b.ff; it has no bog.ff.
retail_fastfiles = {'bog_a.ff', 'bog_b.ff'}
for name, target in commands:
    assert target + '.ff' in retail_fastfiles, f'{name} requests missing retail fastfile {target}.ff'
    assert target == 'bog_a', f'{name} must start the first Bog mission'
print('Survival startup, retry and mode switch all load original bog_a.ff')
