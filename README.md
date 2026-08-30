# LinuxCNC Ansible Playbook

## Human-generated foreword
Note: apart from this section, this entire readme is AI-generated.  This playbook is meant to provision a fresh installation of LinuxCNC 2.9.4 from the official ISO (Debian 12) to match my own personal preferences.  Yours will undoubtedly differ.  The intent is that immediately after completing the OS installation, the steps in the [Quick Start](#quick-start) section should fully configure the system.

Warnings:
- DO NOT do an ```apt upgrade``` prior to running this playbook.  It will break, and one of the things this playbook does is mitigate that.

Note: backups are restic to an NFS repo, not Timeshift/BackInTime to a local
partition.  The /backup partition on /dev/sda5, and the hard-coded UUID that
went with it, were removed on 2026-08-30 along with the tasks that used them.

## Summary
Comprehensive Ansible automation for setting up a complete LinuxCNC workstation with desktop environment, backup systems, remote access, virtual environment setup, and development tools.

## Overview

This playbook transforms a fresh Debian system into a fully configured LinuxCNC workstation with:
- Smart VNC remote access with conditional password handling
- restic backups of /home/evand and /etc to an NFS repository
- Desktop environment configuration (Cinnamon)
- Python virtual environment for LinuxCNC tools
- Adafruit IO integration for IoT connectivity
- udev rules for hardware integration
- System hardening and service management

## Features

- **🔐 Smart VNC Setup**: Conditional password prompting - only asks when needed
- **🔄 Disaster-Recovery Backups**: restic to an NFS repo, with a verified restore path
- **🖥️ Desktop Ready**: Cinnamon desktop with optimized settings for CNC work
- **🐍 Python Environment**: Isolated virtual environment for LinuxCNC Python dependencies
- **🌐 IoT Integration**: Adafruit IO setup with secure credential management
- **⚙️ Development Environment**: LinuxCNC configuration repository and tools
- **🔌 Hardware Integration**: udev rules for custom hardware (imach-p4s)
- **🛡️ System Hardening**: Kernel hold, service management, security configurations
- **🌐 Remote Access**: x11vnc with Avahi discovery for easy connection
- **🛠️ Initramfs Management**: Disables automatic updates to prevent system instability
- **⬆️ Package Management**: Automated apt updates and upgrades with proper sequencing

## Quick Start

### Install Ansible

On Debian/Ubuntu:
```bash
sudo apt update
sudo apt install ansible
```

On other systems, see the [official Ansible installation guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html).

### Run the Playbook

```bash
# Clone the repository
git clone git@github.com:Funkenjaeger/dcnc-ansible.git
cd dcnc-ansible

# Run the playbook
ansible-playbook -i inventory.ini playbook.yml --ask-become-pass
```

The playbook will prompt you for:
- Sudo password (if not using passwordless sudo)
- VNC password (only on first run)
- Ethernet interface for Mesa configuration (if needed)
- Adafruit IO username and key (only on first run)

## Requirements

- **Target System**: Debian GNU/Linux
- **Ansible**: 2.9+ on control machine
- **Privileges**: sudo access on target system
- **SSH Keys**: Configured for GitHub access (for LinuxCNC repo cloning)
- **Python**: Python 3 with venv module (usually included in Debian)

## Task Breakdown

### 🔐 VNC Password Management (Conditional)
1. **Check if x11vnc password file exists** - Tests for `/etc/x11vnc.pass`
2. **Prompt for VNC password if needed** - Secure password input (skipped if file exists)
3. **Confirm VNC password if needed** - Password verification (skipped if file exists)
4. **Verify VNC passwords match** - Validation check (skipped if file exists)
5. **Set VNC password variable** - Store for use in subsequent tasks (skipped if file exists)

### 🖥️ System Configuration
6. **linux-image-6.1.0-30-rt-amd64** - Hold RT kernel package to prevent updates
7. **linux-image-rt-amd64** - Hold RT kernel metapackage to prevent updates
8. **disable brltty service** - Stop/mask brltty (interferes with USB devices)
9. **disable brltty-udev service** - Stop/mask brltty-udev service

### 🛠️ System Hardening & Updates
10. **disable initramfs automatic updates** - Set `update_initramfs=no` to prevent boot issues
11. **update package lists and upgrade system** - Run `apt update && apt upgrade -y` safely

### 🌐 Network Configuration (Conditional)
12. **check if any interface has IP 10.10.10.11** - Detect existing Mesa network configuration
13. **get available ethernet interfaces** - List available network interfaces (if needed)
14. **prompt for ethernet interface selection** - Interactive interface selection (if needed)
15. **configure selected interface with Mesa IP** - Set up Mesa network connection (if needed)

### 📦 Package Installation
16. **install required packages** - Install: git, cinnamon, x11vnc

### 🖥️ Desktop Environment Setup
17. **set cinnamon as default session manager** - Configure lightdm for Cinnamon
18. **disable screensaver in cinnamon** - Turn off screen lock
19. **disable screensaver idle activation** - Prevent idle screen activation
20. **set screen to turn off after 1 hour** - Power management configuration

### 🌐 Remote Access (VNC)
21. **create x11vnc password file** - Generate encrypted password file (conditional)
22. **create x11vnc systemd service** - Install VNC server service with Avahi discovery
23. **enable and start x11vnc service** - Activate remote desktop access

### 🔄 Backup Systems Configuration
Timeshift and Back in Time were removed on 2026-08-30; restic replaced them.
See the restic block near the end of `playbook.yml`.

NOTE: the numbering in this walk-through is stale and has been since before
that change -- it claims 40 tasks against a real count that has never matched.
Read it as an outline of order, not as an index.

### 🔌 Hardware Integration
29. **copy udev rules for imach-p4s** - Install custom udev rules for hardware integration

### ⚙️ Development Environment
30. **clone Funkenjaeger/fj-lcnc-cfg repo** - Install LinuxCNC configuration to `~/linuxcnc`

### 🐍 Python Virtual Environment Setup (Conditional)
31. **check if virtual environment exists** - Test for existing virtual environment
32. **create directory for virtual environment** - Create `/usr/local/venv` (if needed)
33. **create python virtual environment** - Set up `linuxcnc_venv` (if needed)
34. **install adafruit-io requirements** - Install Python packages from requirements.txt (if needed)

### 🌐 Adafruit IO Integration (Conditional)
35. **check if ADAFRUIT_IO_USERNAME is set** - Test for existing username environment variable
36. **check if ADAFRUIT_IO_KEY is set** - Test for existing API key environment variable
37. **prompt for Adafruit IO username** - Interactive username input (if needed)
38. **prompt for Adafruit IO key** - Secure API key input (if needed)
39. **set ADAFRUIT_IO_USERNAME environment variable** - Add to `.bashrc` (if needed)
40. **set ADAFRUIT_IO_KEY environment variable** - Add to `.bashrc` (if needed)

## Configuration Details

### Python Virtual Environment
- **Location**: `/usr/local/venv/linuxcnc_venv`
- **Requirements**: Installed from `~/linuxcnc/configs/DCNC/requirements.txt`
- **Purpose**: Isolated environment for Adafruit IO and other Python dependencies
- **Ownership**: Current user owns the virtual environment directory

### Adafruit IO Integration
- **Credentials**: Stored as environment variables in `.bashrc`
- **Security**: API key input is hidden during entry
- **Persistence**: Environment variables persist across sessions
- **Conditional**: Only prompts if credentials don't already exist

### Hardware Integration
- **udev Rules**: Custom rules for imach-p4s hardware in `/etc/udev/rules.d/`
- **Automatic Reload**: udev rules are automatically reloaded when updated

### Backup Configuration
- **restic**: `/home/evand` and `/etc` to `/mnt/backups/cncpc-restic`, an NFS
  mount of 192.168.1.143:/volume1/backups
- **Schedule**: root cron, nightly backup at 01:00, prune Sundays at 04:00
- **Retention**: `--keep-daily 7 --keep-weekly 4 --keep-monthly 6`

### VNC Access
- **Port**: 5900 (default VNC port)
- **Security**: Password-protected with encrypted storage
- **Discovery**: Avahi/Zeroconf enabled for easy connection
- **Persistence**: Automatic restart on failure

### Desktop Environment
- **DE**: Cinnamon with screensaver disabled
- **Display**: 1-hour screen timeout for CNC work
- **Session**: Configured as default in lightdm

### System Hardening
- **Kernel Management**: RT kernel packages held to prevent breaking updates
- **Initramfs**: Automatic updates disabled to prevent boot issues
- **Services**: brltty services disabled (interfere with USB devices)
- **Updates**: Safe upgrade process after system hardening

## File Structure

```
dcnc-ansible/
├── README.md                 # This file
├── playbook.yml             # Main Ansible playbook
├── inventory.ini            # Inventory configuration
├── files/                   # Source files for copying
│   ├── 99-imach-p4s.rules  # udev rules for imach-p4s hardware
│   └── x11vnc.service      # x11vnc systemd service definition
└── .gitignore              # Git ignore rules
```

## Task Execution Summary

- **Total Tasks**: 40 tasks + 4 handlers
- **Conditional Tasks**: Many tasks skip when already configured (VNC, virtual environment, Adafruit IO, Mesa network)
- **Typical Execution**: ~25-30 active tasks on fresh systems, fewer on configured systems
- **Handlers**: lightdm restart, systemd reload, x11vnc restart, udev rules reload

## Key Features

✅ **Smart Conditional Logic** - Only prompts for input when needed  
✅ **Idempotent Operations** - Safe to run multiple times  
✅ **Comprehensive Automation** - Complete workstation setup from scratch  
✅ **Python Environment Management** - Isolated virtual environment for dependencies  
✅ **IoT Integration** - Secure Adafruit IO credential management  
✅ **Hardware Integration** - Custom udev rules for specialized hardware  
✅ **Backup Integration** - restic to an NFS repo, restore proven 2026-08-01  
✅ **Security-First Design** - Encrypted passwords, secure prompting, hidden API keys  
✅ **System Hardening** - Kernel holds, initramfs management, safe upgrades  
✅ **Production Ready** - Handles services, dependencies, and error conditions

## Hardware Requirements

- **Storage**: Network reachability to the NFS backup host (192.168.1.143)
- **Memory**: Minimum 4GB RAM recommended for desktop environment
- **Network**: Ethernet connection recommended for reliability
- **USB**: Support for imach-p4s hardware (if using custom udev rules)

## Troubleshooting

### Common Issues
- **VNC Connection**: Ensure port 5900 is open in firewall
- **Backup Failures**: Verify `/mnt/backups` is mounted and `/root/.restic-password` exists
- **Service Issues**: Check systemd service status with `systemctl status x11vnc`
- **Boot Issues**: If initramfs updates cause problems, they're now disabled by default
- **Python Environment**: Virtual environment issues can be resolved by deleting `/usr/local/venv/linuxcnc_venv` and re-running
- **Adafruit IO**: Check environment variables with `echo $ADAFRUIT_IO_USERNAME` and `echo $ADAFRUIT_IO_KEY`

### Debug Mode
Run with verbose output:
```bash
ansible-playbook -i inventory.ini playbook.yml --ask-become-pass -vvv
```

### Manual Virtual Environment Activation
To manually use the Python virtual environment:
```bash
source /usr/local/venv/linuxcnc_venv/bin/activate
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Feel free to use, modify, and distribute according to your needs.

## Related Projects

- [LinuxCNC](https://linuxcnc.org/) - Open source CNC control software
- [fj-lcnc-cfg](https://github.com/Funkenjaeger/fj-lcnc-cfg) - LinuxCNC configuration files
- [restic](https://restic.net/) - Backup program with deduplication and verified restores
- [Adafruit IO](https://io.adafruit.com/) - IoT platform for data logging and control
