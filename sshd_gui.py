"""
PyQt6 GUI implementation for SSH server configuration (sshd_config) editor.
"""
import sys
from PyQt6.QtWidgets import (QWidget, QMainWindow, QListWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox,
                             QListWidgetItem, QFormLayout, QCheckBox, QScrollArea, QTextEdit,
                             QInputDialog)
from PyQt6.QtCore import Qt
from sshd_parser import SSHDConfig, SSHDOption
import json
import utils

class SSHDOptionItem(QListWidgetItem):
    def __init__(self, option: SSHDOption, index: int):
        title = f"{option.key}: {option.value}" if option.key and option.value else option.key or "<comment>"
        if option.commented:
            title = f"# {title}"
        super().__init__(title)
        self.option = option
        self.index = index

class SSHDMainWindow(QMainWindow):
    def __init__(self, config_path=None):
        super().__init__()
        self.setWindowTitle('SSH Sentinel - SSH Server Configurator (sshd_config)')
        self.resize(1200, 700)
        self.config_path = config_path
        self.sshd = SSHDConfig(path=config_path)
        
        try:
            self.sshd.load()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load SSH server config: {str(e)}')
            sys.exit(1)
        
        # ensure bak exists
        utils.ensure_backup_exists(self.sshd.path)

        # load explanations for SSH server options
        try:
            with open('sshd_explanations.json', 'r', encoding='utf-8') as f:
                self.expl = json.load(f)
        except Exception:
            # Default explanations for common sshd_config options
            self.expl = {
                'Port': 'Port number that sshd listens on. Default is 22.',
                'ListenAddress': 'IP address(es) that sshd should listen on.',
                'HostKey': 'Private key files used by sshd for host authentication.',
                'PermitRootLogin': 'Whether root can log in using ssh. Values: yes, no, prohibit-password, forced-commands-only.',
                'PasswordAuthentication': 'Whether password authentication is allowed.',
                'PubkeyAuthentication': 'Whether public key authentication is allowed.',
                'AuthorizedKeysFile': 'File containing public keys for public key authentication.',
                'PermitEmptyPasswords': 'Whether server allows login to accounts with empty password strings.',
                'ChallengeResponseAuthentication': 'Whether challenge-response authentication is allowed.',
                'UsePAM': 'Whether Pluggable Authentication Modules interface is enabled.',
                'X11Forwarding': 'Whether X11 forwarding is permitted.',
                'PrintMotd': 'Whether sshd should print /etc/motd when a user logs in interactively.',
                'AcceptEnv': 'Environment variables that may be sent by the client.',
                'Subsystem': 'Configure an external subsystem (e.g. file transfer daemon).',
                'Include': 'Include the specified configuration file(s).'
            }

        self.setup_ui()
        self.reload_options_list()

    def setup_ui(self):
        container = QWidget()
        self.setCentralWidget(container)
        layout = QHBoxLayout()
        container.setLayout(layout)

        # Left panel: options list and controls
        left = QVBoxLayout()
        
        # File info
        info_label = QLabel(f"Editing: {self.sshd.path}")
        info_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        left.addWidget(info_label)
        
        # Options list
        self.list_widget = QListWidget()
        left.addWidget(self.list_widget)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        self.btn_backup = QPushButton('Create Backup')
        self.btn_restore = QPushButton('Restore from Backup')
        self.btn_add = QPushButton('Add Option')
        btn_layout.addWidget(self.btn_backup)
        btn_layout.addWidget(self.btn_restore)
        btn_layout.addWidget(self.btn_add)
        left.addLayout(btn_layout)

        layout.addLayout(left, 2)

        # Right panel: editor
        right = QVBoxLayout()
        
        # Editor area
        self.form_area = QScrollArea()
        self.form_widget = QWidget()
        self.form_layout = QFormLayout()
        self.form_widget.setLayout(self.form_layout)
        self.form_area.setWidget(self.form_widget)
        self.form_area.setWidgetResizable(True)
        right.addWidget(self.form_area)

        # Save buttons
        save_layout = QHBoxLayout()
        self.btn_save_bak = QPushButton('Save as Backup')
        self.btn_save = QPushButton('Save & Apply')
        save_layout.addWidget(self.btn_save_bak)
        save_layout.addWidget(self.btn_save)
        right.addLayout(save_layout)

        layout.addLayout(right, 3)

        # Connect signals
        self.list_widget.currentItemChanged.connect(self.on_select_option)
        self.btn_backup.clicked.connect(self.on_backup)
        self.btn_restore.clicked.connect(self.on_restore)
        self.btn_add.clicked.connect(self.on_add_option)
        self.btn_save.clicked.connect(self.on_save)
        self.btn_save_bak.clicked.connect(self.on_save_as_bak)

        # Current editor widgets
        self.current_widgets = []

    def reload_options_list(self):
        self.list_widget.clear()
        for i, option in enumerate(self.sshd.all_lines):
            item = SSHDOptionItem(option, i)
            self.list_widget.addItem(item)

    def clear_form(self):
        for w in self.current_widgets:
            w.setParent(None)
        self.current_widgets = []
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)

    def on_select_option(self, current, previous=None):
        if current is None:
            return
        
        option = current.option
        self.clear_form()
        
        # Option key
        key_label = QLabel('Option:')
        key_edit = QLineEdit(option.key)
        self.form_layout.addRow(key_label, key_edit)
        
        # Option value
        value_label = QLabel('Value:')
        value_edit = QLineEdit(option.value if option.value else '')
        self.form_layout.addRow(value_label, value_edit)
        
        # Commented checkbox
        comment_chk = QCheckBox('Commented out (disabled)')
        comment_chk.setChecked(option.commented)
        self.form_layout.addRow(QLabel(''), comment_chk)
        
        # Explanation
        if option.key in self.expl:
            expl_label = QLabel('Description:')
            expl_text = QTextEdit()
            expl_text.setPlainText(self.expl[option.key])
            expl_text.setMaximumHeight(80)
            expl_text.setReadOnly(True)
            self.form_layout.addRow(expl_label, expl_text)
            self.current_widgets.extend([expl_label, expl_text])
        
        # Delete button
        delete_btn = QPushButton('Delete This Option')
        delete_btn.setStyleSheet("background-color: #cc0000; color: white;")
        delete_btn.clicked.connect(lambda: self.delete_option(current.index))
        self.form_layout.addRow(delete_btn)
        
        self.current_widgets.extend([key_label, key_edit, value_label, value_edit, comment_chk, delete_btn])
        
        # Store references for saving
        current.editor_refs = {
            'key': key_edit,
            'value': value_edit,
            'commented': comment_chk
        }

    def delete_option(self, index):
        reply = QMessageBox.question(self, 'Delete Option', 
                                   'Are you sure you want to delete this option?',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.sshd.all_lines[index]
            self.reload_options_list()
            self.clear_form()

    def on_add_option(self):
        key, ok = QInputDialog.getText(self, 'Add Option', 'Enter option name:')
        if ok and key.strip():
            value, ok2 = QInputDialog.getText(self, 'Add Option', 'Enter option value (optional):')
            if ok2:
                self.sshd.add_option(key.strip(), value.strip())
                self.reload_options_list()

    def on_backup(self):
        try:
            bak = self.sshd.write_backup()
            QMessageBox.information(self, 'Backup', f'Backup created at {bak}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def on_restore(self):
        try:
            self.sshd.restore_backup()
            QMessageBox.information(self, 'Restore', 'Restored from backup')
            self.refresh_configuration()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def on_save_as_bak(self):
        try:
            text = self.collect_and_serialize()
            bakpath = self.sshd.path + '.bak'
            with open(bakpath, 'w', encoding='utf-8') as f:
                f.write(text)
            QMessageBox.information(self, 'Saved', f'Saved to {bakpath}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def refresh_configuration(self):
        """Reload the configuration from disk and refresh the UI"""
        try:
            # Reload the configuration from file
            self.sshd.load()
            # Refresh the options list
            self.reload_options_list()
            # Clear the current form
            self.clear_form()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to refresh configuration: {str(e)}')

    def on_save(self):
        try:
            # Create backup first
            self.sshd.write_backup()
            
            # Save changes
            text = self.collect_and_serialize()
            with open(self.sshd.path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Refresh the configuration after successful save
            self.refresh_configuration()
            
            QMessageBox.information(self, 'Saved', 
                                  'Configuration saved and backup created.\n\n'
                                  'To apply changes, restart SSH service:\n'
                                  'sudo systemctl restart ssh')
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def collect_and_serialize(self) -> str:
        # Update options from editor widgets
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if hasattr(item, 'editor_refs'):
                option = item.option
                refs = item.editor_refs
                
                new_key = refs['key'].text().strip()
                new_value = refs['value'].text().strip()
                new_commented = refs['commented'].isChecked()
                
                option.key = new_key
                option.value = new_value
                option.commented = new_commented
                
                # Update raw representation
                if new_key:
                    raw = f'{new_key} {new_value}' if new_value else new_key
                    if new_commented:
                        raw = f'#{raw}'
                    option.raw = raw
        
        return self.sshd.to_text()