#!/usr/bin/env python3
import argparse
import requests
from rich.console import Console
from rich.table import Table
from rich import traceback
import hashlib

import app.const
from app.targets import TARGETS

console = Console(color_system="auto")

from app.html import get_html_info

# traceback
traceback.install(show_locals=False)

artifacts_found = 0

hashes = {}
hash_colors = ["red", "green", "yellow", "blue", "magenta", "cyan", "white"]


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
    """Check if a path exists on a site"""
    try:
        outpath = url + path
        r = requests.get(outpath)
        storeHash(outpath, r.content.decode("utf-8"))
        if r.status_code == 200:
            return outpath, True, r.content.decode("utf-8")
        else:
            return None, False, None
    except Exception as e:
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

    target_handler = custom_target["handler"]  # for processing all afterward
    files = custom_target["files"]  # if any of these exist, call the handler

    if type(files) is not dict:
        raise Exception(
            f"Expected dict for {current_target_name}-handled files list..."
        )

    for file in files.keys():
        for tested_path, result, url, content in processFiles(args.url, [file]):
            if args.verbose:
                console.print(
                    f" - {tested_path}, {'[link]'+url+'[/link]' if result else '[red]--[/red]'}"
                )

            if result:
                if not args.verbose:
                    # we've already printed if we're verbose
                    console.print(f" - {tested_path}, {'[green]'+url+'[/green]'}")
                artifacts_found += 1
                call_primary_handler = True

                # if this has a handler specified, call it
                if files[file] is not None and not args.no_handlers:
                    files[file](args, url, content)

    if call_primary_handler and target_handler is not None and not args.no_handlers:
        target_handler(args)

    pass


def main(args):
    global artifacts_found

    # fully quality args.url
    if not args.url.startswith("http"):
        args.url = "https://" + args.url

    console.rule(f"Quick stats for [bold]{args.url}[/bold]", characters="-")

    get_html_info(args)

    call_primary_handler = False

    for target in TARGETS.keys():
        current_target_name = target
        console.rule(f"## {target.upper()} ##", style="black bold", characters="-")

        # just a plain list of files
        if type(TARGETS[target]) is list:
            process_target_list(args, TARGETS[target], current_target_name)

        # a special handler block
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

    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        console.print("\n[yellow blink]ABORTED...[/yellow blink]")
        pass
