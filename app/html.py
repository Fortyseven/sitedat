"""
TODO: Add feature to highlight interesting headers
"""

import app.const as const

import requests
from rich.console import Console
from rich.table import Table
from rich import print
import re
import urllib.parse
import validators

from bs4 import BeautifulSoup, Comment

console = Console()
found_paths = set()
found_domains = set()


def _aggregate_link(link, parse_url):
    global console
    global found_paths

    IGNORED_EXTENSIONS = [".png", ".jpg", ".ico", ".jpeg"]

    parse_link = urllib.parse.urlparse(link)

    if parse_link.hostname and parse_url.hostname in parse_link.hostname:
        found_domains.add(parse_link.hostname)

    # console.print(parse_link)

    if link == "/" or link == "#" or link == "" or not link:
        return

    if link.startswith("/"):
        if parse_link.path:
            # strip file
            if parse_link.path.endswith(tuple(IGNORED_EXTENSIONS)):
                pth = parse_link.path.split("/")[:-1]
                found_paths.add("/".join(pth))

    if (
        parse_link.hostname
        and parse_link.path
        and (parse_url.hostname in parse_link.hostname)
    ):
        # strip file
        if parse_link.path.endswith(tuple(IGNORED_EXTENSIONS)):
            pth = parse_link.path.split("/")[:-1]
            found_paths.add("/".join(pth))


def dump_meta(soup):
    meta = soup.find_all("meta")
    meta_props = {}
    if meta:
        for m in meta:
            if m.has_attr("property"):
                key = (":" + m["property"]).split(":")[-1]
                meta_props[key] = m.get("content", "--")
            elif m.has_attr("name"):
                key = (":" + m["name"]).split(":")[-1]
                meta_props[key] = m.get("content", "--")

    if meta_props:
        console.rule("## Meta Tags ##", characters="-", style="black bold")
        tab = Table(width=console.width)
        tab.add_column("Key", style="red")
        tab.add_column("Value", style="yellow")

        for k, v in sorted(meta_props.items()):
            tab.add_row(k, v)

        console.print(tab)


def dump_comments(soup):
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    if comments:
        console.print("")
        console.rule("## Comments ##", characters="-", style="black bold")
        comment_entry = set()
        for c in comments:
            comment_entry.add(c.strip())

        for c in comment_entry:
            console.print(f"- [green]<!-- {c.strip()} -->[/green]")


def dump_headers(headers):
    """
    Print response headers grouped by category, highlight important headers, and warn about missing/insecure headers.
    """
    from rich.text import Text
    from rich.panel import Panel

    # Define header categories and important headers
    security_headers = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Frame-Options": "deny",
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": None,  # Value varies
        "X-Permitted-Cross-Domain-Policies": "none",
        "Referrer-Policy": "no-referrer",
        "Clear-Site-Data": '"cache","cookies","storage"',
        "Cross-Origin-Embedder-Policy": "require-corp",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Permissions-Policy": None,  # Value varies
    }
    caching_headers = ["Cache-Control", "Pragma", "Expires"]
    cookie_headers = ["Set-Cookie", "Cookie"]
    cors_headers = [
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Credentials",
        "Access-Control-Expose-Headers",
        "Access-Control-Max-Age",
    ]
    other_headers = ["Content-Type", "Content-Disposition", "Server", "X-Powered-By"]

    # Group headers
    grouped = {
        "Security": {},
        "Caching": {},
        "Cookies": {},
        "CORS": {},
        "Other": {},
    }
    for k, v in headers.items():
        if k in security_headers:
            grouped["Security"][k] = v
        elif k in caching_headers:
            grouped["Caching"][k] = v
        elif k in cookie_headers:
            grouped["Cookies"][k] = v
        elif k in cors_headers:
            grouped["CORS"][k] = v
        else:
            grouped["Other"][k] = v

    # Check for missing/weak security headers
    warnings = []
    for k, recommended in security_headers.items():
        if k not in headers:
            warnings.append(f"[bold red]Missing security header:[/bold red] {k}")
        else:
            # Check for weak/insecure values
            val = headers[k]
            if k == "X-Frame-Options" and val.lower() not in ["deny", "sameorigin"]:
                warnings.append(
                    f"[bold yellow]Insecure value for X-Frame-Options:[/bold yellow] {val}"
                )
            if k == "X-Content-Type-Options" and val.lower() != "nosniff":
                warnings.append(
                    f"[bold yellow]Insecure value for X-Content-Type-Options:[/bold yellow] {val}"
                )
            if k == "Strict-Transport-Security" and "max-age" not in val:
                warnings.append(
                    f"[bold yellow]Missing max-age in Strict-Transport-Security:[/bold yellow] {val}"
                )
            if k == "Referrer-Policy" and val.lower() in [
                "unsafe-url",
                "no-referrer-when-downgrade",
            ]:
                warnings.append(
                    f"[bold yellow]Insecure value for Referrer-Policy:[/bold yellow] {val}"
                )
            if k == "Cache-Control" and "no-store" not in val:
                warnings.append(
                    f"[bold yellow]Cache-Control should include 'no-store' for sensitive data:[/bold yellow] {val}"
                )

    # Print warnings first
    if warnings:
        console.print("")
        console.rule(
            "[red bold]Header Warnings[/red bold]", characters="-", style="red bold"
        )
        for w in warnings:
            print(w)

    # Print grouped headers with highlights
    # Build whitelist of common headers
    whitelist = (
        set(security_headers.keys())
        | set(caching_headers)
        | set(cookie_headers)
        | set(cors_headers)
        | set(other_headers)
    )

    for group, items in grouped.items():
        if items:
            console.print("")
            console.rule(f"{group} Headers", characters="-", style="black bold")
            tab = Table(width=console.width)
            tab.add_column("Key", style="blue")
            tab.add_column("Value", style="cyan")
            for k, v in sorted(items.items()):
                if k in whitelist:
                    if group == "Security" and k in security_headers:
                        tab.add_row(
                            f"[bold green]{k}[/bold green]",
                            f"[bold yellow]{v}[/bold yellow]",
                        )
                    else:
                        tab.add_row(k, v)
                else:
                    tab.add_row(f"[white]{k}[/white]", v)
            console.print(tab)


def extract_urls(raw_html):
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    # url_pattern = re.compile(r'\"(https?://)?[^\s<>"]+\.[^\s<>"]+')
    urls = url_pattern.findall(raw_html)
    # trim
    urls = [url.strip() for url in urls]
    return urls


def dump_links_and_such(soup, args):
    parse_url = urllib.parse.urlparse(args.url)

    raw_html = soup.prettify()

    # find all valid URLs in the HTML

    urls = extract_urls(str(soup))

    # iterate urls and remove '/' from urls that end with '/'
    urls = [url[:-1] if url.endswith("/") else url for url in urls]

    # remove anything containing ".w3.org"
    urls = [url for url in urls if ".w3.org" not in url]

    if urls:
        console.print("")
        console.rule("Found URLs", characters="#", style="red bold")

        urls = sorted(set(urls))

        ####

        js_urls = set()

        for url_js in iter(urls):
            if url_js.endswith(".js"):
                js_urls.add(url_js)
                urls = [x for x in urls if not x == url_js]

        if js_urls:
            console.print("")
            console.rule("JAVASCRIPT", characters="-", style="black bold")
            for url in js_urls:
                console.print(f"  - {url}")

            console.print("")
            console.rule(
                "LOOKING INSIDE JAVASCRIPT", characters=">", style="black bold"
            )

            urls = set()
            for url in js_urls:
                try:
                    raw = requests.get(url).content.decode("utf-8")
                    urls = sorted(set(extract_urls(raw)))
                    print(f"  - [yellow bold]{url}[/yellow bold]")
                    for u in urls:
                        # use a library to parse the URL

                        if validators.url(u):
                            print(f"        - [yellow]{u}[/yellow]")
                except Exception as e:
                    console.print(f"Error: {e}")

            if urls:

                for url in urls:
                    console.print(f"  - {url}")

        ####

        img_urls = []
        for url_media in iter(urls):
            if url_media.lower().endswith(
                (
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".ico",
                    ".svg",
                    ".jpeg",
                    ".gif",
                    ".webp",
                    ".bmp",
                    ".tiff",
                    ".tif",
                    ".ico",
                    ".mp4",
                    ".mp3",
                    ".mov",
                    ".avi",
                    ".mkv",
                    ".flv",
                    ".webm",
                    ".ogg",
                    ".wav",
                    ".flac",
                    ".aac",
                    ".wma",
                    ".m4a",
                    ".opus",
                )
            ):
                # console.print(f"2: `{url}`")
                img_urls.append(url_media)
                # urls.remove(url)
                urls = [x for x in urls if not x == url_media]

        ####
        if img_urls:
            console.print("")
            console.rule("MEDIA", characters="-", style="black bold")
            for url in img_urls:
                console.print(f"  - {url}")

        ####
        if urls:
            console.print("")
            console.rule("UNSORTED", characters="-", style="black bold")
            for url in urls:
                console.print(f"  - {url}")

    console.print("")
    console.rule("MISC", characters="#", style="purple bold")

    # enumerate local/relative paths in href and src attributes
    for link in soup.find_all("a"):
        if link.has_attr("href"):
            _aggregate_link(link["href"], parse_url)

    # for host in soup.find_all("img"):
    #     if host.has_attr("src"):
    #         _aggregate_link(host["src"], parse_url)

    # for host in soup.find_all("script"):
    #     if host.has_attr("src"):
    #         _aggregate_link(host["src"], parse_url)

    # for host in soup.find_all("link"):
    #     if host.has_attr("href"):
    #         _aggregate_link(host["href"], parse_url)

    if found_paths:
        console.print("")
        console.rule("## Found paths ##", characters="-", style="black bold")
        for host in sorted(found_paths):
            console.print(f"  - {args.url+host}")

    if found_domains:
        sorted(found_domains)
        console.print("")
        console.rule("## Found domains ##", characters="-", style="black bold")
        for domain in sorted(found_domains):
            console.print(f"  - https://{domain}")


def get_html_info(args):
    global console

    ua = const.USER_AGENTS["firefox"]
    if args.ua_googlebot:
        ua = const.USER_AGENTS["googlebot"]

    try:
        result = requests.get(
            args.url,
            headers={
                "User-Agent": ua,
            },
        )

        raw_html = result.content.decode("utf-8")

        soup = BeautifulSoup(raw_html, "html.parser")

        title = soup.title

        if title:
            console.print(f"Title: `{title.string}`")

        dump_comments(soup)
        dump_headers(result.headers)
        dump_meta(soup)
        dump_links_and_such(soup, args)

    except Exception as e:
        console.print(f"Error: {e}")
        exit(1)
