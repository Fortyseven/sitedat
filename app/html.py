"""
TODO: Add feature to highlight interesting headers
"""

import app.const as const

import requests
from rich.console import Console
from rich.table import Table
from rich import print
import re
import urllib3
import validators

from bs4 import BeautifulSoup, Comment

console = Console()
found_paths = set()
found_domains = set()


def _aggregate_link(link, parse_url):
    global console
    global found_paths

    IGNORED_EXTENSIONS = [".png", ".jpg", ".ico", ".jpeg"]

    parse_link = urllib3.util.url.parse_url(link)

    if parse_link.host and parse_url.host in parse_link.host:
        found_domains.add(parse_link.host)

    # console.print(parse_link)

    if link == "/" or link == "#" or link == "" or not link:
        return

    if link.startswith("/"):
        if parse_link.path:
            # strip file
            if parse_link.path.endswith(tuple(IGNORED_EXTENSIONS)):
                pth = parse_link.path.split("/")[:-1]
                found_paths.add("/".join(pth))

    if parse_link.host and parse_link.path and (parse_url.host in parse_link.host):
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
        console.rule("## Comments ##", characters="-", style="black bold")
        comment_entry = set()
        for c in comments:
            comment_entry.add(c.strip())

        for c in comment_entry:
            console.print(f"- [green]<!-- {c.strip()} -->[/green]")


def dump_headers(headers):
    console.rule("## Response Headers ##", characters="-", style="black bold")
    tab = Table(width=console.width)
    tab.add_column("Key", style="blue")
    tab.add_column("Value", style="cyan")

    for k, v in sorted(headers.items()):
        tab.add_row(k, v)

    console.print(tab)


def extract_urls(raw_html):
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    # url_pattern = re.compile(r'\"(https?://)?[^\s<>"]+\.[^\s<>"]+')
    urls = url_pattern.findall(raw_html)
    # trim
    urls = [url.strip() for url in urls]
    return urls


def dump_links_and_such(soup, args):
    parse_url = urllib3.util.url.parse_url(args.url)

    raw_html = soup.prettify()

    # find all valid URLs in the HTML

    urls = extract_urls(str(soup))

    # iterate urls and remove '/' from urls that end with '/'
    urls = [url[:-1] if url.endswith("/") else url for url in urls]

    # remove anything containing ".w3.org"
    urls = [url for url in urls if ".w3.org" not in url]

    if urls:
        console.rule("Found URLs", characters="#", style="red bold")

        urls = sorted(set(urls))

        ####

        js_urls = set()

        for url_js in iter(urls):
            if url_js.endswith(".js"):
                js_urls.add(url_js)
                urls = [x for x in urls if not x == url_js]

        if js_urls:
            console.rule("JAVASCRIPT", characters="-", style="black bold")
            for url in js_urls:
                console.print(f"  - {url}")

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
            console.rule("MEDIA", characters="-", style="black bold")
            for url in img_urls:
                console.print(f"  - {url}")

        ####
        if urls:
            console.rule("UNSORTED", characters="-", style="black bold")
            for url in urls:
                console.print(f"  - {url}")

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
        console.rule("## Found paths ##", characters="-", style="black bold")
        for host in sorted(found_paths):
            console.print(f"  - {args.url+host}")

    if found_domains:
        sorted(found_domains)
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

        dump_headers(result.headers)
        dump_meta(soup)
        dump_comments(soup)
        dump_links_and_such(soup, args)

    except Exception as e:
        console.print(f"Error: {e}")
        exit(1)
