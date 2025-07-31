#!/usr/bin/env python3
"""
Rich System Monitor - Beautiful terminal-based system monitoring
Uses Rich library for enhanced terminal graphics and smooth updates
"""

import psutil
import platform
import datetime
import os
import time
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TextColumn
from rich.align import Align
from rich import box
from rich.tree import Tree
from rich.bar import Bar

class RichSystemMonitor:
    def __init__(self):
        self.console = Console()
        
    def get_system_stats(self):
        """Get current system statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_cores = psutil.cpu_percent(interval=0.1, percpu=True)
            memory = psutil.virtual_memory()
            disk_partitions = self.get_disk_info()
            network = psutil.net_io_counters()
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time

            return {
                'cpu_percent': cpu_percent,
                'cpu_cores': cpu_cores,
                'memory': memory,
                'disk_partitions': disk_partitions,
                'network': network,
                'uptime': uptime,
                'hostname': platform.node(),
                'system': platform.system(),
                'load_avg': os.getloadavg()
            }
        except Exception as e:
            return None

    def get_disk_info(self):
        """Get detailed disk information for all mounted drives including USB"""
        disk_info = []
        try:
            partitions = psutil.disk_partitions()
            for partition in partitions:
                # Skip snap mounts and other virtual filesystems, but include USB drives
                if (partition.fstype in ['squashfs', 'tmpfs', 'devtmpfs'] or
                    '/snap/' in partition.mountpoint or
                    partition.mountpoint in ['/dev', '/proc', '/sys', '/run']):
                    continue

                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    # Only include drives with significant size (> 100MB)
                    if usage.total > 100 * 1024 * 1024:
                        # Determine drive type
                        drive_type = self._get_drive_type(partition)

                        disk_info.append({
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free,
                            'percent': usage.percent,
                            'drive_type': drive_type
                        })
                except PermissionError:
                    continue

            # Sort by drive type and mountpoint (root first, then internal, then external)
            disk_info.sort(key=lambda x: (
                x['drive_type'] != 'system',
                x['drive_type'] != 'internal',
                x['drive_type'] != 'external',
                x['mountpoint'] != '/',
                x['mountpoint']
            ))
            return disk_info
        except Exception:
            return []

    def _get_drive_type(self, partition):
        """Determine if drive is system, internal, or external (USB)"""
        device = partition.device
        mountpoint = partition.mountpoint

        # System drives
        if mountpoint in ['/', '/boot', '/boot/efi']:
            return 'system'

        # External drives (USB, etc.)
        if ('/media/' in mountpoint or
            '/mnt/' in mountpoint or
            'usb' in mountpoint.lower() or
            'removable' in mountpoint.lower()):
            return 'external'

        # Check device name patterns for USB drives
        if ('/dev/sd' in device and
            device not in ['/dev/sda1', '/dev/sda2', '/dev/sda3']):  # Assume sda is main drive
            return 'external'

        return 'internal'
    
    def get_top_processes(self, count=8):
        """Get top processes by CPU and memory usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent', 'username']):
                try:
                    if proc.info['memory_percent'] > 0.1:
                        processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Sort by memory usage
            memory_procs = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:count]
            # Sort by CPU usage
            cpu_procs = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:count]

            return {
                'memory': memory_procs,
                'cpu': cpu_procs
            }
        except:
            return {'memory': [], 'cpu': []}
    
    def create_progress_bar(self, percentage, width=20):
        """Create a visual progress bar"""
        filled = int(percentage / 100 * width)
        empty = width - filled
        
        if percentage > 80:
            color = "red"
        elif percentage > 60:
            color = "yellow"
        else:
            color = "green"
            
        bar = "█" * filled + "░" * empty
        return f"[{color}]{bar}[/{color}] {percentage:5.1f}%"
    
    def create_system_info_panel(self, stats):
        """Create system information panel without animation"""
        if not stats:
            return Panel("Error loading system stats", title="System Info", border_style="red")

        # Create enhanced load visualization
        load_display = self._create_load_visualization(stats['load_avg'], len(stats['cpu_cores']))

        # Create info text with focus on system specs and load
        info_text = f"""🖥️  [bold white]{stats['hostname']}[/bold white]
⚙️  [yellow]{len(stats['cpu_cores'])} CPU Cores[/yellow]
💾 [magenta]{stats['memory'].total / (1024**3):.1f} GB RAM[/magenta]

{load_display}"""

        return Panel(info_text, title="[bold blue]🖥️ System Status[/bold blue]", border_style="blue")

    def create_animation_panel(self, stats):
        """Create separate animation panel with time and uptime"""
        spinner_display = self._create_spinner_animation()

        # Get current time and date (human-friendly)
        now = datetime.datetime.now()
        current_time = now.strftime("%I:%M:%S %p")
        current_date = now.strftime("%A, %B %d")

        # Format uptime
        if stats:
            uptime_str = f"{stats['uptime'].days}d {stats['uptime'].seconds//3600}h {(stats['uptime'].seconds//60)%60}m"
        else:
            uptime_str = "N/A"

        # Combine animation with time info
        time_info = f"""
🕐 [bright_cyan]{current_time}[/bright_cyan]
📅 [dim]{current_date}[/dim]
⏱️  [green]{uptime_str}[/green]"""

        content = Columns([spinner_display, time_info], equal=False, expand=True)
        return Panel(content, title="[bold magenta]⚡ Live Status[/bold magenta]", border_style="magenta")

    def _create_spinner_animation(self):
        """Create an enhanced spinning animation with randomized colors and patterns"""
        now = datetime.datetime.now()
        second = now.second
        minute = now.minute
        hour = now.hour

        # Time-seeded randomization for continuity
        time_seed = (hour * 3600 + minute * 60 + second) // 10  # Changes every 10 seconds

        # Color palettes that change based on time seed
        color_palettes = [
            {"primary": "bright_cyan", "secondary": "cyan", "accent": "blue", "center": "yellow"},
            {"primary": "bright_magenta", "secondary": "magenta", "accent": "red", "center": "white"},
            {"primary": "bright_green", "secondary": "green", "accent": "yellow", "center": "red"},
            {"primary": "bright_yellow", "secondary": "yellow", "accent": "red", "center": "white"},
            {"primary": "bright_blue", "secondary": "blue", "accent": "cyan", "center": "white"},
            {"primary": "bright_red", "secondary": "red", "accent": "magenta", "center": "yellow"},
        ]

        # Select color palette based on time seed
        palette = color_palettes[time_seed % len(color_palettes)]

        # Different spinner patterns
        spinners = [
            ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],  # Dots
            ["◐", "◓", "◑", "◒"],  # Half circles
            ["▁", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃"],  # Bars
            ["◜", "◠", "◝", "◞", "◡", "◟"],  # Arcs
            ["◢", "◣", "◤", "◥"],  # Triangles
            ["⬢", "⬡", "⬢", "⬡"],  # Hexagons
            ["◆", "◇", "◆", "◇"],  # Diamonds
            ["⚬", "⚭", "⚬", "⚭"],  # Circles
        ]

        # Select spinner based on minute
        spinner_set = spinners[minute % len(spinners)]
        frame = spinner_set[second % len(spinner_set)]

        # Use consistent-width outer elements to prevent shifting
        outer_elements = ["∘", "○", "◦", "●", "◉", "⬢"]  # All single-width characters
        outer_char = outer_elements[second % len(outer_elements)]

        # Create brightness variations (safe markup)
        brightness_cycle = second % 6
        if brightness_cycle < 2:
            outer_color = "dim"
            ring_color = "bright_cyan"
        elif brightness_cycle < 4:
            outer_color = "cyan"
            ring_color = "bright_blue"
        else:
            outer_color = "bright_cyan"
            ring_color = "blue"

        # Create pulsing center elements (consistent width)
        center_chars = ["●", "◉", "◎", "⬢", "◆"]  # All single-width characters
        center_char = center_chars[(second // 2) % len(center_chars)]

        # Get center color from palette
        center_color = palette['center']
        accent_color = palette['accent']

        # Create radiating pattern with safe markup
        radiating = [
            f"     [{outer_color}]{outer_char}[/{outer_color}]     ",
            f"   [{outer_color}]{outer_char}[/{outer_color}] [{ring_color}]∘[/{ring_color}] [{outer_color}]{outer_char}[/{outer_color}]   ",
            f" [{outer_color}]{outer_char}[/{outer_color}] [{ring_color}]∘[/{ring_color}] [bold {accent_color}]{center_char}[/bold {accent_color}] [{ring_color}]∘[/{ring_color}] [{outer_color}]{outer_char}[/{outer_color}] ",
            f"   [{ring_color}]∘[/{ring_color}] [bold {center_color}]{frame}[/bold {center_color}] [{ring_color}]∘[/{ring_color}]   ",
            f" [{outer_color}]{outer_char}[/{outer_color}] [{ring_color}]∘[/{ring_color}] [bold {accent_color}]{center_char}[/bold {accent_color}] [{ring_color}]∘[/{ring_color}] [{outer_color}]{outer_char}[/{outer_color}] ",
            f"   [{outer_color}]{outer_char}[/{outer_color}] [{ring_color}]∘[/{ring_color}] [{outer_color}]{outer_char}[/{outer_color}]   ",
            f"     [{outer_color}]{outer_char}[/{outer_color}]     "
        ]

        return "\n".join(radiating)

    def _create_load_visualization(self, load_avg, cpu_count):
        """Create enhanced load average visualization"""
        load_1min, load_5min, load_15min = load_avg

        # Calculate load percentages relative to CPU count
        load_1_pct = (load_1min / cpu_count) * 100
        load_5_pct = (load_5min / cpu_count) * 100
        load_15_pct = (load_15min / cpu_count) * 100

        # Create visual bars for each load average
        def create_load_bar(load_val, load_pct):
            bar_length = 12
            filled = int(min(load_pct / 100 * bar_length, bar_length))
            empty = bar_length - filled

            if load_pct > 80:
                color = "red"
                status = "HIGH"
            elif load_pct > 50:
                color = "yellow"
                status = "MED"
            else:
                color = "green"
                status = "LOW"

            bar = "█" * filled + "░" * empty
            return f"[{color}]{bar}[/{color}] {load_val:4.2f} [{color}]{status}[/{color}]"

        load_display = f"""📊 [bold white]System Load Average[/bold white]
┌─ 1min:  {create_load_bar(load_1min, load_1_pct)}
├─ 5min:  {create_load_bar(load_5min, load_5_pct)}
└─ 15min: {create_load_bar(load_15min, load_15_pct)}"""

        return load_display

    def create_resource_panel(self, stats):
        """Create resource usage panel"""
        if not stats:
            return Panel("Error loading resource stats", title="Resources", border_style="red")

        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("Resource", style="cyan", width=12)
        table.add_column("Usage", style="white", width=15)
        table.add_column("Visual", width=30)

        # CPU
        cpu_bar = self.create_progress_bar(stats['cpu_percent'])
        table.add_row("CPU", f"{stats['cpu_percent']:.1f}%", cpu_bar)

        # Memory
        mem_bar = self.create_progress_bar(stats['memory'].percent)
        mem_used_gb = stats['memory'].used / (1024**3)
        mem_total_gb = stats['memory'].total / (1024**3)
        table.add_row("Memory", f"{stats['memory'].percent:.1f}% ({mem_used_gb:.1f}/{mem_total_gb:.1f} GB)", mem_bar)

        # Network (show totals)
        net_sent = stats['network'].bytes_sent / (1024**2)  # MB
        net_recv = stats['network'].bytes_recv / (1024**2)  # MB
        table.add_row("Net Sent", f"{net_sent:.1f} MB", "")
        table.add_row("Net Recv", f"{net_recv:.1f} MB", "")

        return Panel(table, title="[bold green]Resource Usage[/bold green]", border_style="green")

    def create_disk_panel(self, stats):
        """Create card-based disk usage panel"""
        if not stats or not stats['disk_partitions']:
            return Panel("Error loading disk stats", title="Storage Dashboard", border_style="red")

        # Create cards for each drive
        drive_cards = []

        for disk in stats['disk_partitions']:
            card = self._create_drive_card(disk)
            drive_cards.append(card)

        # Arrange cards in a responsive grid
        cards_layout = Columns(drive_cards, equal=False, expand=False)

        return Panel(cards_layout, title="[bold cyan]💾 Storage Dashboard[/bold cyan]", border_style="cyan")

    def _create_drive_card(self, disk):
        """Create a card-style display for a single drive"""
        # Format sizes
        if disk['total'] > 1024**4:  # TB
            total_size = f"{disk['total'] / (1024**4):.1f}TB"
            used_size = f"{disk['used'] / (1024**4):.1f}TB"
            free_size = f"{disk['free'] / (1024**4):.1f}TB"
        else:  # GB
            total_size = f"{disk['total'] / (1024**3):.0f}GB"
            used_size = f"{disk['used'] / (1024**3):.0f}GB"
            free_size = f"{disk['free'] / (1024**3):.0f}GB"

        # Determine icon and colors based on drive type
        if disk['drive_type'] == 'system':
            if disk['mountpoint'] == '/':
                icon = "🖥️"
                title_color = "bold blue"
                border_color = "blue"
            else:
                icon = "⚙️"
                title_color = "bold cyan"
                border_color = "cyan"
        elif disk['drive_type'] == 'external':
            icon = "🔌"
            title_color = "bold yellow"
            border_color = "yellow"
        else:
            icon = "💿"
            title_color = "bold green"
            border_color = "green"

        # Create progress bar
        percent = disk['percent']
        bar_length = 16
        filled = int(percent / 100 * bar_length)
        empty = bar_length - filled

        if percent > 80:
            bar_color = "red"
        elif percent > 60:
            bar_color = "yellow"
        else:
            bar_color = "green"

        bar = "█" * filled + "░" * empty
        usage_bar = f"[{bar_color}]{bar}[/{bar_color}]"

        # Get device name (truncate to fit card width)
        device_name = disk['device']
        if '/dev/mapper/' in device_name:
            device_name = device_name.split('/')[-1][:10]  # Shorter for mapper devices
        elif '/dev/sd' in device_name:
            device_name = device_name.split('/')[-1]

        # Ensure device name fits in card
        if len(device_name) > 12:
            device_name = device_name[:12]

        # Format mount point - show first 10 chars of last segment or special names
        mount_path = disk['mountpoint']
        if mount_path == '/':
            mount_display = 'root'
        elif mount_path == '/boot':
            mount_display = 'boot'
        elif mount_path == '/boot/efi':
            mount_display = 'efi'
        else:
            # Get the last segment of the path (after the last /)
            last_segment = mount_path.split('/')[-1]
            # Take first 10 characters of that segment
            mount_display = last_segment[:10] if len(last_segment) > 10 else last_segment
            # If the last segment is empty (path ends with /), use the second-to-last segment
            if not mount_display and len(mount_path.split('/')) > 1:
                last_segment = mount_path.split('/')[-2]
                mount_display = last_segment[:10] if len(last_segment) > 10 else last_segment

        # Create card content
        card_content = f"""{icon} [{title_color}]{device_name}[/{title_color}]
[dim]{disk['fstype']}[/dim]

📂 [cyan]{mount_display}[/cyan]

{usage_bar} [white]{percent:.0f}%[/white]

💾 [white]{used_size}[/white] / [green]{total_size}[/green]
🆓 [bright_green]{free_size}[/bright_green]"""

        return Panel(
            card_content,
            border_style=border_color,
            padding=(0, 1),
            width=20  # Slightly smaller to prevent wrapping
        )
    
    def create_cpu_cores_panel(self, stats):
        """Create CPU cores panel with vertical equalizer-style bars"""
        if not stats:
            return Panel("Error loading CPU stats", title="CPU Cores", border_style="red")

        # Create vertical equalizer display
        max_height = 8  # Height of the equalizer bars
        cores = stats['cpu_cores']

        # Build the equalizer from top to bottom
        equalizer_lines = []

        # Create vertical bars (from top to bottom)
        for row in range(max_height):
            line = ""
            for i, usage in enumerate(cores):
                # Calculate how many bars this core should have
                bars_needed = int((usage / 100) * max_height)

                # Determine if this row should have a bar (counting from bottom)
                current_row_from_bottom = max_height - row - 1

                if current_row_from_bottom < bars_needed:
                    # Choose color based on usage
                    if usage > 80:
                        color = "red"
                    elif usage > 60:
                        color = "yellow"
                    elif usage > 30:
                        color = "green"
                    else:
                        color = "blue"

                    # Align bars with numbers: right-align in 2-char field + space
                    if i < len(cores) - 1:
                        line += f" [{color}]█[/{color}] "  # Space + bar + space to match " 0 "
                    else:
                        line += f" [{color}]█[/{color}]"   # Last: space + bar (matches "15")
                else:
                    # Show empty bar for contrast with same spacing
                    if i < len(cores) - 1:
                        line += " [dim]░[/dim] "  # Space + bar + space
                    else:
                        line += " [dim]░[/dim]"   # Last: space + bar

            equalizer_lines.append(line.rstrip())

        # Add core numbers at the bottom with consistent spacing
        # Each column should be 2 characters wide to accommodate double-digit numbers
        core_line = ""
        for i, usage in enumerate(cores):
            # Format each number to take exactly 2 characters (right-aligned)
            core_line += f"{i:>2}"
            if i < len(cores) - 1:
                core_line += " "  # Single space between numbers

        equalizer_lines.append(core_line)

        equalizer_display = "\n".join(equalizer_lines)

        return Panel(equalizer_display, title="[bold yellow]🎚️ CPU Equalizer[/bold yellow]", border_style="yellow")
    
    def create_top_memory_panel(self, processes):
        """Create top memory processes panel"""
        if not processes or not processes['memory']:
            return Panel("Error loading memory stats", title="Top Memory", border_style="red")

        table = Table(show_header=True, header_style="bold green", box=box.SIMPLE)
        table.add_column("PID", style="cyan", width=6)
        table.add_column("Process", style="white", width=12)
        table.add_column("MEM%", style="green", width=6)
        table.add_column("Usage", width=15)

        for proc in processes['memory'][:8]:  # Show top 8
            mem_percent = proc['memory_percent']
            # Create mini progress bar
            bar_length = int(mem_percent / 2)  # Scale for display
            bar = "█" * min(bar_length, 15) + "░" * max(0, 15 - bar_length)
            color = "red" if mem_percent > 10 else "yellow" if mem_percent > 5 else "green"
            visual_bar = f"[{color}]{bar}[/{color}]"

            table.add_row(
                str(proc['pid']),
                proc['name'][:10],
                f"{mem_percent:.1f}",
                visual_bar
            )

        return Panel(table, title="[bold green]🧠 Top Memory[/bold green]", border_style="green")

    def create_top_cpu_panel(self, processes):
        """Create top CPU processes panel"""
        if not processes or not processes['cpu']:
            return Panel("Error loading CPU stats", title="Top CPU", border_style="red")

        table = Table(show_header=True, header_style="bold yellow", box=box.SIMPLE)
        table.add_column("PID", style="cyan", width=6)
        table.add_column("Process", style="white", width=12)
        table.add_column("CPU%", style="yellow", width=6)
        table.add_column("Usage", width=15)

        for proc in processes['cpu'][:8]:  # Show top 8
            cpu_percent = proc['cpu_percent'] or 0
            # Create mini progress bar
            bar_length = int(cpu_percent / 2)  # Scale for display
            bar = "█" * min(bar_length, 15) + "░" * max(0, 15 - bar_length)
            color = "red" if cpu_percent > 50 else "yellow" if cpu_percent > 20 else "green"
            visual_bar = f"[{color}]{bar}[/{color}]"

            table.add_row(
                str(proc['pid']),
                proc['name'][:10],
                f"{cpu_percent:.1f}",
                visual_bar
            )

        return Panel(table, title="[bold yellow]⚡ Top CPU[/bold yellow]", border_style="yellow")
    
    def create_layout(self):
        """Create the enhanced main layout with 3-column bottom section"""
        layout = Layout()

        # Split into header and body
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )

        # Split body into three rows for better organization
        layout["body"].split_column(
            Layout(name="top_row", ratio=2),
            Layout(name="middle_row", ratio=3),  # Give more space to disk explorer
            Layout(name="bottom_row", ratio=2)   # 3-column section
        )

        # Split top row into three columns (system info, resources, and animation)
        layout["top_row"].split_row(
            Layout(name="system_info"),
            Layout(name="resources"),
            Layout(name="animation", ratio=1)
        )

        # Middle row for disk usage (full width for explorer view)
        # (middle_row is already created, no need to reassign)

        # Split bottom row into three columns (CPU cores, top memory, top CPU)
        layout["bottom_row"].split_row(
            Layout(name="cpu_cores"),
            Layout(name="top_memory"),
            Layout(name="top_cpu")
        )

        return layout
    
    def update_layout(self, layout):
        """Update layout with current data"""
        stats = self.get_system_stats()
        processes = self.get_top_processes()

        # Header with AM/PM time
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        header_text = Text(f"Rich System Monitor - {current_time}", style="bold white on blue")
        layout["header"].update(Align.center(header_text))

        # Update panels
        layout["system_info"].update(self.create_system_info_panel(stats))
        layout["resources"].update(self.create_resource_panel(stats))
        layout["animation"].update(self.create_animation_panel(stats))
        layout["middle_row"].update(self.create_disk_panel(stats))
        layout["cpu_cores"].update(self.create_cpu_cores_panel(stats))
        layout["top_memory"].update(self.create_top_memory_panel(processes))
        layout["top_cpu"].update(self.create_top_cpu_panel(processes))
    
    def run_live_monitor(self, refresh_rate=1.0):
        """Run the live monitoring display"""
        layout = self.create_layout()
        
        try:
            with Live(layout, console=self.console, screen=True, auto_refresh=False) as live:
                while True:
                    self.update_layout(layout)
                    live.refresh()
                    time.sleep(refresh_rate)
        except KeyboardInterrupt:
            self.console.print("\n[bold red]Monitoring stopped.[/bold red]")
    
    def run_single_report(self):
        """Run a single report"""
        layout = self.create_layout()
        self.update_layout(layout)
        self.console.print(layout)

def main():
    """Main function"""
    monitor = RichSystemMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("Rich System Monitor")
            print("Usage:")
            print("  python3 sysmon_rich.py           # Single report")
            print("  python3 sysmon_rich.py --live    # Live monitoring (Ctrl+C to exit)")
            print("  python3 sysmon_rich.py --fast    # Live monitoring with 0.5s refresh")
            return
        elif sys.argv[1] == '--live':
            monitor.run_live_monitor(1.0)
            return
        elif sys.argv[1] == '--fast':
            monitor.run_live_monitor(0.5)
            return
    
    # Default: single report
    monitor.run_single_report()

if __name__ == "__main__":
    main()
