
"""
Entry point. Requires root, launches SSH server config GUI.
"""
import sys
import utils
from PyQt6.QtWidgets import QApplication
from sshd_gui import SSHDMainWindow

def main():
    utils.require_root_or_exit()
    
    config_path = '/etc/ssh/sshd_config'
    
    app = QApplication(sys.argv)
    win = SSHDMainWindow(config_path=config_path)
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()