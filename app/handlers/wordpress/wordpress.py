from rich.console import Console
import requests

from app.handlers.wordpress.wp_theme import wp_theme_handler
from app.handlers.wordpress.wp_xmlrpc import wp_xmlrpc_handler
from app.utils import checkFor

console = Console(color_system="auto")


def wp_handler(args, content):
    # search content for signals suggesting wordpress

    if not "wp-content" in content:
        if args.verbose:
            console.print(" - [red]No wp-content found in index content.[/red]")
            console.log(" - content:", content)
        return

    version = wp_version(args.url, content)
    console.print("")
    console.rule(
        f"[yellow]## [bold]WORDPRESS[/bold] ({version}) ##[/yellow]",
        style="yellow",
        characters="=",
    )

    wp_theme_handler(args, content, console)

    checkFor(args, console, f"{args.url}/wp-content/debug.log")
    checkFor(args, console, f"{args.url}/wp-json")
    if checkFor(args, console, f"{args.url}/xmlrpc.php", expected_code=405):
        wp_xmlrpc_handler(args, console)


def wp_version(url, page_content):
    import re
    import requests

    version = "unknown"

    feed_response = requests.get(f"{url}/feed")

    if feed_response.status_code != 200:
        feed_response = requests.get(f"{url}?feed=rss2")
        if feed_response.status_code != 200:
            return version

    feed_content = feed_response.content.decode("utf-8")

    # look for meta generator tag
    match = re.search(r"wordpress.org\/\?v=(.*)\<", feed_content)

    if match:
        version = match.group(1)

    return version
