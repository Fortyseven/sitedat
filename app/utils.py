import requests


def checkFor(args, console, path: str, expected_code=200) -> bool:
    response = requests.head(path, timeout=10)

    if response.status_code != expected_code:
        if args.verbose:
            console.print(f"- [red]{path}:[/red] {response.status_code}")
        return False

    content_length = ""
    size = None

    if "Content-Length" in response.headers:
        size = int(response.headers["Content-Length"]) / 1024

    if size:
        content_length = f"{size:.2f} KB"

    console.print(f"- [green]found {content_length}:[/green] {path}")

    return True
