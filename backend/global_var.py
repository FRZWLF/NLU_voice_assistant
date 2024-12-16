# global_var.py
from multiprocessing import Manager

# Shared Manager Dictionary für globale Variablen
manager = Manager()
global_state = manager.dict()
global_state['assistant'] = None  # Initial leer
