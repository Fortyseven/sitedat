#!/usr/bin/env python3
import argparse
import requests
from rich.console import Console
from rich.table import Table
from rich import traceback

import app.const
from app.targets import TARGETS

console = Console()

from app.html import get_html_info

# traceback
traceback.install(show_locals=True)

artifacts_found = 0


def checkPathExist(url, path):
    """Check if a path exists on a site"""
    try:
        outpath = url + path
        r = requests.get(outpath)
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


def outputStandardResults(args, base_url, out_path, result, content):
    if result:
        artifacts_found += 1

    if not args.verbose and not result:
        return

    console.print(
        f" - {out_path}, {'[green]'+{base_url}+'[/green]' if result else '[red]--[/red]'}"
    )

    if result and content and args.print_content:
        console.print(f"\n```\n{content}\n```\n`")


def main(args):
    global artifacts_found

    # fully quality args.url
    if not args.url.startswith("http"):
        args.url = "https://" + args.url

    console.print(f"\nQuick stats for [bold]{args.url}[/bold]:")

    console.print("=" * 50)

    get_html_info(args)

    console.print("-" * 50)

    call_primary_handler = False

    for target in TARGETS.keys():
        console.print(f"\n## [bold]{target.upper()}[/bold] ##")

        # just a plain list of files
        if type(TARGETS[target]) is list:
            for tested_path, result, url, content in processFiles(
                args.url, TARGETS[target]
            ):
                if not args.verbose and not result:
                    continue

                if result:
                    artifacts_found += 1

                console.print(
                    f" - {tested_path}, {'[green]'+url+'[/green]' if result else '[red]--[/red]'}"
                )

        # a special handler block
        elif type(TARGETS[target]) is dict:
            target_handler = TARGETS[target]["handler"]  # for processing all afterward
            files = TARGETS[target]["files"]  # if any of these exist, call the handler

            if type(files) is not dict:
                raise Exception(f"Expected dict for {target} handled files list...")

            for file in files.keys():
                for tested_path, result, url, content in processFiles(args.url, [file]):
                    if args.verbose:
                        console.print(
                            f" - {tested_path}, {'[green]'+url+'[/green]' if result else '[red]--[/red]'}"
                        )

                    if result:
                        if not args.verbose:
                            # we've already printed if we're verbose
                            console.print(
                                f" - {tested_path}, {'[green]'+url+'[/green]'}"
                            )
                        artifacts_found += 1
                        call_primary_handler = True

                        # if this has a handler specified, call it
                        if files[file] is not None and not args.no_handlers:
                            files[file](args, url, content)

            if (
                call_primary_handler
                and target_handler is not None
                and not args.no_handlers
            ):
                target_handler(args)
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
        console.print("\n[yellow]ABORTED...[/yellow]")
        pass
