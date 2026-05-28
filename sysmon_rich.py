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
import subprocess
import json
import re
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
        """Get detailed disk information for user drives (excluding boot/efi)"""
        disk_info = []
        try:
            partitions = psutil.disk_partitions()
            for partition in partitions:
                # Skip snap mounts, virtual filesystems, boot partitions, and optical media
                skip_mounts = ['/dev', '/proc', '/sys', '/run', '/boot', '/boot/efi']
                if (partition.fstype in ['squashfs', 'tmpfs', 'devtmpfs', 'udf', 'iso9660'] or
                    '/snap/' in partition.mountpoint or
                    partition.mountpoint in skip_mounts):
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

            # Sort by priority: root first, then ai-storage, then others
            def sort_priority(x):
                if x['mountpoint'] == '/':
                    return (0, x['mountpoint'])
                elif x['mountpoint'] == '/ai-storage':
                    return (1, x['mountpoint'])
                elif x['mountpoint'] == '/cold-storage':
                    return (2, x['mountpoint'])
                elif 'masstore' in x['mountpoint']:
                    return (3, x['mountpoint'])
                else:
                    return (4, x['mountpoint'])

            disk_info.sort(key=sort_priority)
            return disk_info
        except Exception:
            return []

    def _get_drive_type(self, partition):
        """Determine if drive is system, internal, or external (USB)"""
        device = partition.device
        mountpoint = partition.mountpoint

        # System drives (root filesystem)
        if mountpoint == '/':
            return 'system'

        # AI storage and cold storage are internal
        if mountpoint in ['/ai-storage', '/cold-storage']:
            return 'internal'

        # External drives (USB, etc.)
        if ('/media/' in mountpoint or
            '/mnt/' in mountpoint or
            'usb' in mountpoint.lower() or
            'removable' in mountpoint.lower()):
            return 'external'

        return 'internal'

    def get_gpu_info(self):
        """Get NVIDIA GPU information using nvidia-smi"""
        try:
            # Run nvidia-smi to get GPU information
            result = subprocess.run([
                'nvidia-smi',
                '--query-gpu=index,name,temperature.gpu,power.draw,power.limit,memory.used,memory.total,utilization.gpu',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                return None

            gpu_info = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 8:
                        gpu_info.append({
                            'index': int(parts[0]),
                            'name': parts[1],
                            'temperature': int(parts[2]) if parts[2] != '[Not Supported]' else 0,
                            'power_draw': float(parts[3]) if parts[3] != '[Not Supported]' else 0,
                            'power_limit': float(parts[4]) if parts[4] != '[Not Supported]' else 250,
                            'memory_used': int(parts[5]),
                            'memory_total': int(parts[6]),
                            'utilization': int(parts[7]) if parts[7] != '[Not Supported]' else 0
                        })

            return gpu_info

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, ValueError):
            return None

    def get_gpu_processes(self):
        """Get GPU process information using nvidia-smi"""
        try:
            result = subprocess.run([
                'nvidia-smi',
                '--query-compute-apps=gpu_uuid,pid,process_name,used_memory',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                return []

            processes = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 4:
                        processes.append({
                            'gpu_uuid': parts[0],
                            'pid': int(parts[1]),
                            'name': parts[2],
                            'memory_used': int(parts[3])
                        })

            return processes

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, ValueError):
            return []

    def get_network_info(self):
        """Get network connectivity information"""
        try:
            # Check connectivity to known hosts
            hosts = {
                'iMac Server': '192.168.0.77',
                'Surface Pro': '192.168.0.116',
                'Gateway': '192.168.0.1'
            }

            connectivity = {}
            for name, ip in hosts.items():
                try:
                    result = subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                          capture_output=True, timeout=3)
                    connectivity[name] = result.returncode == 0
                except:
                    connectivity[name] = False

            # Get network stats
            net_io = psutil.net_io_counters()

            return {
                'connectivity': connectivity,
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }

        except Exception:
            return None

    def get_disk_io_stats(self):
        """Get disk I/O statistics"""
        try:
            # Get per-disk I/O stats
            disk_io = psutil.disk_io_counters(perdisk=True)
            return disk_io
        except Exception:
            return {}

    def get_system_vitals(self):
        """Get system temperature and fan information"""
        vitals = {
            'cpu_temps': [],
            'fans': [],
            'other_temps': []
        }

        try:
            # Try to get sensor data using psutil
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            if 'coretemp' in name.lower():
                                vitals['cpu_temps'].append({
                                    'label': entry.label or f'Core {len(vitals["cpu_temps"])}',
                                    'current': entry.current,
                                    'high': entry.high,
                                    'critical': entry.critical
                                })
                            else:
                                vitals['other_temps'].append({
                                    'label': entry.label or name,
                                    'current': entry.current,
                                    'high': entry.high,
                                    'critical': entry.critical
                                })

            # Try to get fan data
            if hasattr(psutil, 'sensors_fans'):
                fans = psutil.sensors_fans()
                if fans:
                    for name, entries in fans.items():
                        for entry in entries:
                            vitals['fans'].append({
                                'label': entry.label or name,
                                'current': entry.current
                            })

        except Exception:
            pass

        return vitals

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
        """Create system information panel with compact load info"""
        if not stats:
            return Panel("Error loading system stats", title="System Info", border_style="red")

        # Get load info
        load_1min = stats['load_avg'][0]
        cpu_count = len(stats['cpu_cores'])
        load_pct = (load_1min / cpu_count) * 100

        # Determine load status and color
        if load_1min < 1:
            load_status = "Light"
            load_color = "green"
        elif load_1min < cpu_count * 0.7:
            load_status = "Normal"
            load_color = "yellow"
        elif load_1min < cpu_count:
            load_status = "High"
            load_color = "yellow"
        else:
            load_status = "Overload"
            load_color = "red"

        # Create compact load bar
        bar_length = 12
        filled = int(min(load_pct / 100 * bar_length, bar_length))
        empty = bar_length - filled
        load_bar = "█" * filled + "░" * empty

        load_5min  = stats['load_avg'][1]
        load_15min = stats['load_avg'][2]

        # Get temperature data
        vitals = self.get_system_vitals()
        temp_lines = ""
        if vitals['cpu_temps']:
            cpu_temp = vitals['cpu_temps'][0]['current']
            tc = "red" if cpu_temp > 80 else "yellow" if cpu_temp > 70 else "green"
            temp_lines += f"\n🔥 CPU: [{tc}]{cpu_temp:.0f}°C[/{tc}]"
        if vitals['other_temps']:
            for temp in vitals['other_temps'][:2]:
                if temp['current'] and temp['current'] > 0:
                    tc = "red" if temp['current'] > 60 else "yellow" if temp['current'] > 45 else "green"
                    label = temp['label']
                    if 'temp1' in label or 'temp2' in label:
                        dl = "Case"
                    elif 'temp3' in label:
                        dl = "Chipset"
                    else:
                        dl = label[:7]
                    temp_lines += f"\n🌡️ {dl}: [{tc}]{temp['current']:.0f}°C[/{tc}]"

        # Create info text with load and temps
        info_text = f"""🖥️  [bold white]{stats['hostname'][:20]}[/bold white]
⚙️  [yellow]{cpu_count} CPU Cores[/yellow]
💾 [magenta]{stats['memory'].total / (1024**3):.1f} GB RAM[/magenta]

📊 [bold white]Load:[/bold white] [{load_color}]{load_bar}[/{load_color}] [{load_color}]{load_status}[/{load_color}]
[dim]  1m[/dim]  [{load_color}]{load_1min:.2f}[/{load_color}]  [dim]5m[/dim]  [white]{load_5min:.2f}[/white]  [dim]15m[/dim]  [white]{load_15min:.2f}[/white]
[dim]  [{load_color}]{load_pct:.1f}% of {cpu_count} cores[/{load_color}][/dim]
{temp_lines}"""

        return Panel(info_text, title="[bold blue]🖥️ System Status[/bold blue]", border_style="blue")

    def create_animation_panel(self, stats):
        """Create live status panel with time, uptime, network hosts and interfaces"""
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

        # Network host connectivity
        network_info = self.get_network_info()
        host_lines = ""
        if network_info:
            for name, status in network_info['connectivity'].items():
                icon = "✅" if status else "❌"
                short_name = name.split()[0]
                host_lines += f"\n  {icon} {short_name}"

        # Combine: spinner + time on the left, network on the right
        time_info = f"""🕐 [bright_cyan]{current_time}[/bright_cyan]
📅 [dim]{current_date}[/dim]
⏱️  [green]{uptime_str}[/green]

🌐 [bold white]Hosts:[/bold white]{host_lines}"""

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
        """Create enhanced load average visualization with explanation"""
        load_1min, load_5min, load_15min = load_avg

        # Calculate load percentages relative to CPU count
        load_1_pct = (load_1min / cpu_count) * 100
        load_5_pct = (load_5min / cpu_count) * 100
        load_15_pct = (load_15min / cpu_count) * 100

        # Create visual bars for each load average
        def create_load_bar(load_val, load_pct):
            bar_length = 10
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

        # Determine overall system status
        if load_1min < 1:
            system_status = "[green]System: Light Load[/green]"
        elif load_1min < cpu_count * 0.7:
            system_status = "[yellow]System: Normal Load[/yellow]"
        elif load_1min < cpu_count:
            system_status = "[yellow]System: High Load[/yellow]"
        else:
            system_status = "[red]System: Overloaded[/red]"

        load_display = f"""📊 [bold white]Load Average[/bold white] [dim](processes waiting)[/dim]
┌─ 1min:  {create_load_bar(load_1min, load_1_pct)}
├─ 5min:  {create_load_bar(load_5min, load_5_pct)}
└─ 15min: {create_load_bar(load_15min, load_15_pct)}

{system_status}"""

        return load_display

    def create_resource_panel(self, stats):
        """Create resource usage panel with inline labeled bars"""
        if not stats:
            return Panel("Error loading resource stats", title="Resources", border_style="red")

        def inline_bar(percent, width=14):
            filled = int(percent / 100 * width)
            color = "red" if percent > 80 else "yellow" if percent > 60 else "green"
            return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * (width - filled)}[/dim]", color

        # CPU
        cpu_pct = stats['cpu_percent']
        cpu_bar, cpu_color = inline_bar(cpu_pct)
        cpu_line = f"[bold cyan]CPU[/bold cyan]  {cpu_bar}  [{cpu_color}]{cpu_pct:5.1f}%[/{cpu_color}]"

        # Memory
        mem_pct = stats['memory'].percent
        mem_used = stats['memory'].used / (1024**3)
        mem_total = stats['memory'].total / (1024**3)
        mem_bar, mem_color = inline_bar(mem_pct)
        mem_line = (f"[bold cyan]RAM[/bold cyan]  {mem_bar}  [{mem_color}]{mem_pct:5.1f}%[/{mem_color}]"
                    f"  [dim]{mem_used:.0f}/{mem_total:.0f} GB[/dim]")

        # Network traffic
        def fmt_bytes(b):
            if b > 1024**3:
                return f"{b / 1024**3:.1f} GB"
            elif b > 1024**2:
                return f"{b / 1024**2:.0f} MB"
            else:
                return f"{b / 1024:.0f} KB"

        net = stats['network']
        sent_line = f"[yellow]↑[/yellow] [dim]Sent[/dim]  [white]{fmt_bytes(net.bytes_sent):>9}[/white]"
        recv_line = f"[cyan]↓[/cyan] [dim]Recv[/dim]  [white]{fmt_bytes(net.bytes_recv):>9}[/white]"
        pkts_line = f"[dim]Pkts: {net.packets_sent:,}↑ {net.packets_recv:,}↓[/dim]"

        # Active interfaces
        iface_lines = ""
        try:
            addrs = psutil.net_if_addrs()
            net_stats = psutil.net_if_stats()
            for iface, iface_stat in net_stats.items():
                if iface_stat.isup and iface not in ('lo', 'docker0') and not iface.startswith(('veth', 'br-')):
                    ip = ""
                    if iface in addrs:
                        for addr in addrs[iface]:
                            if addr.family.name == 'AF_INET':
                                ip = addr.address
                                break
                    speed = f" {iface_stat.speed}Mb" if iface_stat.speed > 0 else ""
                    iface_lines += f"\n[green]●[/green] {iface[:8]}{speed}"
                    if ip:
                        iface_lines += f" [dim]{ip}[/dim]"
        except Exception:
            pass

        content = f"{cpu_line}\n{mem_line}\n\n{sent_line}\n{recv_line}\n{pkts_line}{iface_lines}"
        return Panel(content, title="[bold green]Resource Usage[/bold green]", border_style="green")

    def create_disk_panel(self, stats):
        """Create spacious disk usage panel that uses available width"""
        if not stats or not stats['disk_partitions']:
            return Panel("Error loading disk stats", title="Storage Dashboard", border_style="red")

        table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED, padding=(0, 1))
        table.add_column("Drive", style="white", width=18, no_wrap=True)
        table.add_column("Usage", width=16, no_wrap=True)
        table.add_column("Size", style="dim", width=12, no_wrap=True)

        for disk in stats['disk_partitions'][:6]:  # Show up to 6 drives
            # Determine icon and colors
            if disk['drive_type'] == 'system':
                icon = "🖥️"
                color = "blue"
            elif disk['drive_type'] == 'internal':
                if 'ai-storage' in disk['mountpoint']:
                    icon = "🤖"
                    color = "green"
                elif 'cold-storage' in disk['mountpoint']:
                    icon = "❄️"
                    color = "cyan"
                else:
                    icon = "💿"
                    color = "green"
            else:
                icon = "🔌"
                color = "yellow"

            # Create compact usage pill + percentage
            percent = disk['percent']
            bar_length = 5
            filled = int(percent / 100 * bar_length)
            empty = bar_length - filled

            if percent > 85:
                bar_color = "red"
            elif percent > 70:
                bar_color = "yellow"
            elif percent > 50:
                bar_color = "green"
            else:
                bar_color = "blue"

            bar = "█" * filled + "░" * empty
            usage_display = f"[{bar_color}]{bar}[/{bar_color}] [{bar_color}]{percent:4.1f}%[/{bar_color}]"

            # Descriptive but sized mount display names
            mount_path = disk['mountpoint']
            if mount_path == '/':
                mount_display = 'System'
            elif 'ai-storage' in mount_path:
                mount_display = 'AI Storage'
            elif 'cold-storage' in mount_path:
                mount_display = 'Cold Storage'
            elif 'masstore' in mount_path:
                mount_display = 'Mass Storage'
            elif 'Crucial' in mount_path:
                mount_display = 'Crucial X10'
            else:
                mount_display = mount_path.split('/')[-1].title()[:12]

            drive_info = f"{icon} [{color}]{mount_display}[/{color}]"

            # Compact but readable size format
            if disk['total'] > 1024**4:  # TB
                size_info = f"{disk['used'] / (1024**4):.1f}/{disk['total'] / (1024**4):.1f}TB"
            else:  # GB
                size_info = f"{disk['used'] / (1024**3):.0f}/{disk['total'] / (1024**3):.0f}GB"

            table.add_row(drive_info, usage_display, size_info)

        return Panel(table, title="[bold cyan]💾 Storage Overview[/bold cyan]", border_style="cyan")

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

        # Create very compact card content
        card_content = f"""{icon} [{title_color}]{device_name}[/{title_color}]
📂 {mount_display}
{usage_bar} {percent:.0f}%
{used_size}/{total_size}"""

        return Panel(
            card_content,
            border_style=border_color,
            padding=(0, 0),
            width=16  # Very compact to fit 4 drives
        )
    
    def create_cpu_cores_panel(self, stats):
        """Create CPU cores panel as a 2-column horizontal bar layout"""
        if not stats:
            return Panel("Error loading CPU stats", title="CPU Cores", border_style="red")

        cores = stats['cpu_cores']
        bar_width = 5
        half = len(cores) // 2  # split into two columns

        def core_bar(usage):
            filled = max(int(usage / 100 * bar_width), 1 if usage > 0 else 0)
            color = "red" if usage > 80 else "yellow" if usage > 60 else "green" if usage > 30 else "blue"
            bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * (bar_width - filled)}[/dim]"
            pct = f"[{color}]{usage:3.0f}%[/{color}]"
            return bar, pct

        lines = []
        for i in range(half):
            left_usage  = cores[i]
            right_usage = cores[i + half] if (i + half) < len(cores) else 0

            lb, lp = core_bar(left_usage)
            rb, rp = core_bar(right_usage)

            left  = f"[dim]{i:>2}[/dim] {lb} {lp}"
            right = f"[dim]{i + half:>2}[/dim] {rb} {rp}"
            lines.append(f"{left}  [dim]│[/dim]  {right}")

        return Panel("\n".join(lines), title="[bold yellow]🎚️ CPU Cores[/bold yellow]", border_style="yellow")
    
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

    def create_gpu_panel(self):
        """Create enhanced GPU monitoring panel with process information"""
        gpu_info = self.get_gpu_info()
        gpu_processes = self.get_gpu_processes()

        if not gpu_info:
            return Panel(
                "[dim]NVIDIA GPU not detected\nor nvidia-smi not available[/dim]",
                title="[bold red]🎮 GPU Status[/bold red]",
                border_style="red"
            )

        # Create content for each GPU
        gpu_displays = []
        total_vram_used = 0
        total_vram_total = 0

        for gpu in gpu_info:
            # Calculate percentages
            vram_percent = (gpu['memory_used'] / gpu['memory_total']) * 100
            power_percent = (gpu['power_draw'] / gpu['power_limit']) * 100

            # Determine warning colors
            temp_color = "red" if gpu['temperature'] > 80 else "yellow" if gpu['temperature'] > 70 else "green"
            vram_color = "red" if vram_percent > 90 else "yellow" if vram_percent > 75 else "green"
            power_color = "red" if power_percent > 90 else "yellow" if power_percent > 75 else "green"
            util_color = "green" if gpu['utilization'] > 50 else "yellow" if gpu['utilization'] > 20 else "blue"

            # Create VRAM usage bar
            vram_bar_length = 16
            vram_filled = int(vram_percent / 100 * vram_bar_length)
            vram_empty = vram_bar_length - vram_filled
            vram_bar = "█" * vram_filled + "░" * vram_empty

            # Create utilization bar
            util_bar_length = 12
            util_filled = int(gpu['utilization'] / 100 * util_bar_length)
            util_empty = util_bar_length - util_filled
            util_bar = "█" * util_filled + "░" * util_empty

            # Format memory sizes
            vram_used_gb = gpu['memory_used'] / 1024
            vram_total_gb = gpu['memory_total'] / 1024

            # Create enhanced GPU display
            gpu_display = f"""🎮 [bold white]GPU {gpu['index']}: {gpu['name']}[/bold white]
┌─ [{temp_color}]{gpu['temperature']}°C[/{temp_color}] | [{power_color}]{gpu['power_draw']:.0f}W[/{power_color}] | [{util_color}]{gpu['utilization']}%[/{util_color}]
├─ Util: [{util_color}]{util_bar}[/{util_color}]
└─ VRAM: [{vram_color}]{vram_bar}[/{vram_color}] {vram_used_gb:.1f}GB"""

            gpu_displays.append(gpu_display)
            total_vram_used += gpu['memory_used']
            total_vram_total += gpu['memory_total']

        # Add GPU processes if any
        if gpu_processes:
            process_display = "\n🔧 [bold yellow]Active Processes:[/bold yellow]"
            for proc in gpu_processes[:3]:  # Show top 3 processes
                proc_mem_gb = proc['memory_used'] / 1024
                process_name = proc['name'][:12]  # Truncate long names
                process_display += f"\n  • {process_name}: {proc_mem_gb:.1f}GB"
        else:
            process_display = "\n🔧 [dim]No active GPU processes[/dim]"

        # Add total VRAM summary
        total_vram_percent = (total_vram_used / total_vram_total) * 100
        total_color = "red" if total_vram_percent > 90 else "yellow" if total_vram_percent > 75 else "green"
        total_used_gb = total_vram_used / 1024
        total_total_gb = total_vram_total / 1024

        total_display = f"\n💾 [bold {total_color}]Total: {total_used_gb:.1f}/{total_total_gb:.1f}GB[/bold {total_color}]"

        # Combine all displays
        content = "\n\n".join(gpu_displays) + process_display + total_display

        # Determine overall border color based on any warnings
        border_color = "red" if any(gpu['temperature'] > 80 or (gpu['memory_used']/gpu['memory_total']) > 0.9 for gpu in gpu_info) else "green"

        return Panel(content, title="[bold cyan]🎮 GPU Dashboard[/bold cyan]", border_style=border_color)

    def create_network_panel(self):
        """Create network panel with connectivity and traffic stats"""
        network_info = self.get_network_info()

        if not network_info:
            return Panel(
                "[dim]Network info unavailable[/dim]",
                title="[bold red]🌐 Network[/bold red]",
                border_style="red"
            )

        # Connectivity status
        lines = ["🌐 [bold white]Hosts:[/bold white]"]
        for name, status in network_info['connectivity'].items():
            icon = "✅" if status else "❌"
            short_name = name.split()[0]
            lines.append(f"  {icon} {short_name}")

        # Traffic totals
        def fmt_bytes(b):
            if b > 1024**3:
                return f"{b / 1024**3:.1f} GB"
            elif b > 1024**2:
                return f"{b / 1024**2:.0f} MB"
            else:
                return f"{b / 1024:.0f} KB"

        lines.append("")
        lines.append("📊 [bold white]Traffic:[/bold white]")
        lines.append(f"  [yellow]↑[/yellow] Sent  [white]{fmt_bytes(network_info['bytes_sent'])}[/white]")
        lines.append(f"  [cyan]↓[/cyan] Recv  [white]{fmt_bytes(network_info['bytes_recv'])}[/white]")
        lines.append(f"  [dim]Pkts: {network_info['packets_sent']:,}↑ {network_info['packets_recv']:,}↓[/dim]")

        # Active interfaces
        try:
            addrs = psutil.net_if_addrs()
            net_stats = psutil.net_if_stats()
            lines.append("")
            lines.append("🔗 [bold white]Interfaces:[/bold white]")
            for iface, stats_list in net_stats.items():
                if stats_list.isup and iface not in ('lo', 'docker0') and not iface.startswith(('veth', 'br-')):
                    speed = f"{stats_list.speed}Mb" if stats_list.speed > 0 else ""
                    # Get IP if available
                    ip = ""
                    if iface in addrs:
                        for addr in addrs[iface]:
                            if addr.family.name == 'AF_INET':
                                ip = addr.address
                                break
                    detail = f" {speed}" if speed else ""
                    lines.append(f"  [green]●[/green] {iface[:8]}{detail}")
                    if ip:
                        lines.append(f"    [dim]{ip}[/dim]")
        except Exception:
            pass

        all_connected = all(network_info['connectivity'].values())
        border_color = "green" if all_connected else "yellow"

        return Panel("\n".join(lines), title="[bold magenta]🌐 Network[/bold magenta]", border_style=border_color)

    def create_layout(self):
        """Create the enhanced main layout with GPU panel next to storage"""
        layout = Layout()

        # Split into header and body
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )

        # Split body into three rows for better organization
        layout["body"].split_column(
            Layout(name="top_row", ratio=2),
            Layout(name="middle_row", ratio=2),  # Storage + GPU row
            Layout(name="bottom_row", ratio=3)   # 3-column section
        )

        # Split top row into three columns (system info, resources, and animation)
        layout["top_row"].split_row(
            Layout(name="system_info"),
            Layout(name="resources"),
            Layout(name="animation", ratio=1)
        )

        # Split middle row into two panels: storage + GPU
        layout["middle_row"].split_row(
            Layout(name="storage", ratio=3),
            Layout(name="gpu", ratio=2)
        )

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
        layout["storage"].update(self.create_disk_panel(stats))
        layout["gpu"].update(self.create_gpu_panel())
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
