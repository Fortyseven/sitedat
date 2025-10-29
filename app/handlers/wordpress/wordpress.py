from rich.console import Console
import requests

from app.handlers.wordpress.wp_theme import wp_theme_handler
from app.handlers.wordpress.wp_xmlrpc import wp_xmlrpc_handler

console = Console(color_system="auto")


def wp_handler(args, content):
    # search content for signals suggesting wordpress
    if "wp-content" in content:
        version = wp_version(args.url, content)
        console.print("")
        console.rule(
            f"[yellow]## [bold]WORDPRESS[/bold] ({version}) ##[/yellow]",
            style="yellow",
            characters="=",
        )

        wp_theme_handler(args, content, console)
        wp_debug_log(args)
        # console.print("\n")
        wp_xmlrpc_handler(args, console)
    else:
        if args.verbose:
            console.print(" - [red]No wp-content found in index content.[/red]")
            console.log(" - content:", content)


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


def wp_debug_log(args):
    # Check for /wp-content/debug.log

    debug_log_url = f"{args.url}/wp-content/debug.log"
    try:
        response = requests.get(debug_log_url, timeout=10)
        if response.status_code == 200:
            console.print(
                f"\n - [green bold]Found debug log:[/green bold] {debug_log_url}"
            )
            lines = response.text.splitlines()
            for line in lines[:10]:  # print first 10 lines
                console.print(f"      [yellow]{line}[/yellow]")
        else:
            if args.verbose:
                console.print(
                    f"\n - [red]Debug log not found (status code: {response.status_code})[/red]"
                )
    except Exception as e:
        console.print("   - [red]Error while trying to access debug log[/red]", e)
