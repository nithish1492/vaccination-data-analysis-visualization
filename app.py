import importlib.util
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_FILE = os.path.join(BASE_DIR, "app", "main.py")

spec = importlib.util.spec_from_file_location("immunoscope_main", MAIN_FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

app = module.app