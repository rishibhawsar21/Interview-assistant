# debug_test.py
import sys
sys.path.insert(0, ".")
from src.llm_client import debug_run_verbose
import pprint

res = debug_run_verbose("Hello! Please respond briefly.", 128)
pprint.pprint(res)
