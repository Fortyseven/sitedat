from rich.console import Console

console = Console()


def wp_handler(args):
    wp_theme_handler(args)
    console.print("\n")
    wp_xmlrpc_handler(args, f"{args.url}/xmlrpc.php", None)


def wp_theme_handler(args):
    # this will look inside the index for a reference to the current theme `/wp-content/themes/theme-name`
    theme = None
    import requests
    from bs4 import BeautifulSoup

    try:
        response = requests.get(args.url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
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


def wp_xmlrpc_handler(args, url, content):
    """WordPress XML-RPC handler"""
    # query methods from xmlrpc

    import xmlrpc.client

    try:
        server = xmlrpc.client.ServerProxy(url)
        console.print(f" - {url} system.listMethods(): ")
        console.print("\n - ", server.system.listMethods())

    except Exception as e:
        console.print("   - [red]Tried to query XML-RPC methods but failed.[/red]")
