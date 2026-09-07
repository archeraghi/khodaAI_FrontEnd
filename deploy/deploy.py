#!/usr/bin/env python3
"""Deploy a pinned Khoda website archive on its existing Nginx host.

Run on the server after extracting the selected GitHub commit:
  python3 deploy/deploy.py --source /tmp/extracted-source --revision FULL_GIT_SHA --dry-run
  python3 deploy/deploy.py --source /tmp/extracted-source --revision FULL_GIT_SHA

The dry run only reads and validates files, then prints the proposed config diff.
No credentials are created or changed. TLS directives remain untouched.
"""

import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile


SITE = Path("/var/www/khoda-ai")
CONFIG_LINK = Path("/etc/nginx/sites-enabled/khoda-ai")
PUBLIC_FILES = (
    "index.html", "robots.txt", "sitemap.xml", "favicon.png",
    "google0cbd976d77731379.html", "assets/site.css",
    "images/logo.png", "images/bearie.png", "images/me.jpg",
    "images/logo.webp", "images/bearie.webp", "images/me.webp",
    "fonts/inter-latin-wght-400-800.woff2", "fonts/OFL.txt", "fonts/INTER-LICENSE.txt",
)
PREVIOUS_ASSET_TYPES = {
    "images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"},
    "assets": {".css", ".js", ".png", ".jpg", ".webp", ".svg"},
    "fonts": {".woff", ".woff2", ".txt"},
}
BEGIN = "    # BEGIN Khoda static SEO deployment"
END = "    # END Khoda static SEO deployment"
CONFIG_ADDITION = r'''
    # BEGIN Khoda static SEO deployment
    if ($host != khoda.ai) {
        return 301 https://khoda.ai$request_uri;
    }
    # $request_uri stays original when index.html is selected internally.
    if ($request_uri ~ "^/index[.]html(?:[?]|$)") {
        return 301 https://khoda.ai/$is_args$args;
    }

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/javascript application/json application/xml text/xml image/svg+xml;

    location = /assets/site.css {
        expires 1h;
        try_files $uri =404;
    }
    location /fonts/ {
        expires 7d;
        try_files $uri =404;
    }
    # END Khoda static SEO deployment
'''


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def regular_file(root, relative):
    path = root / relative
    require(all(not part.is_symlink() for part in [path, *path.parents]
                if part != root.parent and part.is_relative_to(root)),
            f"Symlink is not permitted in public asset: {path}")
    require(path.is_file() and path.stat().st_size > 0,
            f"Missing or empty public file: {path}")
    return path


def matching_brace(text, opening):
    depth, quote, comment, escaped = 0, None, False, False
    for position in range(opening, len(text)):
        character = text[position]
        if comment:
            comment = character != "\n"
        elif escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif quote:
            if character == quote:
                quote = None
        elif character in "\"'":
            quote = character
        elif character == "#":
            comment = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return position
    raise RuntimeError("Unbalanced Nginx server block")


def updated_config(original):
    # Replace only our marked addition on later deployments.
    if BEGIN in original or END in original:
        require(original.count(BEGIN) == original.count(END) == 1,
                "Unexpected deployment marker count")
        original = re.sub(r"\n" + re.escape(BEGIN) + r"[\s\S]*?" + re.escape(END) + r"\n",
                          "", original, count=1)
    servers = list(re.finditer(r"(?m)^[ \t]*server\s*\{", original))
    require(len(servers) == 2, "Expected exactly the existing HTTPS and HTTP servers")
    first = servers[0]
    opening = original.index("{", first.start())
    closing = matching_brace(original, opening)
    block = original[opening + 1:closing]
    require(closing < servers[1].start(), "Unexpected nested server blocks")
    require(re.search(r"(?m)^\s*listen\s+[^;]*\b443\b[^;]*\bssl\b[^;]*;", block),
            "First server is not the expected HTTPS server")
    names = re.findall(r"(?m)^\s*server_name\s+([^;]+);", block)
    require(len(names) == 1 and set(names[0].split()) == {
        "khoda.ai", "www.khoda.ai", "khoda-ai.165-22-147-34.nip.io"
    }, "HTTPS server names differ from the inspected host")
    require(re.findall(r"(?m)^\s*root\s+([^;]+);", block) == [str(SITE / "current")],
            "Unexpected HTTPS document root")
    require(re.findall(r"(?m)^\s*index\s+([^;]+);", block) == ["index.html"],
            "Unexpected HTTPS index configuration")
    require(re.search(r"location\s+/\s*\{\s*try_files\s+\$uri\s+\$uri/\s+=404;\s*\}", block),
            "Expected existing static-file fallback was not found")
    require("/etc/letsencrypt/live/khoda-ai.165-22-147-34.nip.io/" in block,
            "Expected existing certificate configuration was not found")
    require(not re.search(r"(?m)^\s*(?:gzip(?:_\w+)?\s|location\s+(?:=\s+)?/(?:assets/site\.css|fonts/))", block),
            "Existing compression or asset rule needs manual review")
    require(not re.search(r"(?m)^\s*if\s*\(\s*\$(?:host|request_uri)\b", block),
            "Existing host or URI rewrite needs manual review")
    return original[:opening + 1] + CONFIG_ADDITION + original[opening + 1:]


def copy_public(source, destination, relative):
    path = regular_file(source, relative)
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    shutil.copyfile(path, target)
    target.chmod(0o644)


def atomic_config(path, content, metadata):
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), stat.S_IMODE(metadata.st_mode))
            os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def switch_release(current, target):
    pending = current.parent / f".current-{os.getpid()}"
    require(not pending.exists() and not pending.is_symlink(), "Pending release link already exists")
    try:
        pending.symlink_to(target)
        os.replace(pending, current)
    finally:
        pending.unlink(missing_ok=True)


def run(*arguments):
    subprocess.run(arguments, check=True)


def check_live(release):
    def request(path, host="khoda.ai"):
        result = subprocess.run([
            "curl", "--silent", "--show-error", "--max-time", "20",
            "--noproxy", "*", "--resolve", f"{host}:443:127.0.0.1",
            "--write-out", "\n%{http_code}\n%{redirect_url}", f"https://{host}{path}",
        ], check=True, capture_output=True)
        body, code, redirect = result.stdout.rsplit(b"\n", 2)
        return body, int(code), redirect.decode()

    for relative in PUBLIC_FILES:
        body, code, _ = request("/" if relative == "index.html" else f"/{relative}")
        require(code == 200 and body == (release / relative).read_bytes(),
                f"Live content differs for {relative} (HTTP {code})")
    for path, host, expected, destination in [
        ("/index.html?deploy=check", "khoda.ai", 301, "https://khoda.ai/?deploy=check"),
        ("/", "www.khoda.ai", 301, "https://khoda.ai/"),
        ("/", "khoda-ai.165-22-147-34.nip.io", 301, "https://khoda.ai/"),
        ("/__khoda_deploy_missing_page__", "khoda.ai", 404, ""),
    ]:
        _, code, redirect = request(path, host)
        require(code == expected and redirect == destination,
                f"Unexpected response for {host}{path}: HTTP {code}, redirect {redirect}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.revision), "Use the full lowercase Git commit SHA")
    require(not args.source.is_symlink(), "Source directory must not be a symlink")
    source = args.source.resolve(strict=True)
    require(source.is_dir() and source != Path("/") and not source.is_relative_to(SITE),
            "Source must be an extracted directory outside the live website")
    for relative in PUBLIC_FILES:
        regular_file(source, relative)
    require((source / "google0cbd976d77731379.html").read_text().strip() ==
            "google-site-verification: google0cbd976d77731379.html", "Google ownership file differs")
    require("https://khoda.ai/sitemap.xml" in (source / "robots.txt").read_text(),
            "robots.txt does not reference the public sitemap")
    require("https://khoda.ai/" in (source / "sitemap.xml").read_text(), "Unexpected sitemap origin")

    current = SITE / "current"
    releases = SITE / "releases"
    require(current.is_symlink() and releases.is_dir(), "Expected existing release layout")
    previous_link = os.readlink(current)
    previous = current.resolve(strict=True)
    require(previous.is_dir() and previous.parent == releases.resolve(),
            "Current link must point directly to a release directory")
    regular_file(previous, "index.html")
    require((previous / "images").is_dir() and not (previous / "images").is_symlink(),
            "Expected existing images directory")
    allowed_top = {Path(name).parts[0] for name in PUBLIC_FILES}
    require(all(entry.name in allowed_top and not entry.is_symlink() for entry in previous.iterdir()),
            "Unexpected files or links in the current release")
    preserved = []
    for directory, suffixes in PREVIOUS_ASSET_TYPES.items():
        asset_root = previous / directory
        if not asset_root.exists():
            continue
        require(asset_root.is_dir() and not asset_root.is_symlink(), "Unexpected previous asset directory")
        for asset in asset_root.rglob("*"):
            require(not asset.is_symlink(), f"Symlink in previous assets: {asset}")
            if asset.is_file():
                require(asset.suffix.lower() in suffixes and not asset.name.startswith("."),
                        f"Unexpected previous public asset: {asset}")
                relative = asset.relative_to(previous).as_posix()
                regular_file(previous, relative)
                if relative not in PUBLIC_FILES:
                    preserved.append(relative)

    config = CONFIG_LINK.resolve(strict=True)
    require(config.is_file() and config.parent in {
        Path("/etc/nginx/sites-available"), Path("/etc/nginx/sites-enabled")
    }, "Unexpected Nginx configuration target")
    config_metadata = config.stat()
    original = config.read_bytes()
    proposed = updated_config(original.decode()).encode()
    release_name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-seo-" + args.revision[:12]
    release = releases / release_name
    require(not release.exists(), "Release name already exists")
    print(f"Source: {source}\nRevision: {args.revision}\nPrevious: {previous}\nRelease: {release}")
    print(f"Public files: {len(PUBLIC_FILES)}; preserved earlier assets: {len(preserved)}")
    if args.dry_run:
        print("".join(difflib.unified_diff(original.decode().splitlines(True),
                                           proposed.decode().splitlines(True),
                                           fromfile=str(config), tofile="proposed")))
        return

    require(os.geteuid() == 0, "Deployment requires the existing root console")
    for command in ("nginx", "systemctl", "curl"):
        require(shutil.which(command), f"Missing required command: {command}")
    run("nginx", "-t")
    release.mkdir(mode=0o755)
    for relative in PUBLIC_FILES:
        copy_public(source, release, relative)
    for relative in preserved:
        copy_public(previous, release, relative)
    backup = SITE / "deploy-backups" / release_name
    backup.mkdir(parents=True, mode=0o700, exist_ok=False)
    (backup / "nginx.conf").write_bytes(original)
    (backup / "nginx.conf").chmod(0o600)
    record = {
        "revision": args.revision, "release": str(release), "previous": str(previous),
        "previous_link": previous_link, "configuration": str(config), "backup": str(backup),
        "files": {name: hashlib.sha256((release / name).read_bytes()).hexdigest() for name in PUBLIC_FILES},
        "preserved_assets": preserved, "status": "prepared",
    }
    record_file = backup / "deployment.json"
    record_file.write_text(json.dumps(record, indent=2) + "\n")
    record_file.chmod(0o600)
    changed_config = switched = False
    try:
        # Stop if another deployment changed state while files were copied.
        require(config.read_bytes() == original and os.readlink(current) == previous_link,
                "Live configuration or release changed during preparation")
        atomic_config(config, proposed, config_metadata)
        changed_config = True
        run("nginx", "-t")
        switch_release(current, release)
        switched = True
        run("systemctl", "reload", "nginx")
        check_live(release)
        record["status"] = "verified"
        record_file.write_text(json.dumps(record, indent=2) + "\n")
    except BaseException:
        if changed_config:
            atomic_config(config, original, config_metadata)
        if switched:
            switch_release(current, previous_link)
        if changed_config or switched:
            run("nginx", "-t")
            run("systemctl", "reload", "nginx")
        record["status"] = "rolled_back"
        record_file.write_text(json.dumps(record, indent=2) + "\n")
        raise
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
