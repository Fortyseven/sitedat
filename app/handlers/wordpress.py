from rich.console import Console

console = Console(color_system="auto")


def wp_handler(args, content):
    # search content for signals suggesting wordpress
    if "wp-content" in content:
        version = wp_version(args.url, content)
        console.print("")
        console.rule(f"## WORDPRESS ({version}) ##", style="black bold", characters="-")
    wp_theme_handler(args, content)
    console.print("\n")
    wp_xmlrpc_handler(args, f"{args.url}/xmlrpc.php")


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


def wp_theme_handler(args, page_content):
    # this will look inside the index for a reference to the current theme `/wp-content/themes/theme-name`
    theme = None
    import requests
    from bs4 import BeautifulSoup

    try:
        soup = BeautifulSoup(page_content, "html.parser")
        for link in soup.find_all("link", href=True):
            href = link["href"]
            if "/wp-content/themes/" in href:
                theme = href.split("/wp-content/themes/")[1].split("/")[0]
                console.print(
                    f"\n - [green bold]Found WordPress theme:[/green bold] {theme}"
                )
                stylescss = f"{args.url}/wp-content/themes/{theme}/style.css"
                styles_response = requests.get(stylescss, timeout=10)
                if styles_response.status_code == 200:
                    console.print(
                        f"   - [blue]Style.css found (size: {len(styles_response.content)} bytes):[/blue] {stylescss}"
                    )
                    # extract content between /* and */
                    content = styles_response.text
                    start = content.find("/*")
                    end = content.find("*/", start)
                    if start != -1 and end != -1:
                        style_content = content[start + 2 : end].strip()
                        for line in style_content.splitlines():
                            console.print(f"      [green]{line.strip()}[/green]")
                else:
                    console.print(f"   - [red]Style.css not found:[/red] {stylescss}")
                return
        console.print("   - [red]No WordPress theme detected?[/red]")
    except Exception as e:
        console.print("   - [red]Error while trying to find WordPress theme[/red]", e)


def wp_xmlrpc_handler(args, url):
    """WordPress XML-RPC handler"""
    # query methods from xmlrpc

    import xmlrpc.client

    try:
        server = xmlrpc.client.ServerProxy(url)
        console.print(f" - {url} system.listMethods(): ")
        console.print("\n - ", server.system.listMethods())

    except Exception as e:
        console.print("   - [red]Tried to query XML-RPC methods but failed.[/red]")
