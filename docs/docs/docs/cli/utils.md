---
slug: /cli/utils
title: CLI Utilities
description: Utility functions and shared components for the midil-kit CLI
---

# CLI Utilities

The CLI utilities provide shared functionality and components used across different CLI commands, including console output, logo display, and common helper functions.

## Overview

The utilities module includes:
- **Console Management**: Rich console output and formatting
- **Logo Display**: ASCII art logo with styling
- **Shared Components**: Common functionality across commands
- **Helper Functions**: Utility functions for CLI operations

## Console Management

### Rich Console Integration

The CLI uses the Rich library for beautiful console output:

```python
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from pyfiglet import Figlet

console = Console()
```

**Purpose**: Provides consistent, styled console output across all CLI commands.

**Features**:
- Colored text output
- Formatted panels and boxes
- Progress indicators
- Error and success styling

### Console Output Examples

```python
# Success message
console.print("✅ Project scaffolded successfully", style="green")

# Error message
console.print("❌ Failed to create project", style="red")

# Warning message
console.print("⚠️  Warning: API settings not configured", style="yellow")

# Info message
console.print("ℹ️  Running tests...", style="blue")

# Dimmed text
console.print("Running: pytest --cov=midil", style="dim")
```

## Logo Display

### print_logo() Function

```python
def print_logo() -> None:
    width = console.size.width - 4
    figlet = Figlet(font="standard")
    ascii_art = figlet.renderText("midil-kit")
    
    text = Text(ascii_art, style="bold magenta", justify="center")
    panel = Panel(
        text,
        title="⚡ Ingenuity ⚡",
        subtitle="by midil.io",
        border_style="magenta",
        padding=(1, 4),
        width=width,
        expand=True,
    )
    console.print(panel)
```

**Purpose**: Displays the midil-kit ASCII art logo with styling.

**Features**:
- Responsive width based on terminal size
- Centered text alignment
- Colored and styled output
- Panel with title and subtitle

### Logo Output

```
┌─────────────────────────────────────────────────────────┐
│                    ⚡ Ingenuity ⚡                      │
│                        by midil.io                     │
│                                                         │
│  ███╗   ███╗██╗██████╗ ██╗██╗         ██╗  ██╗██╗████████╗ │
│  ████╗ ████║██║██╔══██╗██║██║         ██║ ██╔╝██║╚══██╔══╝ │
│  ██╔████╔██║██║██║  ██║██║██║         █████╔╝ ██║   ██║   │
│  ██║╚██╔╝██║██║██║  ██║██║██║         ██╔═██╗ ██║   ██║   │
│  ██║ ╚═╝ ██║██║██████╔╝██║███████╗    ██║  ██╗██║   ██║   │
│  ╚═╝     ╚═╝╚═╝╚═════╝ ╚═╝╚══════╝    ╚═╝  ╚═╝╚═╝   ╚═╝   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Shared Components

### Common Console

```python
# In commands/_common.py
from rich.console import Console

console = Console()

__all__ = ["console"]
```

**Purpose**: Provides a shared console instance across all command modules.

**Usage**: Import and use in command implementations for consistent output.

### Console Styling

The CLI uses consistent styling patterns:

```python
# Success styling
style="green"

# Error styling
style="red"

# Warning styling
style="yellow"

# Info styling
style="blue"

# Dimmed styling
style="dim"

# Bold styling
style="bold"

# Colored text
style="bold magenta"
style="bold cyan"
style="bold white"
```

## Helper Functions

### Text Formatting

```python
# Bold text
console.print(f"[bold]{text}[/bold]")

# Colored text
console.print(f"[green]{text}[/green]")

# Combined styling
console.print(f"[bold green]{text}[/bold green]")

# Justified text
console.print(text, justify="center")
```

### Panel Creation

```python
# Create styled panel
panel = Panel(
    content,
    title="Title",
    subtitle="Subtitle",
    border_style="magenta",
    padding=(1, 4),
    width=width,
    expand=True,
)
console.print(panel)
```

### Progress Indicators

```python
# Simple progress message
console.print("🔄 Processing...", style="blue")

# Success indicator
console.print("✅ Complete", style="green")

# Error indicator
console.print("❌ Failed", style="red")
```

## Integration Examples

### Command Integration

```python
# In commands/init.py
from midil.cli.commands._common import console
from midil.cli.utils import print_logo

@click.command("init")
def init_command(name, type):
    print_logo()
    console.print(f"🚀 Scaffolding {type} project: [bold]{name}[/bold]", style="blue")
    # ... rest of command
```

### Error Handling

```python
# In commands/test.py
from midil.cli.commands._common import console

def test_command(coverage, file, verbose, html_cov):
    try:
        # Test execution
        console.print("✅ All tests passed!", style="green")
    except Exception as e:
        console.print(f"❌ Error running tests: {e}", style="red")
        sys.exit(1)
```

### Status Messages

```python
# In commands/launch.py
from midil.cli.commands._common import console

def launch_command(port, host, reload):
    console.print("🛸 Launching service...", style="bold blue")
    console.print(f"   on [bold yellow]http://{host}:{port}[/bold yellow]")
    # ... launch logic
```

## Best Practices

### Consistent Styling

- Use consistent color schemes across commands
- Apply appropriate styling for different message types
- Maintain visual hierarchy with bold and dim text

### Error Messages

- Use red styling for errors
- Provide clear, actionable error messages
- Include context when possible

### Success Messages

- Use green styling for success
- Provide confirmation of completed actions
- Include relevant details

### Info Messages

- Use blue styling for informational messages
- Provide helpful context
- Use dim styling for secondary information

## Troubleshooting

### Common Issues

1. **Console Not Displaying Colors**
   - Check terminal color support
   - Verify Rich library installation
   - Test with simple color output

2. **Logo Display Issues**
   - Check terminal width
   - Verify pyfiglet installation
   - Test with different terminal sizes

3. **Text Formatting Problems**
   - Check Rich syntax
   - Verify console instance
   - Test with simple text first

### Debug Mode

```python
# Test console output
console.print("Test message", style="green")

# Test logo display
print_logo()

# Test panel creation
panel = Panel("Test content", title="Test")
console.print(panel)
```

## Advanced Usage

### Custom Styling

```python
# Create custom style
custom_style = Style(color="cyan", bold=True)
console.print("Custom styled text", style=custom_style)

# Use multiple styles
console.print("[bold green]Success[/bold green] with [dim]details[/dim]")
```

### Dynamic Content

```python
# Dynamic width calculation
width = console.size.width - 4
panel = Panel(content, width=width)

# Responsive text
text = Text(content, justify="center")
console.print(text)
```

### Progress Tracking

```python
# Simple progress
console.print("🔄 Step 1/3: Initializing...", style="blue")
console.print("🔄 Step 2/3: Processing...", style="blue")
console.print("✅ Step 3/3: Complete!", style="green")
```

<!-- source: midil-kit-main/midil/cli/utils.py -->
<!-- source: midil-kit-main/midil/cli/commands/_common.py -->
