# Rich System Monitor

A beautiful, real-time system monitoring tool built with Python's Rich library. Features smooth updates, professional styling, and comprehensive system metrics display.

## Features

- **Real-time monitoring** with smooth, flash-free updates
- **Beautiful interface** with color-coded progress bars and panels
- **Comprehensive metrics**: CPU cores, memory, disk, network, top processes
- **Multiple display modes**: single report, live monitoring, fast updates
- **Professional styling** with borders, colors, and proper typography
- **Cross-platform** support (Linux, macOS, Windows)

## Installation

1. **Clone or download** this directory to your target machine
2. **Run the installer**:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

The installer will:
- Create a Python virtual environment
- Install all required dependencies (Rich, psutil)
- Set up executable scripts
- Verify everything is working

## Usage

### Quick Start
```bash
# Single system report
./sysmon

# Live monitoring (updates every second)
./sysmon --live

# Fast live monitoring (updates every 0.5 seconds)
./sysmon --fast

# Show help
./sysmon --help
```

### Alternative Usage
```bash
# Using run.sh directly
./run.sh --live
./run.sh --fast
```

## Display Modes

### Single Report Mode (default)
Displays a one-time snapshot of system metrics in a beautiful layout.

### Live Monitoring Mode (`--live`)
Continuously updates the display every second with real-time system data. Press `Ctrl+C` to exit.

### Fast Monitoring Mode (`--fast`)
Updates every 0.5 seconds for high-frequency monitoring. Useful for performance testing or troubleshooting.

## System Requirements

- **Python 3.6+** with venv module
- **Linux/Unix system** (tested on Ubuntu, should work on most distributions)
- **Terminal** with color support (most modern terminals)
- **Sufficient permissions** to read system information

## What's Monitored

- **System Information**: Hostname, OS, uptime, CPU cores, load averages
- **CPU Usage**: Overall percentage and individual core usage with visual bars
- **Memory**: Usage percentage, total/available memory
- **Disk**: Usage percentage, free/total space
- **Network**: Bytes sent/received totals
- **Processes**: Top memory-consuming processes with CPU and memory percentages

## Packaging for Other Machines

This project is designed to be easily portable:

1. **Copy the entire `rich-sysmon` directory** to the target machine
2. **Run `./install.sh`** on the target machine
3. **Start monitoring** with `./sysmon`

No system-wide installation required - everything runs in an isolated virtual environment.

## Troubleshooting

### Installation Issues
- **Python 3 not found**: Install Python 3.6 or newer
- **venv module missing**: Install `python3-venv` package
- **Permission denied**: Run `chmod +x install.sh run.sh sysmon`

### Runtime Issues
- **Virtual environment not found**: Run `./install.sh` first
- **Import errors**: Delete `venv` directory and run `./install.sh` again
- **Permission errors**: Ensure user has access to `/proc` filesystem

## Uninstallation

Simply delete the `rich-sysmon` directory. No system files are modified.

## License

Open source - feel free to modify and distribute.
