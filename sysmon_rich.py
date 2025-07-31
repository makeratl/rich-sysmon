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

class RichSystemMonitor:
    def __init__(self):
        self.console = Console()
        
    def get_system_stats(self):
        """Get current system statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_cores = psutil.cpu_percent(interval=0.1, percpu=True)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_cores': cpu_cores,
                'memory': memory,
                'disk': disk,
                'network': network,
                'uptime': uptime,
                'hostname': platform.node(),
                'system': platform.system(),
                'load_avg': os.getloadavg()
            }
        except Exception as e:
            return None
    
    def get_top_processes(self, count=8):
        """Get top processes by memory usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    if proc.info['memory_percent'] > 0.1:
                        processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:count]
        except:
            return []
    
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
        """Create system information panel"""
        if not stats:
            return Panel("Error loading system stats", title="System Info", border_style="red")
            
        uptime_str = f"{stats['uptime'].days}d {stats['uptime'].seconds//3600}h {(stats['uptime'].seconds//60)%60}m"
        
        info_text = f"""[bold cyan]Hostname:[/bold cyan] {stats['hostname']}
[bold cyan]System:[/bold cyan] {stats['system']} {platform.release()}
[bold cyan]CPU Cores:[/bold cyan] {len(stats['cpu_cores'])}
[bold cyan]Uptime:[/bold cyan] {uptime_str}
[bold cyan]Memory Total:[/bold cyan] {stats['memory'].total / (1024**3):.1f} GB
[bold cyan]Load Average:[/bold cyan] {stats['load_avg'][0]:.2f}, {stats['load_avg'][1]:.2f}, {stats['load_avg'][2]:.2f}"""
        
        return Panel(info_text, title="[bold blue]System Information[/bold blue]", border_style="blue")
    
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
        table.add_row("Memory", f"{stats['memory'].percent:.1f}%", mem_bar)
        
        # Disk
        disk_bar = self.create_progress_bar(stats['disk'].percent)
        table.add_row("Disk", f"{stats['disk'].percent:.1f}%", disk_bar)
        
        # Network (show totals)
        net_sent = stats['network'].bytes_sent / (1024**2)  # MB
        net_recv = stats['network'].bytes_recv / (1024**2)  # MB
        table.add_row("Net Sent", f"{net_sent:.1f} MB", "")
        table.add_row("Net Recv", f"{net_recv:.1f} MB", "")
        
        return Panel(table, title="[bold green]Resource Usage[/bold green]", border_style="green")
    
    def create_cpu_cores_panel(self, stats):
        """Create CPU cores panel"""
        if not stats:
            return Panel("Error loading CPU stats", title="CPU Cores", border_style="red")
            
        cores_text = ""
        for i, usage in enumerate(stats['cpu_cores']):
            color = "red" if usage > 80 else "yellow" if usage > 60 else "green"
            bar_length = int(usage / 5)  # Scale to 20 chars
            bar = "█" * bar_length + "░" * (20 - bar_length)
            cores_text += f"Core {i:2d}: [{color}]{bar}[/{color}] {usage:5.1f}%\n"
        
        return Panel(cores_text.rstrip(), title="[bold yellow]CPU Cores[/bold yellow]", border_style="yellow")
    
    def create_processes_panel(self, processes):
        """Create top processes panel"""
        table = Table(show_header=True, header_style="bold red", box=box.SIMPLE)
        table.add_column("PID", style="cyan", width=8)
        table.add_column("Name", style="white", width=16)
        table.add_column("CPU%", style="yellow", width=8)
        table.add_column("MEM%", style="green", width=8)
        
        for proc in processes:
            table.add_row(
                str(proc['pid']),
                proc['name'][:14],
                f"{proc['cpu_percent']:.1f}",
                f"{proc['memory_percent']:.1f}"
            )
        
        return Panel(table, title="[bold red]Top Processes[/bold red]", border_style="red")
    
    def create_layout(self):
        """Create the main layout"""
        layout = Layout()
        
        # Split into header and body
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        
        # Split body into two rows
        layout["body"].split_column(
            Layout(name="top_row"),
            Layout(name="bottom_row")
        )
        
        # Split top row into two columns
        layout["top_row"].split_row(
            Layout(name="system_info"),
            Layout(name="resources")
        )
        
        # Split bottom row into two columns
        layout["bottom_row"].split_row(
            Layout(name="cpu_cores"),
            Layout(name="processes")
        )
        
        return layout
    
    def update_layout(self, layout):
        """Update layout with current data"""
        stats = self.get_system_stats()
        processes = self.get_top_processes()
        
        # Header
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header_text = Text(f"Rich System Monitor - {current_time}", style="bold white on blue")
        layout["header"].update(Align.center(header_text))
        
        # Update panels
        layout["system_info"].update(self.create_system_info_panel(stats))
        layout["resources"].update(self.create_resource_panel(stats))
        layout["cpu_cores"].update(self.create_cpu_cores_panel(stats))
        layout["processes"].update(self.create_processes_panel(processes))
    
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
