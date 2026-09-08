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

### Running unattended (CI, a script, or any run without a terminal)

**`ansible.builtin.pause` is a two-sided trap, and both sides bite.**

| how you run it | what `pause` does |
|---|---|
| no tty (stdin not interactive) | **does not block.** Warns `Not waiting for response to prompt as stdin is not interactive`, returns `ok`, and leaves `user_input` **empty** |
| any tty present (including one driven by `expect`) | **blocks forever.** It will sit there indefinitely and outlive whatever was driving it |

The first side is why the credential tasks have explicit guards: without them an
unattended run wrote `export ADAFRUIT_IO_USERNAME=""` and a 1-byte restic
password file, and because the consumers fail *soft*, the only symptom was an
air compressor that never connected and backups that could not authenticate.
Worse, the restic case was **sticky** -- the "does the file exist" check saw the
1-byte file and skipped the fix on every subsequent run.

The second side is not hypothetical either: a stray `ansible-playbook` driving a
`pause` through a pty sat hung on the dry-run VM for **two days** before anyone
noticed it.

**So: do not try to drive the prompts. Supply the values instead.** Extra-vars
are Ansible's highest-precedence source, so they shadow the registered `pause`
result and need no tty at all:

```bash
ansible-playbook -i inventory.ini playbook.yml \
  -e '{"adafruit_username_input":{"user_input":"YOUR_USERNAME"}}' \
  -e '{"adafruit_key_input":{"user_input":"YOUR_KEY"}}' \
  -e '{"restic_password_input":{"user_input":"THE_EXISTING_REPO_PASSWORD"}}' \
  < /dev/null
```

Pass only the ones you need -- each block is skipped entirely when usable
credentials are already present on the machine, so a second run needs none of
them.

**The guards are not bypassed by this.** Verified 2026-09-01 on the dry-run VM:
an extra-var carrying an **empty** value still fails at
`verify Adafruit IO credentials were actually captured` and writes nothing.
Extra-vars are a way around the *prompt*, never around the *check*.

**Do not put a real key in shell history or a CI log.** Read it from a file or
an environment variable at the point of use.

**Known gap:** `ansible-playbook` exits **0** when the inventory matches no
hosts -- a run with a mistyped `-i` prints an empty `PLAY RECAP`, does nothing,
and looks green. Check the recap names a host before believing a clean run.

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
11. **refresh the apt cache** - `apt-get update` once, tolerantly; every later apt task uses `update_cache: no`
12. **work out which repos failed to refresh** - Parse `Err:` lines out of the output
13. **split those into load-bearing and incidental** - Against `cncpc_apt_required_hosts`
14. **fail when a repo this playbook installs from could not be refreshed** - Fatal, and named
15. **fail when apt-get update broke in a way this cannot attribute** - Nonzero exit, no `Err:` line
16. **report third-party repos that could not be refreshed** - Reported; the run continues
17. **upgrade the system** - `apt-get upgrade --with-new-pkgs -y`

### 🌐 Network Configuration (Conditional)
12. **check if any interface has IP 10.10.10.11** - Detect existing Mesa network configuration
13. **get available ethernet interfaces** - List available network interfaces (if needed)
14. **prompt for ethernet interface selection** - Interactive interface selection (if needed)
15. **configure selected interface with Mesa IP** - Set up Mesa network connection (if needed)

### 📦 Package Installation
**install required packages** - git, cinnamon, x11vnc, x11-xserver-utils, python3-dbus

### 🖥️ Desktop Environment Setup
17. **set cinnamon as default session manager** - Configure lightdm for Cinnamon
18. **do not lock the screen** - No password prompt between operator and machine
19. **enable the screensaver overlay** - So a waking touch is not a click in AXIS
20. **show the screensaver overlay after 600s idle** - `org.cinnamon.desktop.session idle-delay`
21. **power the panel down after 660s idle** - `sleep-display-ac`, staggered behind the overlay
22. **install the display guard** - `/usr/local/bin/cncpc-display-guard`
23. **install the display guard user unit** - `/etc/systemd/user/cncpc-display-guard.service`
24. **enable the display guard for every graphical session** - `systemctl --global enable`
25. **start the display guard in the current session if there is one** - Best-effort, non-fatal
26. **install the greeter blanking script** - `/usr/local/bin/cncpc-greeter-blank`
27. **point lightdm at the greeter blanking script** - `lightdm.conf.d` drop-in
28. **apply greeter blanking to the X server already running** - No lightdm restart, so no session is killed
29. **report what the greeter blanking did** - Says whether it reached a live display

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
- **DE**: Cinnamon, screen lock disabled, screensaver overlay **enabled**
- **Display**: overlay at 10 min idle, panel powered off at 11 min, both suspended while a program runs
- **Session**: Configured as default in lightdm

#### Display blanking, and why it is shaped this way

Rewritten 2026-09-07, when the panel became an **Elo 2494L**. What was here
before amounted to "never blank": lock off, idle activation off, display sleep
at 3600s. cncpc idles at a static LinuxCNC GUI far more than it cuts, so that
was an hour of unchanging DRO digits in fixed pixels, indefinitely. The 2494L
is an LED-backlit industrial LCD, so the exposure is **not** OLED burn-in — it
is backlight hours (8760 a year if the panel never sleeps, against a rating in
the tens of thousands) and image sticking.

**The touchscreen is why a shorter timeout alone would have been the wrong
patch.** DPMS powers the panel down but leaves X fully live, so a touch on a
dark screen is delivered to whatever sits underneath it. The operator's
wake-up tap would become a blind click in AXIS, at a coordinate they did not
choose, on a machine tool. So `idle-activation-enabled` is turned back **on**:
cinnamon-screensaver takes an input grab and spends that first touch
dismissing the overlay. `lock-enabled` stays `false` — the overlay exists to
eat one touch, not to put a password between an operator and a running
machine. The two timeouts are staggered (`idle-delay` 600s, `sleep-display-ac`
660s) so the grab is in place before the screen goes dark.

`cncpc-display-guard` then suspends both while LinuxCNC is actually working.
It holds two independent layers, because two independent things blank this
screen:

| Layer | What blanks it | How the guard holds it |
|---|---|---|
| Session | cinnamon-screensaver + csd-power, on the session idle timer | `org.freedesktop.ScreenSaver` Inhibit cookie — dies with the process's D-Bus connection, so a crash cannot wedge the screen on |
| X server | the server's own DPMS timers | `xset -dpms`, re-applied every poll so it self-heals if csd-power re-asserts DPMS underneath it |

"Busy" is deliberately wider than "a G-code program is streaming": a paused
program, a task in `RCS_EXEC`, and a spinning spindle all count, because in all
of them the operator is at the machine and wants the DRO. Every error path —
no `linuxcnc` module, a dead NML channel, an unexpected spindle shape — fails
to **idle**, i.e. "let the screen blank". A broken guard costs a dark screen
someone wakes with a touch; the opposite default would cook the panel for
months and report nothing. On exit it restores `+dpms`, so a stopped guard
cannot leave the display pinned on.

**It never injects synthetic input.** The usual trick for keeping a screen
awake is nudging a key or the pointer, and on a CNC that is a loaded gun — a
fake keystroke into AXIS is a jog, an estop toggle, or a spindle command
depending on focus. The guard changes blanking policy and nothing else.

Tuning: `cncpc_display_idle_secs`, `cncpc_display_blank_secs` and
`cncpc_display_poll_secs` at the top of the playbook. Keep idle < blank.

Watching it work (fine over SSH — `systemctl --user` reaches the same user
manager, since there is one per *user*, not per session):

```bash
journalctl --user -fu cncpc-display-guard.service
```

#### The greeter is protected separately, and has to be

The guard is a **user** service and can only reach the logged-in session's X
server. Measured on the live machine sitting at the login screen:

```
Xorg :0 -seat seat0 -auth /var/run/lightdm/root/:0 ... vt7
session c2  lightdm  seat0  greeter
```

The greeter's X **is** `:0`, but its auth cookie is lightdm's root-only file,
while the guard holds `evand`'s `~/.Xauthority`. So the guard is locked out and
logs `CANNOT REACH display :0` — correctly — for every second cncpc sits there.
That is not a defect: a user service cannot reach a display it has no cookie
for, and should not be given one.

What matters is the consequence. **cncpc returns to the greeter after any
unattended reboot** — a power interruption, a watchdog, an overnight update —
and can sit there for days showing one static login form. That is exactly the
burn-in and backlight-hours case the whole exercise exists to prevent, in the
one state where nobody is present to notice. Protection that requires an
operator already logged in is not protection.

So `/usr/local/bin/cncpc-greeter-blank` is wired into lightdm's
`display-setup-script` hook, which runs as root at display setup with `DISPLAY`
and `XAUTHORITY` already correct. It applies the same two timeouts at the X
level — blank at `cncpc_display_idle_secs`, panel off at
`cncpc_display_blank_secs` — so both states behave identically.

No screensaver overlay there, deliberately: the overlay exists in the session to
swallow the touch that wakes a dark 2494L, because in AXIS that touch would be a
blind button press on a machine tool. At the greeter the worst a stray touch can
do is put a character in a password field. Nothing can move.

**The script exits 0 unconditionally.** A nonzero exit from
`display-setup-script` can stop the greeter coming up at all — which on this
machine would mean a CNC that boots to a blank screen after a power cut, caused
by the script meant to protect its monitor. Every command is forgiving and the
exit is forced.

Installing it does **not** restart lightdm, because that kills the logged-in
session and can take LinuxCNC down mid-job. The playbook applies the settings to
the already-running X server instead, reading the auth path off the live `Xorg`
process rather than assuming `/var/run/lightdm/root/:0` — that is what lightdm
uses today, and a version bump is free to change it.

### System Hardening
- **Kernel Management**: RT kernel packages held to prevent breaking updates
- **Initramfs**: Automatic updates disabled to prevent boot issues
- **Services**: brltty services disabled (interfere with USB devices)
- **Updates**: Safe upgrade process after system hardening

#### The apt cache, and why one dead repo no longer stops a rebuild

Added 2026-09-07, after a third-party repo halted a whole provisioning run.

QtPyVCP rotated the signing key on their `develop` repo on 2026-09-01. cncpc
still had the old one, so the `InRelease` signature stopped verifying.
`apt-get update` treats that as a **warning** — it keeps the previous index for
that repo, reports every other repo as `Hit`, and **exits 0**.
`ansible.builtin.apt`'s `update_cache` does not: it calls python-apt's
`cache.update()`, which raises if *any* index fails to fetch. So a repo that
nothing is installed from killed `install required packages`, five retries
deep, with:

```
Failed to update apt cache after 5 retries:
```

Note the empty reason — that message is the module's, not apt's. The run died
at a task unconnected to the broken repo, and named neither the repo nor the
key. Diagnosing it meant running `apt-get update` by hand to see what Ansible
had swallowed.

The cache is now refreshed **once**, and failures are classified rather than
treated alike:

| What failed | What happens |
|---|---|
| A repo in `cncpc_apt_required_hosts` | **Fatal**, and the repo is named |
| Any other repo | Reported; the run continues |
| `apt-get update` exits nonzero with no `Err:` line | **Fatal**, full output shown |

Every `ansible.builtin.apt` task carries `update_cache: no` and leans on that
one task. The point is to put the judgement about which repos are load-bearing
in **one readable place**, instead of spread across four tasks that each fail
the same undifferentiated way. Debian being unreachable means the packages
cannot be installed and the run is worthless; a third-party repo being
unreachable means a rotated key, a dead domain, or a source the machine no
longer uses — worth *saying*, never worth aborting a machine-tool rebuild over.

**This logic is tested, because reading it was not enough to get it right.**

```bash
python3 tests/test_apt_classification.py
```

Written with single backslashes, `regex_replace(..., '\1')` looks correct in
YAML — but Jinja reads `'\1'` as a *Python* string escape and hands the regex
the control character `0x01` instead of a backreference. Every failed repo
collapsed to the same unmatchable string and sorted into the *incidental*
bucket, so a dead Debian mirror would have been tolerated and the run would
have continued into an install it could not perform: the exact failure this
block exists to prevent, reintroduced one escape level down. Nothing about it
looks wrong on the page. Rendering the expressions against real apt output
caught it on the first run. `--syntax-check` cannot — it validates YAML shape
and never renders a template.

## File Structure

```
dcnc-ansible/
├── README.md                 # This file
├── playbook.yml             # Main Ansible playbook
├── inventory.ini            # Inventory configuration
├── files/                   # Source files for copying
│   ├── 99-imach-p4s.rules  # udev rules for imach-p4s hardware
│   ├── cncpc-display-guard # holds the display awake while LinuxCNC runs
│   └── x11vnc.service      # x11vnc systemd service definition
├── templates/               # Templated files
│   ├── cncpc-display-guard.service.j2  # user unit for the display guard
│   ├── cncpc-greeter-blank.j2          # blanks the panel at the lightdm greeter
│   ├── lightdm-cncpc-display.conf.j2   # drop-in wiring the greeter hook
│   └── cncpc-restic-backup.sh.j2       # restic backup/prune script
├── tests/                   # Runnable checks (no ansible required)
│   └── test_apt_classification.py      # proves the apt-failure classification
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

Note that `-vvv` prints each task's full module arguments. Tasks handling
secrets are marked `no_log`, so the Adafruit IO key and the restic repository
password appear as `censored` rather than in clear -- that is deliberate, and
the cost is that those tasks' `changed`/`ok` detail is suppressed too. If you
need to see whether such a task acted, check the effect on the machine rather
than reaching for more `-v`.

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
