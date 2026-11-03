import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

with open(os.path.join(ROOT_DIR, 'app.py'), 'r', encoding='utf-8') as app_f:
    exec(app_f.read(), globals())
