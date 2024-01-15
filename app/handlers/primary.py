from rich.console import Console

console = Console()


def robots_handler(args, url, content):
    urls = set()

    for line in content.splitlines():
        if (
            line.startswith("Disallow:") or line.startswith("Allow:")
        ) and "*" not in line:
            urls.add(line.split(": ")[-1].strip())

        if line.startswith("Sitemap:"):
            urls.add(line.split(": ")[-1].strip())

    urls = sorted(urls)
    for u in urls:
        console.print(f"   - {args.url}{u}")


def sitemap_handler(args, url, content):
    pass
