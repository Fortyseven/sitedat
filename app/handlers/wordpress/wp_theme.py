import requests
from app.utils import checkFor
from bs4 import BeautifulSoup
import app.const as const


def wp_theme_handler(args, page_content, console):
    theme = None

    try:
        soup = BeautifulSoup(page_content, "html.parser")

        for link in soup.find_all("link", href=True):
            href = link["href"]
            if "/wp-content/themes/" in href:
                theme = href.split("/wp-content/themes/")[1].split("/")[0]
                console.rule(
                    f"theme: [bold cyan]{theme}[/bold cyan]",
                    style="yellow dim",
                    characters=const.CHAR_H2,
                )

    except Exception as e:
        console.print("   - [red]Error while trying to find theme[/red]", e)

    if theme:
        theme_base = f"{args.url}/wp-content/themes/{theme}"
        if checkFor(args, console, f"{theme_base}/style.css"):
            dumpStyleCSS(theme_base, console)
        checkFor(args, console, f"{theme_base}/theme.json")
        checkFor(args, console, f"{theme_base}/package.json")
        checkFor(args, console, f"{theme_base}/readme.txt")
        checkFor(args, console, f"{theme_base}/README.txt")
        checkFor(args, console, f"{theme_base}/README.md")
        checkFor(args, console, f"{theme_base}/functions.bak")
        checkFor(args, console, f"{theme_base}/functions.bkp")
        checkFor(args, console, f"{theme_base}/functions.php.bak")
        checkFor(args, console, f"{theme_base}/functions.php.old")
        checkFor(args, console, f"{theme_base}/composer.json")
        checkFor(args, console, f"{theme_base}/yarn.lock")

    else:
        console.print("- [red]No theme reference detected?![/red]\n")


def dumpStyleCSS(theme_base, console):
    response = requests.get(theme_base + "/style.css", timeout=10)
    content = response.text
    start = content.find("/*")
    end = content.find("*/", start)
    if start != -1 and end != -1:
        style_content = content[start : end + 2].strip()
        for line in style_content.splitlines():
            console.print(f"      [green bold]{line.strip()}[/green bold]")
