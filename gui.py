"""
PyQt6 GUI implementation. This file builds the main window with a sidebar listing Host blocks
and a form editor for the selected Host. It offers Backup, Restore, and Save buttons.
"""
from PyQt6.QtWidgets import (QWidget, QMainWindow, QListWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QMessageBox,
                             QListWidgetItem, QFormLayout, QCheckBox, QScrollArea)
from ssh_parser import SSHConfig, ConfigOption
import json
import utils

class HostListItem(QListWidgetItem):
    def __init__(self, title, block_index):
        super().__init__(title)
        self.block_index = block_index

class MainWindow(QMainWindow):
    def __init__(self, config_path=None):
        super().__init__()
        self.setWindowTitle('SSH Sentinel - SSH Configurator')
        self.resize(1000, 600)
        self.config_path = config_path
        self.ssh = SSHConfig(path=config_path)
        self.ssh.load()
        utils.ensure_backup_exists(self.ssh.path)

        try:
            with open('explanations.json', 'r', encoding='utf-8') as f:
                self.expl = json.load(f)
        except Exception:
            self.expl = {}

        container = QWidget()
        self.setCentralWidget(container)
        layout = QHBoxLayout()
        container.setLayout(layout)

        left = QVBoxLayout()
        self.list_widget = QListWidget()
        self.reload_host_list()
        left.addWidget(self.list_widget)
        btn_layout = QHBoxLayout()
        self.btn_backup = QPushButton('Backup (.bak)')
        self.btn_restore = QPushButton('Restore (.bak)')
        self.btn_add = QPushButton('Add Host')
        btn_layout.addWidget(self.btn_backup)
        btn_layout.addWidget(self.btn_restore)
        btn_layout.addWidget(self.btn_add)
        left.addLayout(btn_layout)

        layout.addLayout(left, 2)

        right = QVBoxLayout()
        self.form_area = QScrollArea()
        self.form_widget = QWidget()
        self.form_layout = QFormLayout()
        self.form_widget.setLayout(self.form_layout)
        self.form_area.setWidget(self.form_widget)
        self.form_area.setWidgetResizable(True)
        right.addWidget(self.form_area)

        save_layout = QHBoxLayout()
        self.btn_save = QPushButton('Save (overwrite)')
        self.btn_save_bak = QPushButton('Save As .bak')
        self.btn_restore_from_bak = QPushButton('Restore now')
        save_layout.addWidget(self.btn_save_bak)
        save_layout.addWidget(self.btn_restore_from_bak)
        save_layout.addWidget(self.btn_save)
        right.addLayout(save_layout)

        layout.addLayout(right, 5)

        self.list_widget.currentItemChanged.connect(self.on_select_host)
        self.btn_backup.clicked.connect(self.on_backup)
        self.btn_restore.clicked.connect(self.on_restore)
        self.btn_add.clicked.connect(self.on_add_host)
        self.btn_save.clicked.connect(self.on_save)
        self.btn_save_bak.clicked.connect(self.on_save_as_bak)
        self.btn_restore_from_bak.clicked.connect(self.on_restore_now)

        self.current_widgets = []

    def reload_host_list(self):
        self.list_widget.clear()
        for i, block in enumerate(self.ssh.blocks):
            name = block.header.raw
            item = HostListItem(name, i)
            self.list_widget.addItem(item)

    def clear_form(self):
        for w in self.current_widgets:
            w.setParent(None)
        self.current_widgets = []
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)

    def on_select_host(self, current, previous=None):
        if current is None:
            return
        idx = current.block_index
        block = self.ssh.blocks[idx]
        self.clear_form()
        header_lbl = QLabel('Host (pattern)')
        header_edit = QLineEdit(block.header.raw.replace('\n',''))
        self.form_layout.addRow(header_lbl, header_edit)
        self.current_widgets.extend([header_lbl, header_edit])

        for opt in block.options:
            row_label = QLabel(opt.key if opt.key else '<comment>')
            expl = self.expl.get(opt.key, '')
            if expl:
                row_label.setToolTip(expl)
            val_edit = QLineEdit(opt.value if opt.value is not None else '')
            comment_chk = QCheckBox('Commented')
            comment_chk.setChecked(opt.commented)
            self.form_layout.addRow(row_label, val_edit)
            self.form_layout.addRow(QLabel(''), comment_chk)
            self.current_widgets.extend([row_label, val_edit, comment_chk])

        add_opt_btn = QPushButton('Add Option')
        add_opt_btn.clicked.connect(lambda _, i=idx: self.add_option(i))
        self.form_layout.addRow(add_opt_btn)
        self.current_widgets.append(add_opt_btn)

        block._editor_refs = {
            'header': header_edit,
            'option_rows': []
        }
        row = 1
        idx_widget = 0
        for opt in block.options:
            pass
        refs = []
        cw = self.current_widgets[2:]  
        i = 0
        while i < len(cw):
            lbl = cw[i]
            if isinstance(lbl, QLabel) and lbl.text() == '':
                i += 1
                continue
            if i+1 < len(cw):
                val = cw[i+1]
            else:
                val = None
            chk = cw[i+2] if (i+2 < len(cw) and isinstance(cw[i+2], QCheckBox)) else None
            refs.append((lbl, val, chk))
            i += 3
        block._editor_refs['option_rows'] = refs

    def add_option(self, block_index):
        block = self.ssh.blocks[block_index]
        opt = ConfigOption(key='NewOption', value='', raw='NewOption ', commented=False)
        block.options.append(opt)
        self.reload_host_list()
        self.list_widget.setCurrentRow(block_index)

    def on_add_host(self):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, 'Add Host', 'Enter host pattern:')
        if ok and text.strip():
            self.ssh.add_host(text.strip())
            self.reload_host_list()

    def on_backup(self):
        try:
            bak = self.ssh.write_backup()
            QMessageBox.information(self, 'Backup', f'Backup created at {bak}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def on_restore(self):
        try:
            self.ssh.restore_backup()
            QMessageBox.information(self, 'Restore', 'Restored from .bak')
            self.ssh.load()
            self.reload_host_list()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def on_restore_now(self):
        self.on_restore()

    def on_save_as_bak(self):
        try:
            text = self.collect_and_serialize()
            bakpath = self.ssh.path + '.bak'
            with open(bakpath, 'w', encoding='utf-8') as f:
                f.write(text)
            QMessageBox.information(self, 'Saved', f'Saved to {bakpath}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def on_save(self):
        try:
            text = self.collect_and_serialize()
            self.ssh.write_backup()
            with open(self.ssh.path, 'w', encoding='utf-8') as f:
                f.write(text)
            QMessageBox.information(self, 'Saved', 'Configuration saved and backup created')
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def collect_and_serialize(self) -> str:
        for i, block in enumerate(self.ssh.blocks):
            if not hasattr(block, '_editor_refs'):
                continue
            hdr = block._editor_refs['header'].text().strip()
            block.header.raw = hdr
            new_opts = []
            for (lbl, val_widget, chk) in block._editor_refs['option_rows']:
                key = lbl.text()
                value = val_widget.text() if val_widget else ''
                commented = chk.isChecked() if chk else False
                raw = f'{key} {value}'.strip()
                new_opts.append(ConfigOption(key=key, value=value, raw=raw, commented=commented))
            block.options = new_opts
        return self.ssh.to_text()