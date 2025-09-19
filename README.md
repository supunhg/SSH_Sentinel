# SSH Sentinel - SSH Server Configuration Editor

A specialized GUI tool for editing SSH server configuration (`/etc/ssh/sshd_config`) built with Python and PyQt6. SSH Sentinel provides an intuitive interface for managing SSH server daemon settings with safety features like automatic backups and configuration validation.

## Features

### SSH Server Configuration Management
- **Complete sshd_config editing**: Edit SSH server daemon configuration with a user-friendly GUI
- **Root access protection**: Automatically requires root privileges for system configuration files
- **Option management**: Add, edit, remove, and comment/uncomment configuration options
- **Interactive explanations**: Built-in descriptions for common SSH server options
- **Real-time validation**: Immediate feedback on configuration changes

### Safety & Backup Features
- **Automatic backups**: Always creates `.bak` files before any changes
- **Restore functionality**: Easy restoration from backup files
- **Auto-refresh**: Configuration automatically reloads after successful saves
- **Save options**: Save directly to config file or save to backup for testing
- **Data integrity**: Preserves comments and formatting in configuration files

## Requirements

- **Python**: 3.8 or higher
- **PyQt6**: For the graphical user interface
- **Root access**: Required for editing SSH server configuration (`/etc/ssh/sshd_config`)

## Installation

1. Clone or download the project
2. Set up a Python virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Launch the SSH server configuration editor:
```bash
sudo python3 main.py
```

**Note**: Root privileges are required because the tool edits the system SSH server configuration file at `/etc/ssh/sshd_config`.

## Interface Overview

- **Left Panel**: Lists all configuration options and comments from sshd_config
- **Right Panel**: Edit form for the selected configuration option
- **Control Buttons**: 
  - Create/restore backups
  - Add new configuration options
  - Save changes (with automatic backup)

## Safety Features

- **Mandatory Backups**: Every save operation automatically creates a backup file
- **Auto-refresh**: Configuration reloads automatically after saves to show current state
- **Preserve Comments**: Maintains all comments and formatting from original config
- **Root Protection**: Prevents accidental execution without proper privileges

## Important Notes

- **Service Restart Required**: After making changes, restart the SSH service to apply them:
  ```bash
  sudo systemctl restart ssh
  ```
- **Backup Files**: Backups are saved as `/etc/ssh/sshd_config.bak`
- **Safety First**: Always test changes in a non-production environment first
- **Remote Access**: Be careful when modifying SSH settings on remote servers

## File Structure

- `main.py` - Entry point for SSH server configuration editor
- `sshd_gui.py` - GUI for SSH server config editing
- `sshd_parser.py` - Parser for sshd_config format
- `utils.py` - Utility functions (root checking, backups)

## Contributing

This tool is designed to make SSH server configuration management safer and more accessible. Contributions for additional features, bug fixes, or documentation improvements are welcome.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Supun Hewagamage** - [@supunhg](https://github.com/supunhg)

## Copyright

Copyright (c) 2025 Supun Hewagamage