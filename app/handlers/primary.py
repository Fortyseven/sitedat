from rich.console import Console

console = Console()


def robots_handler(args, url, content):
    urls = set()

    for line in content.splitlines():
        if line.startswith("Disallow:") or line.startswith(
            "Allow:"
        ):  # and "*" not in line:
            if line.endswith("*"):
                line = line.split(": ")[-1].strip()[:-1]
            if line.endswith("?"):
                line = line.split(": ")[-1].strip()[:-1]

            urls.add(line.split(": ")[-1].strip())

        if line.startswith("Sitemap:"):
            urls.add(line.split(": ")[-1].strip())

    urls = sorted(urls)

    console.print
    for u in urls:
        composed_url = u

        if u.startswith("/"):
            composed_url = args.url + u

        console.print(f"   - {composed_url}")


def sitemap_handler(args, url, content):
    pass
