#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import runpy
script = os.path.join(os.path.dirname(__file__), 'src',
                      'palworld_save_tools', 'commands', 'auto_update.py')
runpy.run_path(script, run_name='__main__')
