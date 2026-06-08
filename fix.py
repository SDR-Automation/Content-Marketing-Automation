import pathlib
print('starting')
pathlib.Path('utils/__init__.py').write_text('# utils package\n', encoding='utf-8')
pathlib.Path('agents/__init__.py').write_text('# agents package\n', encoding='utf-8')
print('init files fixed')
