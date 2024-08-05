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
        "/humans.txt",
        "/.vscode/settings.json",
        "/.env",
        "/.git",
        "/.github/workflows/main.yml",
        "/.gitignore",
        "/.travis.yml",
        "/package.json",
        "/README.md",
        "/readme.txt",
        "/README.txt",
        "/index.old",
        "/index.bak",
        "/index.php.old",
        "/index.php.bak",
    ],
    "Paths": [
        "/.well-known",
        "/admin",
        "/administrator",
        "/assets",
        "/backup",
        "/downloads",
        "/files",
        "/images",
        "/include",
        "/includes",
        "/logs",
        "/media",
        "/misc",
        "/old",
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
            "/wp-login.php": None,  # optional handler here; None if no handler
            "/wp-content": None,
        },
    },
}

# TODO: this will be a bin where we can add targets found after a handler finds them;
# not currently used
DISCOVERED_ASSETS = []
