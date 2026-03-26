# FalcoMP

**FalcoMP** is a terminal-based device manager for MicroPython boards built around `mpremote`.  
It provides a structured interface for interacting with devices over serial, managing files, and streamlining development workflows.

---

## Features

- **Device Discovery**
  - Automatically detects devices connected via serial on startup

- **Terminal UI (TUI)**
  - Keyboard-driven interface

- **File Explorer**
  - Browse device filesystem
  - Create and delete files/directories
  - Run micropython files directly on the device remotely.

- **Command Abstraction**
  - Wraps common `mpremote` operations:
    - Run scripts
    - Open REPL
    - File transfer
    - Directory management

- **Smart Sync**
  - Diff-based synchronization between local working directory and device
  - Only modified files are written
  - Reduces unnecessary writes

- **Stub Generator**
  - Generates local type stubs from device modules
  - Improves editor support with a custom typing file catered to your specific port

- **Configuration Injection**
  - Automatically deploys a lightweight JSON config to each device
  - Enables:
    - Device naming
    - Ignore rules
    - Sync behavior control

---

## Installation

```bash
python -m venv env
env/Scripts/activate
pip install falco-mp
```

---

## Usage

Start the interface:

```bash
env/Scripts/activate
falco-mp
```

---

## Basic Workflow

1. Connect your MicroPython device via USB
2. Launch FalcoMP
3. Select your device from the menu
4. Use available actions:
   - Run scripts
   - Open REPL
   - Sync files
   - Manage filesystem

---

## Configuration

Each device receives a small JSON configuration file on first connection.

Example structure:

```json
{
  "name": "MyDevice",
  "serial": "<device serial if applicable>",
  "verify-on-sync": true,
  "preserve-device-files": false,
  "ignore": ["typings", "__pycache__"],
  "notes": []
}
```

- Stored directly on the device
- Used to control sync behavior and UI display

---

## Design Philosophy

- **Pure Python implementation**
- **Minimal overhead on device**
- **Deterministic file operations**
- **Optimized for MicroPython constraints**

---

## Requirements

- Python 3.10+
- MicroPython 1.16+

---

## Notes

- FalcoMP does not replace `mpremote` — it builds on top of it
- Designed for local, direct USB workflows (not network-first)

---

## License

MIT License