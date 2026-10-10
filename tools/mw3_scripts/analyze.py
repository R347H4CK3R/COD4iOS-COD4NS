#!/usr/bin/env python3
"""Static GSC dependency inventory. Never establishes runtime compatibility.
Inputs remain local; output contains symbol names/locations, not source bodies.
"""
import argparse
import collections
import json
import re
from pathlib import Path

TOKEN = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|[A-Za-z_][\w]*(?:\\[A-Za-z_][\w]*)*|::|[^\s]')
CONTROL = {'if', 'while', 'for', 'foreach', 'switch', 'return', 'wait', 'waittill', 'waittillmatch', 'endon', 'notify'}

def parse_script(text):
    tokens = [m.group() for m in TOKEN.finditer(text) if not m.group().startswith(('//', '/*'))]
    definitions, calls, references, tables = set(), [], [], set()
    includes = [tokens[i+2] for i in range(len(tokens)-2) if tokens[i]=='#' and tokens[i+1]=='include' and re.fullmatch(r'[\w\\/]+', tokens[i+2])]
    for i, token in enumerate(tokens):
        if token.startswith('"'):
            if token.lower().endswith('.csv"'): tables.add(token[1:-1])
            continue
        if not re.fullmatch(r'[A-Za-z_]\w*', token): continue
        if i >= 2 and tokens[i-1] == '::':
            qualifier=tokens[i-2]
            if re.fullmatch(r'[A-Za-z_][\w]*(?:\\[A-Za-z_][\w]*)*', qualifier) and qualifier not in {'thread', 'self', 'return'}:
                namespace = qualifier.replace('\\', '/').lower()
                references.append((namespace, token.lower()))
            continue
        if i+1 >= len(tokens) or tokens[i+1] != '(': continue
        depth, j = 1, i+2
        while j < len(tokens) and depth:
            depth += (tokens[j] == '(') - (tokens[j] == ')'); j += 1
        if depth == 0 and j < len(tokens) and tokens[j] == '{' and token.lower() not in CONTROL:
            definitions.add(token.lower())
        elif token.lower() not in CONTROL:
            calls.append(token.lower())
    return {'definitions': sorted(definitions), 'calls': sorted(set(calls)),
            'references': sorted(set(references)), 'tables': sorted(tables), 'includes': sorted({value.replace('\\', '/').lower() for value in includes})}

def single_player_source(text):
    """Filter only known SP/MP conditions. Unknown conditions retain both branches."""
    stack, output = [], []
    active = True
    for line in text.splitlines():
        directive = re.match(r'\s*#\s*(ifdef|ifndef|if|elif|else|endif)\b(.*)', line)
        if directive:
            op, condition = directive[1], directive[2].strip()
            if op in ('ifdef', 'ifndef', 'if'):
                value = {'KISAK_SP': True, 'KISAK_MP': False}.get(condition)
                if op == 'ifndef' and value is not None: value = not value
                stack.append((active, value))
                active = active and value is not False
            elif op in ('else', 'elif') and stack:
                parent, value = stack[-1]
                active = parent and value is not True
            elif op == 'endif' and stack:
                active, _ = stack.pop()
            continue
        if active: output.append(line)
    return '\n'.join(output)

def builtin_registry(root):
    result = {'functions': {}, 'methods': {}}
    for path in sorted(root.rglob('*.cpp')):
        text = single_player_source(path.read_text(encoding='utf-8', errors='replace'))
        for array in re.finditer(r'(?:const\s+|static\s+)*Builtin(Function|Method)Def\s+\w+\s*\[[^\]]*\]\s*=\s*\{([\s\S]*?)\n\s*\};', text):
            kind = 'functions' if array[1] == 'Function' else 'methods'
            for name, handler in re.findall(r'\{\s*"([^"]+)"\s*,\s*([^,]+),', array[2]):
                result[kind].setdefault(name.lower(), []).append({'file': str(path.relative_to(root)), 'handler': handler.strip()})
    return result

def analyze(roots, engine, aliases=None, entries=None):
    if not engine.is_dir() or any(not root.is_dir() for root in roots): raise ValueError("All input roots must exist")
    scripts = {}
    namespaces = {}
    for n, root in enumerate(roots):
        for path in sorted(root.rglob('*.gsc')):
            relative = path.relative_to(root).as_posix()
            key = f'{n}:{relative}'
            scripts[key] = parse_script(path.read_text(encoding='utf-8', errors='replace'))
            namespaces.setdefault(relative[:-4].lower(), []).append(key)
    for namespace, filename in (aliases or {}).items():
        matches = [key for key in scripts if key.split(':', 1)[1] == filename]
        if len(matches) != 1: raise ValueError(f'Alias {namespace} must select one file; got {matches}')
        namespaces[namespace.lower()] = matches
    builtins = builtin_registry(engine)
    registered = set(builtins['functions']) | set(builtins['methods'])
    unresolved = collections.defaultdict(set)
    missing_exports, candidate_namespaces = [], {}
    for key, script in scripts.items():
        script['registered_calls'] = sorted(set(script['calls']) & registered)
        script['unclassified_calls'] = sorted(set(script['calls']) - registered - set(script['definitions']))
        for call in script['unclassified_calls']: unresolved[call].add(key)
        for namespace, function in script['references']:
            targets = namespaces.get(namespace, [])
            if not targets:
                candidate_namespaces.setdefault(namespace, set()).add(function)
            elif not any(function in scripts[target]['definitions'] for target in targets):
                missing_exports.append({'caller': key, 'namespace': namespace, 'function': function})
    candidates = {}
    for namespace, functions in sorted(candidate_namespaces.items()):
        ranked = sorted(((len(functions & set(script['definitions'])), key) for key, script in scripts.items()), reverse=True)
        candidates[namespace] = {'referenced_functions': sorted(functions), 'unverified_candidates': [{'file': key, 'matching_exports': count} for count, key in ranked[:3] if count]}
    dependency_graph = {}
    for key, script in scripts.items():
        dependency_graph[key] = sorted(set(script['includes']) | {namespace for namespace, _ in script['references']})
    entry_closures = {}
    for entry in entries or []:
        pending=list(namespaces.get(entry.lower(), [])); visited=set(); absent=set()
        while pending:
            key=pending.pop()
            if key in visited: continue
            visited.add(key)
            for dependency in dependency_graph[key]:
                if dependency in namespaces: pending.extend(namespaces[dependency])
                else: absent.add(dependency)
        entry_closures[entry] = {'entry_found': entry.lower() in namespaces, 'resolved_scripts': sorted(visited), 'unresolved_dependencies': sorted(absent)}
    return {'limitations': ['Known KISAK_SP/KISAK_MP branches are filtered; other preprocessing conditions are conservatively retained. Array discovery does not prove runtime resolver reachability.', 'Static inventory only: registered names do not prove matching IW5 semantics, call signatures, or execution.', 'Unclassified calls may be VM syntax, unresolved script helpers, dynamic calls, or absent builtins.', 'Numeric namespace candidates are heuristic and never treated as resolved.', 'Asset availability, map entities, bytecode/compiler compatibility, event timing and co-op behavior require separate validation.'],
            'summary': {'scripts': len(scripts), 'registered_functions': len(builtins['functions']), 'registered_methods': len(builtins['methods']), 'unclassified_call_names': len(unresolved), 'unresolved_namespaces': len(candidates), 'missing_exports': len(missing_exports)},
            'aliases': aliases or {}, 'resolved_namespaces': namespaces, 'entry_closures': entry_closures, 'dependency_graph': dependency_graph, 'builtins': builtins, 'scripts': scripts,
            'unclassified_calls': {name: sorted(files) for name, files in sorted(unresolved.items())},
            'unresolved_namespaces': candidates, 'missing_exports': missing_exports}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scripts', type=Path, action='append', required=True)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--alias', action='append', default=[], metavar='NAMESPACE=RELATIVE.gsc')
    parser.add_argument('--entry', action='append', default=[], help='Namespace for conservative script-level dependency closure')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.scripts, args.engine, dict(value.split('=', 1) for value in args.alias), args.entry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report['summary']))

if __name__ == '__main__': main()
