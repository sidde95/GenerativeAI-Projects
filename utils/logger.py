"""Logging Utility"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from datetime import datetime
import logging

console = Console()

class AgentLogger:
    """Logger for agent execution with rich formatting"""
    
    @staticmethod
    def log_header(title: str, subtitle: str = ""):
        """Log application header"""
        content = f"[bold blue]{title}[/bold blue]"
        if subtitle:
            content += f"\n{subtitle}"
        
        console.print(Panel.fit(
            content,
            border_style="blue",
            padding=(1, 2)
        ))
    
    @staticmethod
    def log_run_id(run_id: str):
        """Log run ID"""
        console.print(f"\n[green]✓[/green] Run ID: [bold]{run_id}[/bold]")
    
    @staticmethod
    def log_agent_start(agent_name: str):
        """Log agent execution start"""
        console.print(f"\n[cyan]▶[/cyan] [{agent_name.upper()}] Starting execution...")
    
    @staticmethod
    def log_agent_detail(agent_name: str, key: str, value: str):
        """Log agent execution detail"""
        console.print(f"  ├─ {key}: {value}")
    
    @staticmethod
    def log_agent_success(agent_name: str, duration: float):
        """Log agent execution success"""
        console.print(f"  └─ Status: [green]SUCCESS[/green] ({duration:.2f}s)")
    
    @staticmethod
    def log_agent_error(agent_name: str, error: str):
        """Log agent execution error"""
        console.print(f"  └─ Status: [red]FAILED[/red] - {error}")
    
    @staticmethod
    def log_info(message: str):
        """Log info message"""
        console.print(f"[green]✓[/green] {message}")
    
    @staticmethod
    def log_warning(message: str):
        """Log warning message"""
        console.print(f"[yellow]⚠[/yellow] {message}")
    
    @staticmethod
    def log_error(message: str):
        """Log error message"""
        console.print(f"[red]✗[/red] {message}")
    
    @staticmethod
    def log_table(title: str, data: dict):
        """Log data as a formatted table"""
        table = Table(title=title, box=box.ROUNDED)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            table.add_row(str(key), str(value))
        
        console.print(table)
    
    @staticmethod
    def log_completion(run_id: str, duration: float):
        """Log execution completion"""
        console.print(
            f"\n[bold green]✅ Execution Complete[/bold green] "
            f"(Run ID: {run_id}, Duration: {duration:.2f}s)"
        )

# Global logger instance
logger = AgentLogger()
