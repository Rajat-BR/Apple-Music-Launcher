from rich.console import Console
from rich.text import Text

console = Console()

banner = r"""

 ▄▄▄       ██▓███   ██▓███   ██▓    ▓█████ 
▒████▄    ▓██░  ██▒▓██░  ██▒▓██▒    ▓█   ▀ 
▒██  ▀█▄  ▓██░ ██▓▒▓██░ ██▓▒▒██░    ▒███   
░██▄▄▄▄██ ▒██▄█▓▒ ▒▒██▄█▓▒ ▒▒██░    ▒▓█  ▄ 
 ▓█   ▓██▒▒██▒ ░  ░▒██▒ ░  ░░██████▒░▒████▒
 ▒▒   ▓▒█░▒▓▒░ ░  ░▒▓▒░ ░  ░░ ▒░▓  ░░░ ▒░ ░
  ▒   ▒▒ ░░▒ ░     ░▒ ░     ░ ░ ▒  ░ ░ ░  ░
  ░   ▒   ░░       ░░         ░ ░      ░   
      ░  ░                      ░  ░   ░  ░
                                           
 ███▄ ▄███▓ █    ██   ██████  ██▓ ▄████▄  
▓██▒▀█▀ ██▒ ██  ▓██▒▒██    ▒ ▓██▒▒██▀ ▀█  
▓██    ▓██░▓██  ▒██░░ ▓██▄   ▒██▒▒▓█    ▄ 
▒██    ▒██ ▓▓█  ░██░  ▒   ██▒░██░▒▓▓▄ ▄██▒
▒██▒   ░██▒▒▒█████▓ ▒██████▒▒░██░▒ ▓███▀ ░
░ ▒░   ░  ░░▒▓▒ ▒ ▒ ▒ ▒▓▒ ▒ ░░▓  ░ ░▒ ▒  ░
░  ░      ░░░▒░ ░ ░ ░ ░▒  ░ ░ ▒ ░  ░  ▒   
░      ░    ░░░ ░ ░ ░  ░  ░   ▒ ░░        
       ░      ░           ░   ░  ░ ░      
                                 ░ 

"""

def print_banner():
    text = Text()

    lines = banner.splitlines()
    total = len(lines)

    for i, line in enumerate(lines):
        t = i / max(total - 1, 1)
        r = int(165 + (175 - 165) * t)
        g = 0
        b = 0
        color = f"#{r:02x}{g:02x}{b:02x}"
        text.append(line + "\n", style=f"bold {color}")

    console.print(text)