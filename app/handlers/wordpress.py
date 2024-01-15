from rich.console import Console

console = Console()


def wp_handler(args):
    """WordPress handler"""
    wp_xmlrpc_handler(args, f"{args.url}/xmlrpc.php", None)


def wp_xmlrpc_handler(args, url, content):
    """WordPress XML-RPC handler"""
    # query methods from xmlrpc

    import xmlrpc.client

    try:
        server = xmlrpc.client.ServerProxy(url)
        console.print(f" - {url} system.listMethods(): ")
        print(" - ", server.system.listMethods())

    except Exception as e:
        console.print("Tried to query XML-RPC methods, but got an error: ", e)
