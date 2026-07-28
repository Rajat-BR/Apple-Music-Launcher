from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from banner import print_banner

console = Console()


def print_menu():
    menu = Text()

    menu.append("  [1] ", style="bold #B00000")
    menu.append("Launch Apple Music\n\n", style="white")

    menu.append("  [2] ", style="bold #B00000")
    menu.append("Refresh Login\n\n", style="white")

    menu.append("  [3] ", style="bold #B00000")
    menu.append("Exit", style="white")

    panel = Panel(
        menu,
        title="[bold #A50000]Select an option[/bold #A50000]",
        border_style="#700000",
        padding=(1, 2),
        expand=True,
        width=50
    )

    console.print()
    console.print(Align.center(panel))

def get_choice():
    console.print()
    console.print("[bold #B00000]Apple Music[/bold #B00000] >", end=" ")
    return input()