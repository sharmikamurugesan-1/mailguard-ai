#!/usr/bin/env python3
"""Build script for MailGuard AI static frontend export.

Phase 12I: Vercel frontend + Render backend
Renders/exports all static assets and HTML templates from templates/ and static/
into the standalone frontend/ directory for Vercel deployment.
Flask continues to serve the application directly for Render-only monolith fallback.
"""

import os
import shutil
import sys
from pathlib import Path


def build_frontend() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    templates_dir = repo_root / "templates"
    static_dir = repo_root / "static"
    output_dir = repo_root / "frontend"

    print("=" * 60)
    print("MailGuard AI - Static Frontend Export (Phase 12I)")
    print("=" * 60)
    print(f"Repository Root: {repo_root}")
    print(f"Templates Directory: {templates_dir}")
    print(f"Static Assets Directory: {static_dir}")
    print(f"Target Output Directory: {output_dir}")

    if not templates_dir.exists():
        print(f"ERROR: Templates directory not found at {templates_dir}", file=sys.stderr)
        return 1

    if not static_dir.exists():
        print(f"ERROR: Static directory not found at {static_dir}", file=sys.stderr)
        return 1

    # 1. Clean or create frontend/ directory
    if output_dir.exists():
        print(f"Cleaning existing output directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Copy static files & subdirectories (css/, js/, fonts/, img/, vendor/, data/, favicons, config.js)
    copied_files = 0
    copied_bytes = 0

    for item in static_dir.iterdir():
        dest = output_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
            dir_count = sum(1 for _ in dest.rglob("*") if _.is_file())
            dir_size = sum(_.stat().st_size for _ in dest.rglob("*") if _.is_file())
            copied_files += dir_count
            copied_bytes += dir_size
            print(f"  [DIR]  static/{item.name} -> frontend/{item.name} ({dir_count} files, {dir_size:,} bytes)")
        else:
            shutil.copy2(item, dest)
            size = item.stat().st_size
            copied_files += 1
            copied_bytes += size
            print(f"  [FILE] static/{item.name} -> frontend/{item.name} ({size:,} bytes)")

    # 3. Check and export templates (index.html, 404.html, 500.html)
    for tpl_name in ["index.html", "404.html", "500.html"]:
        src_tpl = templates_dir / tpl_name
        dest_html = output_dir / tpl_name
        if not src_tpl.exists():
            print(f"WARNING: Template {tpl_name} not found, skipping.")
            continue

        with open(src_tpl, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for Jinja templating expressions
        has_jinja = "{{" in content or "{%" in content
        if has_jinja:
            print(f"  [JINJA] Rendering template {tpl_name} via Jinja2...")
            try:
                from jinja2 import Environment, FileSystemLoader
                env = Environment(loader=FileSystemLoader(str(templates_dir)))
                template = env.get_template(tpl_name)
                rendered = template.render()
                with open(dest_html, "w", encoding="utf-8") as f:
                    f.write(rendered)
            except Exception as e:
                print(f"ERROR: Jinja rendering failed for {tpl_name}: {e}", file=sys.stderr)
                return 1
        else:
            # Pure static HTML template
            shutil.copy2(src_tpl, dest_html)

        size = dest_html.stat().st_size
        copied_files += 1
        copied_bytes += size
        print(f"  [HTML] templates/{tpl_name} -> frontend/{tpl_name} ({size:,} bytes)")

    # 4. Verify frontend/config.js exists and exports API_BASE_URL
    config_js = output_dir / "config.js"
    if not config_js.exists():
        print("ERROR: frontend/config.js was not created!", file=sys.stderr)
        return 1
    with open(config_js, "r", encoding="utf-8") as f:
        config_content = f.read()
    if "API_BASE_URL" not in config_content:
        print("ERROR: frontend/config.js does not define API_BASE_URL!", file=sys.stderr)
        return 1

    print("=" * 60)
    print(f"Static frontend export SUCCESSFUL!")
    print(f"Total files in frontend/: {copied_files}")
    print(f"Total size: {copied_bytes:,} bytes ({copied_bytes / (1024*1024):.2f} MB)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(build_frontend())
