#!/usr/bin/env python3

from .handlers.wordpress import wp_handler, wp_xmlrpc_handler
from .handlers.primary import robots_handler, sitemap_handler

TARGETS = {
    "Primary": {
        "handler": None,
        "files": {
            "/robots.txt": robots_handler,
            "/sitemap.xml": sitemap_handler,
        },
    },
    "Misc": [
        # "/robots.txt",
        # "/sitemap.xml",
        "/humans.txt",
        "/.vscode/settings.json",
        "/.env",
        "/.github/workflows/main.yml",
        "/.gitignore",
        "/.travis.yml" "/package.json",
        "/README.md",
        "/readme.txt",
        "/README.txt",
    ],
    "Paths": [
        "/.well-known",
        "/admin",
        "/administrator",
        "/assets",
        "/downloads",
        "/files",
        "/images",
        "/include",
        "/includes",
        "/logs",
        "/media",
        "/misc",
        "/scripts",
        "/temp",
        "/test",
        "/testing",
        "/tmp",
        # "/.well-known/security.txt",
    ],
    "WordPress": {
        "handler": wp_handler,
        "files": {
            "/wp-admin": None,  # optional handler here; None if no handler
        },
    },
}

# TODO: this will be a bin where we can add targets found after a handler finds them;
# not currently used
DISCOVERED_ASSETS = []
