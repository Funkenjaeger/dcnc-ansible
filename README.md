# LinuxCNC Ansible Playbook

## Human-generated foreword
Note: apart from this section, this entire readme is AI-generated.  This playbook is meant to provision a fresh installation of LinuxCNC 2.9.4 from the official ISO (Debian 12) to match my own personal preferences.  Yours will undoubtedly differ.  The intent is that immediately after completing the OS installation, the following steps should fully configure the system:
- ```sudo apt update && sudo apt install -y ansible git```
- ```cd ~ && git clone https://github.com/Funkenjaeger/dcnc-ansible.git && cd dcnc-ansible```
- ```ansible-playbook -i inventory.ini playbook.yml --ask-become-pass```

Warnings:
- This assumes there's a dedicated partition for backups with mount point /backup at /dev/sda5 that should be persisted through system reinstallations.
- DO NOT do an ```apt upgrade``` prior to running this playbook.  It will break, and one of the things this playbook does is mitigate that.

To Do:
- Currently the UUID of the backup partition is hard-coded in the playbook.  make it not.

## Summary
Comprehensive Ansible automation for setting up a complete LinuxCNC workstation with desktop environment, backup systems, remote access, and development tools.

## Overview

This 235-line playbook transforms a fresh Debian system into a fully configured LinuxCNC workstation with:
- Smart VNC remote access with conditional password handling
- Automated backup systems (Timeshift + Back in Time)
- Desktop environment configuration (Cinnamon)
- Development environment setup
- System hardening and service management

## Features

- **🔐 Smart VNC Setup**: Conditional password prompting - only asks when needed
- **🔄 Dual Backup Systems**: System snapshots (Timeshift) + user data backups (Back in Time)
- **🖥️ Desktop Ready**: Cinnamon desktop with optimized settings for CNC work
- **⚙️ Development Environment**: LinuxCNC configuration repository and tools
- **🛡️ System Hardening**: Kernel hold, service management, security configurations
- **🌐 Remote Access**: x11vnc with Avahi discovery for easy connection
- **📂 Config Restoration**: Automatically restores backup configurations from existing snapshots

## Quick Start

```bash
# Clone the repository
git clone git@github.com:Funkenjaeger/dcnc-ansible.git
cd dcnc-ansible

# Run the playbook
ansible-playbook -i inventory.ini playbook.yml --ask-become-pass
```

## Requirements

- **Target System**: Debian GNU/Linux
- **Ansible**: 2.9+ on control machine
- **Privileges**: sudo access on target system
- **SSH Keys**: Configured for GitHub access (for LinuxCNC repo cloning)

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

### 📦 Package Installation
10. **install required packages** - Install: git, pipx, timeshift, backintime-qt, cinnamon, x11vnc
11. **install adafruit-io with pipx** - Python package installation with dependencies

### 🖥️ Desktop Environment Setup
12. **set cinnamon as default session manager** - Configure lightdm for Cinnamon
13. **disable screensaver in cinnamon** - Turn off screen lock
14. **disable screensaver idle activation** - Prevent idle screen activation
15. **set screen to turn off after 1 hour** - Power management configuration

### 🌐 Remote Access (VNC)
16. **create x11vnc password file** - Generate encrypted password file (conditional)
17. **create x11vnc systemd service** - Install VNC server service with Avahi discovery
18. **enable and start x11vnc service** - Activate remote desktop access

### 🔄 Backup Systems Configuration
19. **configure timeshift backup device** - Set RSYNC mode with `/dev/sda5`
20. **create timeshift configuration file** - Full config: 6 monthly, 3 weekly, 3 daily snapshots
21. **ensure timeshift cron job is active** - Activate scheduled system snapshots

### 📂 Back in Time Restoration
22. **find latest backintime snapshot** - Locate most recent backup in `/backup/backintime/`
23. **restore backintime config from latest backup** - Restore user backup configuration

### ⚙️ Development Environment
24. **clone Funkenjaeger/fj-lcnc-cfg repo** - Install LinuxCNC configuration to `~/linuxcnc`

## Configuration Details

### Backup Configuration
- **Timeshift**: RSYNC mode, `/dev/sda5` storage, excludes `/home/evand/**`
- **Back in Time**: Automatically restores configuration from latest available snapshot
- **Retention**: 6 monthly, 3 weekly, 3 daily snapshots

### VNC Access
- **Port**: 5900 (default VNC port)
- **Security**: Password-protected with encrypted storage
- **Discovery**: Avahi/Zeroconf enabled for easy connection
- **Persistence**: Automatic restart on failure

### Desktop Environment
- **DE**: Cinnamon with screensaver disabled
- **Display**: 1-hour screen timeout for CNC work
- **Session**: Configured as default in lightdm

## File Structure

```
dcnc-ansible/
├── README.md           # This file
├── playbook.yml        # Main Ansible playbook (235 lines)
├── inventory.ini       # Inventory configuration
└── .gitignore         # Git ignore rules
```

## Task Execution Summary

- **Total Tasks**: 24 tasks + 3 handlers
- **Conditional Tasks**: 5 VNC-related tasks (skipped when password file exists)
- **Typical Execution**: ~19 active tasks on configured systems
- **Handlers**: lightdm restart, systemd reload, x11vnc restart

## Key Features

✅ **Smart Conditional Logic** - Only prompts for passwords when needed  
✅ **Idempotent Operations** - Safe to run multiple times  
✅ **Comprehensive Automation** - Complete workstation setup from scratch  
✅ **Backup Integration** - Both system (Timeshift) and user data (Back in Time)  
✅ **Security-First Design** - Encrypted passwords, secure prompting  
✅ **Production Ready** - Handles services, dependencies, and error conditions

## Hardware Requirements

- **Storage**: Dedicated backup partition (`/dev/sda5`) for Timeshift
- **Memory**: Minimum 4GB RAM recommended for desktop environment
- **Network**: Ethernet connection recommended for reliability

## Troubleshooting

### Common Issues
- **VNC Connection**: Ensure port 5900 is open in firewall
- **Backup Failures**: Verify `/dev/sda5` is mounted and writable
- **Service Issues**: Check systemd service status with `systemctl status x11vnc`

### Debug Mode
Run with verbose output:
```bash
ansible-playbook -i inventory.ini playbook.yml --ask-become-pass -vvv
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source under the MIT license.

## Related Projects

- [LinuxCNC](https://linuxcnc.org/) - Open source CNC control software
- [fj-lcnc-cfg](https://github.com/Funkenjaeger/fj-lcnc-cfg) - LinuxCNC configuration files
- [Timeshift](https://github.com/teejee2008/timeshift) - System backup utility
- [Back in Time](https://backintime.readthedocs.io/) - User data backup tool
