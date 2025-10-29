def wp_xmlrpc_handler(args, console):
    """WordPress XML-RPC handler"""
    # query methods from xmlrpc

    import xmlrpc.client

    # import requests

    # console.print("")
    xmlrpc_path = f"{args.url}/xmlrpc.php"

    # # check if xmlrpc.php is accessible
    # response = requests.get(xmlrpc_path, timeout=10)
    # if response.status_code != 405:
    #     if args.verbose:
    #         console.print(
    #             f" - [red]XML-RPC endpoint not found (status code: {response.status_code})[/red]"
    #         )
    #     return

    # has 405 ("post only")
    # console.print(f" - [green] endpoint found:[/green] {xmlrpc_path}")
    console.rule(
        f"XML-RPC: [bold cyan]{xmlrpc_path}[/bold cyan]",
        style="yellow dim",
        characters="-",
    )

    try:
        server = xmlrpc.client.ServerProxy(xmlrpc_path)
        console.print(f" - {xmlrpc_path} system.listMethods(): ")
        console.print("\n    - ", server.system.listMethods())

    except Exception as e:
        console.print("    - [red]Tried to query methods but failed.[/red]", e)
