import ast, sys
source = sys.stdin.read()
try:
    ast.parse(source)
    with open('/mnt/d/LAAP/world_model.py', 'w', encoding='utf-8') as f:
        f.write(source)
    lines = source.count('\n')
    print(f'WORLD MODEL: {lines} lines, syntax OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR at line {e.lineno}: {e.msg}')
    slines = source.split('\n')
    if e.lineno and e.lineno <= len(slines):
        print(f'  Line: {slines[e.lineno-1]}')
