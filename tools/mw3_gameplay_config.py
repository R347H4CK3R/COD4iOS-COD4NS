"""Shared MW3-preferred gameplay definitions for COD4iOS staging.
Configuration resolver only; not wired to in-game C++ runtime yet.
"""
from __future__ import annotations
import json
from pathlib import Path

CATEGORIES = frozenset({'weapon','attachment','perk','lethal','tactical','killstreak'})
SECTIONS = frozenset({'multiplayer','special_ops'})
SOURCES = frozenset({'cod4','mw3'})

def validate(entry):
    required = {'id','category','source','sections','properties'}
    if not isinstance(entry, dict) or not required <= entry.keys():
        raise ValueError('Definition missing required keys')
    if not isinstance(entry['id'],str) or not entry['id'].strip():
        raise ValueError('Invalid identifier')
    if entry['category'] not in CATEGORIES or entry['source'] not in SOURCES:
        raise ValueError('Invalid category/source')
    if not isinstance(entry['sections'],list) or not entry['sections'] or not set(entry['sections']) <= SECTIONS:
        raise ValueError('Invalid sections')
    if not isinstance(entry['properties'],dict):
        raise ValueError('Invalid properties')
    return entry

def resolve(entries, section, prefer='mw3'):
    if section not in SECTIONS or prefer not in SOURCES:
        raise ValueError('Invalid section/preference')
    selected = {}
    for item in entries:
        item = validate(item)
        if section not in item['sections']:
            continue
        key = (item['category'],item['id'])
        incumbent = selected.get(key)
        if incumbent is None or (incumbent['source'] != prefer and item['source'] == prefer):
            selected[key] = item
        elif incumbent['source'] == item['source']:
            raise ValueError('Duplicate definition for '+str(key))
    return {category: {key: value['properties'] | {'source': value['source']}
                       for (cat,key),value in selected.items() if cat == category}
            for category in sorted(CATEGORIES)}

def load(path):
    content=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(content,list):
        raise ValueError('Expected array of definitions')
    return [validate(entry) for entry in content]

if __name__ == '__main__':
    source=Path(__file__).resolve().parents[1]/'config/mw3/gameplay.sample.json'
    for mode in sorted(SECTIONS):
        data=resolve(load(source),mode)
        print(mode, {k:len(v) for k,v in data.items()})
