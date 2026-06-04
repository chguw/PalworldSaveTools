import sys
import os
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
import runpy
script = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'palsav', 'palsav', 'commands', 'auto_update.py'))
runpy.run_path(script, run_name='__main__')