#!/usr/bin/env python3
import argparse
import requests
from rich.console import Console
from rich.table import Table
from rich import traceback
import hashlib

import app.const
from app.targets import TARGETS
from app.cloudflare import is_cloudflare_challenge, try_cloudflare_bypass

console = Console(color_system="auto")

from app.html import get_html_info

# traceback
traceback.install(show_locals=False)

artifacts_found = 0

hashes = {}
hash_colors = ["red", "green", "yellow", "blue", "magenta", "cyan", "white"]

index_content = None
session = None  # requests session reused for all HTTP calls

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
}


def storeHash(url, content):
    global hashes

    hashes[url] = hashlib.md5(content.encode("utf-8")).hexdigest()


def getStoredHash(url):
    return hashes.get(url, None)


def getDecoratedStoredHash(url):

    hash = getStoredHash(url)

    # convert hash into an integer
    hash_id = int(hash, 16) if hash else 0
    hash_color = hash_colors[hash_id % len(hash_colors)]

    if not hash:
        return "[red]<?????> [/red] "

    return f"[{hash_color}]<{hash[:5]}>[/{hash_color}] |"


def checkPathExist(url, path):
    """Check if a path exists on a site using the shared session."""
    global session
    try:
        outpath = url + path
        r = session.get(outpath, timeout=15)
        # best effort decode
        encoding = r.encoding or "utf-8"
        text = r.content.decode(encoding, errors="replace")
        storeHash(outpath, text)
        if r.status_code == 200:
            return outpath, True, text
        else:
            return None, False, None
    except Exception:
        return None, False, None


def processFiles(base_url, targets):
    for test_file in targets:
        result_url, result, content = checkPathExist(base_url, test_file)
        yield test_file, result, result_url if result else "--", content


def process_target_list(args, targets, current_target_name):
    global artifacts_found

    with console.status(current_target_name, spinner="earth"):
        for tested_path, result, url, content in processFiles(args.url, targets):
            if not args.verbose and not result:
                continue

            if result:
                artifacts_found += 1

            decorated_hash = getDecoratedStoredHash(url)

            console.print(
                f" - {decorated_hash} {tested_path}, [green link]{url}[/green link]"
                if result
                else "[red]--[/red]"
            )


def process_target_custom(args, custom_target, current_target_name):
    global artifacts_found

    call_primary_handler = False

    if "files" in custom_target:
        files = custom_target["files"]  # if any of these exist, call the handler
        if type(files) is not dict:
            raise Exception(
                f"Expected dict for {current_target_name}-handled files list..."
            )
        for file in files.keys():
            for tested_path, result, url, content in processFiles(args.url, [file]):
                if args.verbose:
                    if result and url:
                        console.print(f" - {tested_path}, [link]{url}[/link]")
                    else:
                        console.print(f" - {tested_path}, [red]--[/red]")

                if result:
                    if not args.verbose:
                        # we've already printed if we're verbose
                        if url:
                            console.print(f" - {tested_path}, [green]{url}[/green]")
                        else:
                            console.print(f" - {tested_path}, [red]--[/red]")
                    artifacts_found += 1
                    call_primary_handler = True

                    # if this has a handler specified, call it
                    if files[file] is not None and not args.no_handlers:
                        files[file](args, url, content)

    if not args.no_handlers and "handler" in custom_target and custom_target["handler"]:
        custom_target["handler"](args, index_content)
    pass


def main(args):
    global artifacts_found, index_content, session

    # fully quality args.url
    if not args.url.startswith("http"):
        args.url = "https://" + args.url

    # Strip trailing slash from URL if present
    if args.url.endswith("/"):
        args.url = args.url[:-1]

    console.rule(f"Quick stats for [bold]{args.url}[/bold]", characters="-")

    # Prepare reusable session
    session = requests.Session()
    session.headers.update(HEADERS)
    if args.ua_googlebot:
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        )

    print("Fetching index content...", args.url)
    resp = session.get(args.url, timeout=20)
    index_encoding = resp.encoding or "utf-8"
    index_content = resp.content.decode(index_encoding, errors="replace")

    if is_cloudflare_challenge(resp.status_code, index_content):
        if getattr(args, "cf_bypass", False):
            console.print(
                "[yellow]Cloudflare/WAF challenge detected; attempting bypass (--cf-bypass).[/yellow]"
            )
            success, bypass_status, bypass_body = try_cloudflare_bypass(
                args.url, session.headers
            )
            if success:
                console.print("[green]Bypass successful.[/green]")
                index_content = bypass_body
            else:
                if bypass_status == 0:
                    console.print(
                        "[red]cloudscraper not installed or error occurred. Install with: pip install cloudscraper[/red]"
                    )
                else:
                    console.print(
                        "[red]Bypass attempt failed; still challenged or received error status. Halting.[/red]"
                    )
                return
        else:
            console.print(
                "[red]Cloudflare/WAF challenge (403) detected. Use --cf-bypass to attempt a bypass. Halting.[/red]"
            )
            return

    # Only call get_html_info if no --target is specified
    if not getattr(args, "target", None):
        get_html_info(args)

    call_primary_handler = False

    if getattr(args, "target", None):
        target_input = args.target.lower()
        # Find matching key in TARGETS (case-insensitive)
        matched_target = None
        for key in TARGETS.keys():
            if key.lower() == target_input:
                matched_target = key
                break
        if not matched_target:
            console.print(f"[red]Target '{args.target}' not found in TARGETS.[/red]")
            return
        current_target_name = matched_target
        if type(TARGETS[matched_target]) is list:
            console.print("")
            console.rule(
                f"## {matched_target.upper()} ##", style="black bold", characters="-"
            )
            process_target_list(args, TARGETS[matched_target], current_target_name)
        elif type(TARGETS[matched_target]) is dict:
            process_target_custom(args, TARGETS[matched_target], current_target_name)
        else:
            raise Exception(f"Unknown target type for {matched_target}...")
    else:
        for target in TARGETS.keys():
            current_target_name = target
            if type(TARGETS[target]) is list:
                console.print("")
                console.rule(
                    f"## {target.upper()} ##", style="black bold", characters="-"
                )
                process_target_list(args, TARGETS[target], current_target_name)
            elif type(TARGETS[target]) is dict:
                process_target_custom(args, TARGETS[target], current_target_name)
            else:
                raise Exception(f"Unknown target type for {target}...")
    console.print(f"\nFound [bold]{artifacts_found}[/bold] artifacts.")


if __name__ == "__main__":
    # get arguments, require a URL
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="The URL of the site you want to parse")
    parser.add_argument(
        "--print-content",
        help="Print the content of the file if it exists",
        action="store_true",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true",
    )

    parser.add_argument(
        "-nh",
        "--no-handlers",
        help="Don't run any handlers",
        action="store_true",
    )

    parser.add_argument(
        "--ua-googlebot",
        help="Use googlebot for user agent",
        action="store_true",
    )

    parser.add_argument(
        "--target",
        help="Only run the specified target (case-sensitive, e.g. 'WordPress')",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--cf-bypass",
        help="Attempt to bypass Cloudflare JS challenge using cloudscraper",
        action="store_true",
    )

    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        console.print("\n[yellow blink]ABORTED...[/yellow blink]")
        pass
