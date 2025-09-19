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
        
        # Comment blocks to ignore
        self.ignored_comment_blocks = [
            # PAM comment block
            [
                "# Set this to 'yes' to enable PAM authentication, account processing,",
                "# and session processing. If this is enabled, PAM authentication will",
                "# be allowed through the KbdInteractiveAuthentication and",
                "# PasswordAuthentication.  Depending on your PAM configuration,",
                "# PAM authentication via KbdInteractiveAuthentication may bypass",
                "# the setting of \"PermitRootLogin prohibit-password\".",
                "# If you just want the PAM account and session checks to run without",
                "# PAM authentication, then enable this but set PasswordAuthentication",
                "# and KbdInteractiveAuthentication to 'no'."
            ],
            # Keyboard-interactive authentication comment block
            [
                "# Change to \"yes\" to enable keyboard-interactive authentication.  Depending on",
                "# the system's configuration, this may involve passwords, challenge-response,",
                "# one-time passwords or some combination of these and other methods.",
                "# Beware issues with some PAM modules and threads."
            ],
            # SSH server system-wide configuration header
            [
                "#This is the sshd server system-wide configuration file.  See",
                "# sshd_config(5) for more information.",
                "",
                "# This sshd was compiled with PATH=/usr/local/bin:/usr/bin:/bin:/usr/games",
                "",
                "# The strategy used for options in the default sshd_config shipped with",
                "# OpenSSH is to specify options with their default value where",
                "# possible, but leave them commented.  Uncommented options override the",
                "# default value."
            ],
            # Section headers and explanatory comments
            ["# Ciphers and keying"],
            ["# Logging"],
            ["# Authentication:"],
            ["# Expect .ssh/authorized_keys2 to be disregarded by default in future."],
            ["# For this to work you will also need host keys in /etc/ssh/ssh_known_hosts"],
            ["# Change to yes if you don't trust ~/.ssh/known_hosts for", "# HostbasedAuthentication"],
            ["# Don't read the user's ~/.rhosts and ~/.shosts files"],
            ["# To disable tunneled clear text passwords, change to \"no\" here!"],
            ["# Kerberos options"],
            ["# GSSAPI options"],
            ["# no default banner path"],
            ["# Allow client to pass locale and color environment variables"],
            ["# override default of no subsystems"],
            ["# Example of overriding settings on a per-user basis"]
        ]
    
    def _is_ignored_comment_block(self, lines, start_index):
        """Check if the current position starts any of the ignored comment blocks"""
        for ignored_block in self.ignored_comment_blocks:
            if start_index + len(ignored_block) > len(lines):
                continue
                
            block_matches = True
            for i, expected_line in enumerate(ignored_block):
                if start_index + i >= len(lines):
                    block_matches = False
                    break
                actual_line = lines[start_index + i].strip()
                if actual_line != expected_line:
                    block_matches = False
                    break
            
            if block_matches:
                return len(ignored_block)  # Return the length of the matched block
        
        return 0  # No block matched

    def load(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'SSH server config not found: {self.path}')
        
        with open(self.path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.options = []
        self.includes = []
        self.comments = []
        self.all_lines = []
        
        i = 0
        while i < len(lines):
            raw_line = lines[i]
            line = raw_line.rstrip('\n')
            stripped = line.strip()
            line_num = i + 1
            
            # Check if this is the start of any ignored comment block
            block_length = self._is_ignored_comment_block(lines, i)
            if stripped.startswith('#') and block_length > 0:
                # Skip the entire ignored comment block
                i += block_length
                continue
            
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
                        i += 1
                        continue
                
                # Pure comment or empty line
                comment = SSHDOption(key='', value=None, raw=line, commented=True, line_number=line_num)
                self.comments.append(comment)
                self.all_lines.append(comment)
                i += 1
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
                i += 1
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
            
            i += 1

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