#!/usr/bin/env python3

from .handlers.wordpress import wp_handler, wp_xmlrpc_handler

TARGETS = {
    "Misc": [
        "/robots.txt",
        "/sitemap.xml",
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
        "/wp-admin",
        # "/.well-known/security.txt",
    ],
    "WordPress": {
        "handler": wp_handler,
        "files": {
            "/wp-admin": None,  # optional handler here; None if no handler
        },
    },
}
