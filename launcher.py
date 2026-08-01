import sys

from getpass import getpass
from rich.console import Console

from banner import print_banner
from menu import print_menu, get_choice
from launcher_backend import load_config, launch, refresh_login, LauncherError

console = Console()

try:
    load_config()
except LauncherError as e:
    console.print(f"\n[bold red]{e}[/bold red]\n")
    sys.exit(1)

# ==============================================================
#                    Terminal Interface
# ==============================================================

def main():
    while True:

        print_banner()
        print_menu()
        choice = get_choice()

        if choice == 1:
            try:
                launch()
            except LauncherError as e:
                console.print(f"\n[bold red]{e}[/bold red]\n")
                sys.exit(1)

            console.print("\n[bold green]GUI launched successfully.[/bold green]")
            sys.exit(0)

        elif choice == 2:
            print()
            email = input("Apple ID: ")
            password = getpass("Password: ")

            try:
                refresh_login(email, password)
            except LauncherError as e:
                console.print(f"\n[bold red]{e}[/bold red]\n")
                sys.exit(1)

            console.print(
                "\n[bold green]Returning to main menu...[/bold green]\n"
            )
            input("Press Enter to continue...")

        elif choice == 3:
            console.print("\n[bold #B00000]Goodbye![/bold #B00000]")
            sys.exit(0)

        else:
            console.print("\n[bold red]Invalid option![/bold red]\n")
            input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        console.print("\n[bold #B00000]Interrupted. Goodbye![/bold #B00000]")
        sys.exit(0)