import os
import sys
import shutil
from pathlib import Path

def require_root_or_exit():
    # On Windows, skip the euid check but warn
    if os.name == 'nt':
        return
    try:
        if os.geteuid() != 0:
            print('This application requires root privileges. Exiting.')
            sys.exit(1)
    except AttributeError:
        # Platform doesn't support geteuid
        return

def ensure_backup_exists(config_path):
    bak = config_path + '.bak'
    if not os.path.exists(bak):
        shutil.copy2(config_path, bak)
    return bak