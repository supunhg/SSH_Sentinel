"""
Parser and serializer for OpenSSH server config (sshd_config) that preserves comments.
This handles the server configuration format which is different from client config.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import re
import os
import shutil

@dataclass
class SSHDOption:
    key: str
    value: Optional[str]
    raw: str
    commented: bool = False
    line_number: int = 0

@dataclass
class SSHDInclude:
    path: str
    raw: str
    line_number: int = 0

class SSHDConfig:
    def __init__(self, path=None):
        self.path = path or '/etc/ssh/sshd_config'
        self.options: List[SSHDOption] = []
        self.includes: List[SSHDInclude] = []
        self.comments: List[SSHDOption] = []  # pure comment lines
        self.all_lines: List[SSHDOption] = []  # all lines in order

    def load(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'SSH server config not found: {self.path}')
        
        with open(self.path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.options = []
        self.includes = []
        self.comments = []
        self.all_lines = []
        
        for line_num, raw_line in enumerate(lines, 1):
            line = raw_line.rstrip('\n')
            stripped = line.strip()
            
            # Empty line or pure comment
            if not stripped or stripped.startswith('#'):
                # Check if it's a commented option
                if stripped.startswith('#'):
                    uncommented = stripped.lstrip('#').strip()
                    # Try to parse as option
                    opt_match = re.match(r'^(\S+)(\s+(.*))?$', uncommented)
                    if opt_match and uncommented:
                        key = opt_match.group(1)
                        value = opt_match.group(3) if opt_match.group(3) else ''
                        option = SSHDOption(key=key, value=value, raw=line, commented=True, line_number=line_num)
                        self.all_lines.append(option)
                        continue
                
                # Pure comment or empty line
                comment = SSHDOption(key='', value=None, raw=line, commented=True, line_number=line_num)
                self.comments.append(comment)
                self.all_lines.append(comment)
                continue
            
            # Include directive
            include_match = re.match(r'^Include\s+(.+)$', stripped, re.IGNORECASE)
            if include_match:
                include_path = include_match.group(1)
                include = SSHDInclude(path=include_path, raw=line, line_number=line_num)
                self.includes.append(include)
                # Also add as option for editing
                option = SSHDOption(key='Include', value=include_path, raw=line, commented=False, line_number=line_num)
                self.options.append(option)
                self.all_lines.append(option)
                continue
            
            # Regular option
            opt_match = re.match(r'^(\S+)(\s+(.*))?$', stripped)
            if opt_match:
                key = opt_match.group(1)
                value = opt_match.group(3) if opt_match.group(3) else ''
                option = SSHDOption(key=key, value=value, raw=line, commented=False, line_number=line_num)
                self.options.append(option)
                self.all_lines.append(option)
            else:
                # Unrecognized line, treat as comment
                comment = SSHDOption(key='', value=None, raw=line, commented=True, line_number=line_num)
                self.comments.append(comment)
                self.all_lines.append(comment)

    def to_text(self) -> str:
        parts = []
        for option in self.all_lines:
            if option.commented and option.key:
                # Ensure it starts with #
                if not option.raw.strip().startswith('#'):
                    parts.append(f'#{option.raw}')
                else:
                    parts.append(option.raw)
            else:
                parts.append(option.raw)
        return '\n'.join(parts) + '\n'

    def write_backup(self, bak_path=None):
        bak = bak_path or self.path + '.bak'
        shutil.copy2(self.path, bak)
        return bak

    def restore_backup(self, bak_path=None):
        bak = bak_path or self.path + '.bak'
        if not os.path.exists(bak):
            raise FileNotFoundError('Backup not found')
        shutil.copy2(bak, self.path)

    def get_options_by_key(self, key: str) -> List[SSHDOption]:
        """Get all options with a specific key (case-insensitive)"""
        return [opt for opt in self.all_lines if opt.key.lower() == key.lower()]

    def add_option(self, key: str, value: str, commented: bool = False):
        """Add a new option"""
        raw = f'{key} {value}' if value else key
        if commented:
            raw = f'#{raw}'
        option = SSHDOption(key=key, value=value, raw=raw, commented=commented, line_number=len(self.all_lines) + 1)
        self.all_lines.append(option)
        if not commented:
            self.options.append(option)
        return option