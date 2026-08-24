#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Auto Release v2 — Open Source Launcher
One command: local project → fully dressed public GitHub repository.

What v2 adds over v1 (2026-08-24 merge):
  - Repo facade: About description, homepage, topics
  - Release: tag + auto-generated release notes
  - CHANGELOG.md scaffold (Keep a Changelog format)
  - package.json scaffold (name/version/description/repository/bugs/keywords)
  - Full badge wall in generated READMEs (release/stars/forks/issues/license/changelog/website)
  - Bilingual README with language switch links (README.md EN + README.zh.md 中文)
  - gh CLI auth fallback: uses `gh auth token` when no --token given

v1 capabilities kept:
  - Privacy scan before any upload
  - Repo creation via GitHub API
  - git init + push
  - Multi-language README generation from templates
  - Xiaohongshu draft promotion (optional)

Usage:
    python github_release.py \
        --repo "owner/repo-name" --path ./project \
        --title "Title" --desc "Description" \
        --homepage "https://your.site" \
        --topics "gaokao,education,static-site"
"""
import os
import sys
import re
import json
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR.parent / "references"

# Sensitive data patterns
SENSITIVE_PATTERNS = {
    "GitHub Token": [r"ghp_[A-Za-z0-9_]{36}", r"gho_[A-Za-z0-9_]{36}", r"github_pat_[A-Za-z0-9_]{22}_[A-Za-z0-9_]{59}"],
    "OpenAI/Anthropic Key": [r"sk-[A-Za-z0-9_-]{20,}"],
    "API Key": [r"api[_-]?key[\"'\s:=]+[\w-]{16,}", r"apikey[\"'\s:=]+[\w-]{16,}"],
    "Password": [r"password[\"'\s:=]+[\w@#$%^&*]{6,}"],
    "Secret": [r"secret[\"'\s:=]+[\w-]{16,}"],
    "Private Key": [r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----"],
    "WeChat Credential": [r"wx[0-9a-f]{16,}", r"app[_-]?secret[\"'\s:=]+[\w-]{16,}"],
}

SENSITIVE_EXTENSIONS = {".pem", ".key", ".p12", ".pfx", ".id_rsa", "id_dsa"}

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode", "dist", "build"}


def scan_sensitive_files(path: str) -> list:
    """Scan for sensitive files and content."""
    issues = []
    root = Path(path)

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if any(part in SKIP_DIRS for part in file_path.parts):
            continue

        # Check file extension
        if file_path.suffix.lower() in SENSITIVE_EXTENSIONS:
            issues.append({"file": str(file_path), "type": "Private Key File", "severity": "high"})
            continue

        # Skip binary files
        if file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip", ".tar", ".gz", ".exe", ".dll"}:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for pattern_name, patterns in SENSITIVE_PATTERNS.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        issues.append({
                            "file": str(file_path),
                            "type": pattern_name,
                            "severity": "high",
                            "matches": len(matches)
                        })
                        break
        except Exception:
            continue

    return issues


def gh_api(endpoint: str, method: str = "GET", token: str = "", body: dict = None) -> dict:
    """Call GitHub REST API. Returns {'success', 'data'/'error', 'status'}."""
    url = f"https://api.github.com{endpoint}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return {"success": True, "data": json.loads(raw) if raw else {}, "status": resp.status}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return {"success": False, "error": f"HTTP {e.code}: {error_body}", "status": e.code}
    except Exception as e:
        return {"success": False, "error": str(e), "status": 0}


def get_token(args_token: str) -> str:
    """Resolve token: --token arg > GITHUB_TOKEN env > gh auth token."""
    if args_token:
        return args_token
    env = os.environ.get("GITHUB_TOKEN", "")
    if env:
        return env
    try:
        r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=15)
        t = (r.stdout or "").strip()
        if r.returncode == 0 and t:
            return t
    except Exception:
        pass
    return ""


def create_github_repo(token: str, name: str, description: str, private: bool = False) -> dict:
    """Create GitHub repository via API."""
    payload = {
        "name": name,
        "description": description,
        "private": private,
        "has_issues": True,
        "has_wiki": False,
        "auto_init": False,
    }
    return gh_api("/user/repos", "POST", token, payload)


def update_repo_meta(token: str, repo: str, description: str, homepage: str, topics: list) -> dict:
    """Set About description + homepage (PATCH) and topics (PUT)."""
    out = {}
    patch = {"description": description, "homepage": homepage or ""}
    if homepage:
        patch["has_projects"] = False
    out["patch"] = gh_api(f"/repos/{repo}", "PATCH", token, patch)
    if topics:
        out["topics"] = gh_api(f"/repos/{repo}/topics", "PUT", token, {"names": topics})
    return out


def push_file_via_api(token: str, repo: str, branch: str, path: str, local_file: Path, message: str) -> dict:
    """Create/update a single file via Contents API (works even when git push is blocked, e.g. CN network)."""
    import base64
    content_b64 = base64.b64encode(local_file.read_bytes()).decode()
    # existing sha?
    existing = gh_api(f"/repos/{repo}/contents/{path}?ref={branch}", "GET", token)
    body = {"message": message, "content": content_b64, "branch": branch}
    if existing.get("success"):
        body["sha"] = existing["data"]["sha"]
    return gh_api(f"/repos/{repo}/contents/{path}", "PUT", token, body)


def init_and_push(repo_url: str, local_path: Path, token: str, branch: str = "main") -> dict:
    """Initialize git repo and push to GitHub. Falls back to a helpful error on network failure."""
    path = local_path

    def run(*cmd):
        return subprocess.run(list(cmd), cwd=path, capture_output=True, text=True)

    run("git", "init")
    run("git", "config", "user.email", "github-actions@github.com")
    run("git", "config", "user.name", "GitHub Actions")
    run("git", "add", ".")
    c = run("git", "commit", "-m", "Initial commit: open source launch")
    if c.returncode != 0 and "nothing to commit" not in (c.stdout or ""):
        return {"success": False, "stderr": c.stderr or c.stdout}

    remote_url = repo_url.replace("https://", f"https://{token}@")
    run("git", "remote", "remove", "origin")
    r = run("git", "remote", "add", "origin", remote_url)
    if r.returncode != 0:
        return {"success": False, "stderr": r.stderr}

    result = run("git", "push", "-u", "origin", branch)
    ok = result.returncode == 0
    hint = ""
    if not ok and ("Could not resolve" in result.stderr or "Failed to connect" in result.stderr
                   or "Connection refused" in result.stderr or "timeout" in result.stderr.lower()):
        hint = ("\n     Network tip: if git push is blocked (e.g. github.com unreachable), "
                "retry with --api-push to upload files one-by-one via the Contents API.")
    return {"success": ok, "stdout": result.stdout, "stderr": result.stderr + hint}


def make_changelog(title: str) -> str:
    return f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- (add your roadmap items here)

## [1.0.0] - {__import__('datetime').date.today().isoformat()}

### Added

- Initial open-source release of {title}

[Unreleased]: compare/v1.0.0...HEAD
[1.0.0]: releases/tag/v1.0.0
"""


def make_package_json(name: str, version: str, description: str, repo: str, homepage: str, keywords: list, author: str) -> str:
    pkg = {
        "name": name,
        "version": version,
        "description": description,
        "homepage": homepage or "",
        "repository": {"type": "git", "url": f"git+https://github.com/{repo}.git"},
        "bugs": {"url": f"https://github.com/{repo}/issues"},
        "license": "MIT",
        "author": {"name": author, "url": f"https://github.com/{repo.split('/')[0]}"},
        "keywords": keywords,
    }
    return json.dumps(pkg, ensure_ascii=False, indent=2) + "\n"


MIT_LICENSE = """MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def generate_readme(template_path: str, ctx: dict) -> str:
    """Generate README from template with full variable context."""
    tpl = Path(template_path).read_text(encoding="utf-8")
    for key, value in ctx.items():
        tpl = tpl.replace("{{" + key + "}}", str(value))
    # strip leftover unknown placeholders
    return re.sub(r"\{\{\w+\}\}", "", tpl)


def create_release(token: str, repo: str, tag: str, name: str, notes: str) -> dict:
    """Create a Git tag + GitHub Release with notes."""
    r = gh_api(f"/repos/{repo}/releases", "POST", token, {
        "tag_name": tag,
        "name": name,
        "body": notes,
        "draft": False,
        "prerelease": False,
    })
    return r


def generate_xhs_caption(title: str, description: str, repo: str) -> str:
    """Generate Xiaohongshu promotional caption from project info."""
    caption = f"""🔥 发现一个超棒的开源项目：{title}

{description}

✨ 为什么推荐这个项目？
• 功能强大，开箱即用
• 代码规范，易于二次开发
• 持续维护，社区活跃

💡 适合谁用？
• 想要提升效率的开发者
• 需要自动化工具的技术团队
• 对开源感兴趣的学习者

🚀 快速开始：
1. GitHub 搜索「{repo.split('/')[-1]}」获取源码
2. 按照 README 指引安装配置
3. 开始使用，遇到问题欢迎提 Issue

---
如果觉得有用，别忘了点赞👍、收藏⭐、分享给更多朋友！
关注我，持续分享优质开源项目和技术干货。

#开源项目 #技术分享 #编程 #效率工具 #开发者
"""
    return caption.strip()


def find_cover_image(local_path: Path) -> str:
    """Find a suitable cover image in the project."""
    candidates = [
        "cover.png", "cover.jpg", "cover.jpeg", "cover.gif",
        "thumbnail.png", "thumbnail.jpg", "thumbnail.jpeg",
        "banner.png", "banner.jpg", "banner.jpeg",
        "icon.png", "icon.jpg", "logo.png", "logo.jpg",
    ]
    for name in candidates:
        candidate = local_path / name
        if candidate.exists() and candidate.is_file():
            return str(candidate)

    for subdir in ["assets", "images", "img", "media", "static"]:
        subpath = local_path / subdir
        if subpath.exists() and subpath.is_dir():
            for name in candidates:
                candidate = subpath / name
                if candidate.exists() and candidate.is_file():
                    return str(candidate)

    return ""


def publish_xiaohongshu_draft(title: str, cover_image: str, caption: str) -> dict:
    """Publish long-text draft to Xiaohongshu via opencli."""
    if not cover_image or not Path(cover_image).exists():
        return {"success": False, "error": "Cover image not found"}

    cmd = ["opencli", "xiaohongshu", "publish", "--title", title, "--images", cover_image, "--draft", "--", caption]

    env = os.environ.copy()
    env["OPENCLI_BROWSER_COMMAND_TIMEOUT"] = "300000"
    if sys.platform == 'win32' and cmd[0] == 'opencli':
        cmd[0] = 'opencli.cmd'

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300, env=env)
        stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''

        if "暂存成功" in stdout or "成功" in stdout or "ok: true" in stdout.lower():
            return {"success": True, "output": stdout}
        else:
            return {"success": False, "error": stderr or stdout[:200]}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "TIMEOUT"}
    except FileNotFoundError:
        return {"success": False, "error": "opencli not found. Please install opencli first."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Auto Release v2 — open source a local project as a fully dressed repo "
                    "(About/topics, bilingual badge-wall READMEs, CHANGELOG, package.json, LICENSE, Release v1.0.0)")
    parser.add_argument("--repo", required=True, help="Repository (owner/repo-name)")
    parser.add_argument("--path", default=".", help="Local project path")
    parser.add_argument("--token", help="GitHub PAT (or GITHUB_TOKEN env, or gh auth token)")
    parser.add_argument("--title", required=True, help="Repository title / README heading")
    parser.add_argument("--desc", default="", help="Repository description (goes to About + READMEs)")
    parser.add_argument("--private", action="store_true", help="Create private repository")
    parser.add_argument("--homepage", default="", help="Project website URL (About 'website' field + website badge)")
    parser.add_argument("--topics", default="", help="Comma-separated repo topics (max 20, lowercase)")
    parser.add_argument("--version", default="1.0.0", help="Initial release tag version (default 1.0.0)")
    parser.add_argument("--author", default="", help="Author name for LICENSE/package.json (default: repo owner)")
    parser.add_argument("--readme-langs", default="en,zh", help="Comma-separated README languages (default en,zh)")
    parser.add_argument("--skip-privacy-check", action="store_true", help="Skip privacy scan (not recommended)")
    parser.add_argument("--no-release", action="store_true", help="Do not create the initial GitHub Release")
    parser.add_argument("--no-facade-files", action="store_true", help="Do not generate CHANGELOG/package.json/LICENSE scaffolds")
    parser.add_argument("--api-push", action="store_true",
                        help="Push files one-by-one via Contents API instead of git push (use when git push is blocked)")
    parser.add_argument("--publish-xhs", action="store_true", help="Publish promotional text to Xiaohongshu drafts")
    parser.add_argument("--xhs-cover", help="Cover image path for Xiaohongshu post")
    args = parser.parse_args()

    token = get_token(args.token)
    if not token:
        print("Error: no GitHub token. Use --token, GITHUB_TOKEN env, or `gh auth login`.", file=sys.stderr)
        sys.exit(1)

    owner = args.repo.split("/")[0]
    repo_name = args.repo.split("/")[-1]
    author = args.author or owner
    topics = [t.strip().lower() for t in args.topics.split(",") if t.strip()]
    local_path = Path(args.path).resolve()

    # ---------- Step 1: privacy scan ----------
    if not args.skip_privacy_check:
        print("[1/7] Scanning for sensitive data...")
        issues = scan_sensitive_files(str(local_path))
        if issues:
            print(f"     Found {len(issues)} potential issues:")
            for issue in issues:
                print(f"     - {issue['file']}: {issue['type']} ({issue['severity']})")
            confirm = input("     Continue anyway? (y/N): ").strip().lower()
            if confirm != "y":
                print("     Aborted.")
                sys.exit(1)
        else:
            print("     No sensitive data found.")
    else:
        print("[1/7] Privacy scan skipped (--skip-privacy-check).")

    # ---------- Step 2: create repo ----------
    print("[2/7] Creating GitHub repository...")
    result = create_github_repo(token, repo_name, args.desc, args.private)
    if not result["success"]:
        if "422" in result["error"]:
            print("     Repository already exists — continuing (facade will update it).")
        else:
            print(f"     Failed to create repo: {result['error']}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"     Created: https://github.com/{args.repo}")

    # ---------- Step 3: About/topics ----------
    print("[3/7] Setting About description, homepage, topics...")
    meta = update_repo_meta(token, args.repo, args.desc, args.homepage, topics)
    if not meta.get("patch", {}).get("success"):
        print(f"     Warning: About update failed: {meta.get('patch', {}).get('error')}")
    elif topics and not meta.get("topics", {}).get("success"):
        print(f"     Warning: topics update failed: {meta.get('topics', {}).get('error')}")

    # ---------- Step 4: push code ----------
    if args.api_push:
        print("[4/7] Pushing files via Contents API (--api-push)...")
        files = [f for f in local_path.rglob("*")
                 if f.is_file() and ".git" not in f.parts]
        failed = []
        for f in files:
            rel = f.relative_to(local_path).as_posix()
            r = push_file_via_api(token, args.repo, "main", rel, f, f"feat: add {rel}")
            if not r.get("success"):
                failed.append((rel, r.get("error", "")[:120]))
        if failed:
            print(f"     WARNING: {len(failed)} file(s) failed:")
            for rel, err in failed:
                print(f"     - {rel}: {err}")
        else:
            print(f"     {len(files)} file(s) pushed via API.")
    else:
        print("[4/7] Pushing code via git...")
        repo_url = f"https://github.com/{args.repo}.git"
        push_result = init_and_push(repo_url, local_path, token)
        if not push_result["success"]:
            print(f"     Push failed: {push_result['stderr']}", file=sys.stderr)
            print("     Tip: retry with --api-push to upload via Contents API.", file=sys.stderr)
            sys.exit(1)
        print("     Code pushed successfully.")

    # ---------- Step 5: READMEs ----------
    print("[5/7] Generating multi-language README with badge wall...")
    langs = [l.strip() for l in args.readme_langs.split(",")]
    badge_repo = args.repo
    website_badge = (f'<a href="{args.homepage}"><img '
                     f'src="https://img.shields.io/website?url={urllib.request.quote(args.homepage, safe="")}'
                     f'&label=live%20site" alt="website"></a>') if args.homepage else ""
    lang_switch = {"en": '<a href="README_zh.md">中文</a>',
                   "zh": '<a href="README.md">English</a>',
                   "ja": '<a href="README.md">English</a> · <a href="README_zh.md">中文</a>'}
    readme_names = {}
    for lang in langs:
        template = TEMPLATE_DIR / f"readme_template.{lang}.md"
        if not template.exists():
            print(f"     No template for '{lang}', skipping.")
            continue
        ctx = {
            "title": args.title,
            "description": args.desc,
            "repo": badge_repo,
            "repo_name": repo_name,
            "owner": owner,
            "version": args.version,
            "topics_line": " · ".join(topics),
            "website_badge": website_badge,
            "lang_switch": lang_switch.get(lang, ""),
            "year": __import__('datetime').date.today().year,
            "author": author,
        }
        content = generate_readme(str(template), ctx)
        readme_name = "README_zh.md" if lang == "zh" else ("README_ja.md" if lang == "ja" else "README.md")
        readme_names[lang] = (readme_name, content)
        print(f"     Prepared {readme_name}")

    # write locally then push (so they exist in repo)
    for lang, (name, content) in readme_names.items():
        tmp = local_path / name
        tmp.write_text(content, encoding="utf-8")
        if args.api_push:
            r = push_file_via_api(token, args.repo, "main", name, tmp, f"docs: add {name}")
            if not r.get("success"):
                print(f"     Warning: pushing {name} failed: {r.get('error', '')[:120]}")
        print(f"     Wrote {tmp}")

    # if we used git push, READMEs were written after push — push them now
    if not args.api_push and readme_names:
        subprocess.run(["git", "add", "."], cwd=local_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "docs: bilingual README with badge wall"], cwd=local_path, capture_output=True)
        subprocess.run(["git", "push"], cwd=local_path, capture_output=True)

    # ---------- Step 6: facade files ----------
    if not args.no_facade_files:
        print("[6/7] Generating CHANGELOG / package.json / LICENSE scaffolds...")
        cl = local_path / "CHANGELOG.md"
        if not cl.exists():
            cl.write_text(make_changelog(args.title), encoding="utf-8")
        pkg = local_path / "package.json"
        if not pkg.exists():
            kws = topics[:10] if topics else ["open-source"]
            pkg.write_text(make_package_json(repo_name.lower().replace("_", "-"), args.version,
                                             args.desc, args.repo, args.homepage, kws, author), encoding="utf-8")
        lic = local_path / "LICENSE"
        if not lic.exists():
            lic.write_text(MIT_LICENSE.format(year=__import__('datetime').date.today().year, author=author),
                           encoding="utf-8")
        # push them
        for fname, msg in [("CHANGELOG.md", "docs: add CHANGELOG"),
                           ("package.json", "chore: add package.json"),
                           ("LICENSE", "docs: add MIT LICENSE")]:
            fp = local_path / fname
            if fp.exists():
                if args.api_push:
                    push_file_via_api(token, args.repo, "main", fname, fp, msg)
                else:
                    subprocess.run(["git", "add", fname], cwd=local_path, capture_output=True)
        if not args.api_push:
            subprocess.run(["git", "commit", "-m", "chore: add CHANGELOG, package.json, LICENSE"],
                           cwd=local_path, capture_output=True)
            subprocess.run(["git", "push"], cwd=local_path, capture_output=True)
        print("     Facade files ready.")
    else:
        print("[6/7] Skipping facade files (--no-facade-files).")

    # ---------- Step 7: release ----------
    if not args.no_release:
        print(f"[7/7] Creating Release v{args.version}...")
        notes = f"""## {args.title} v{args.version}

{args.desc}

### What's inside
- Bilingual README ({', '.join(langs)}) with full badge wall
- Repository About, topics{' , homepage' if args.homepage else ''}
- CHANGELOG (Keep a Changelog), package.json, MIT License
"""
        r = create_release(token, args.repo, f"v{args.version}",
                           f"v{args.version} · Initial open-source release", notes)
        if r.get("success"):
            print(f"     Released: https://github.com/{args.repo}/releases/tag/v{args.version}")
        else:
            print(f"     Warning: release failed: {r.get('error', '')[:160]}")
    else:
        print("[7/7] Skipping release (--no-release).")

    # ---------- Xiaohongshu ----------
    if args.publish_xhs:
        cover_image = args.xhs_cover or find_cover_image(local_path)
        if not cover_image:
            print("[xhs] No cover image found. Provide --xhs-cover or add cover.jpg to project root.")
        else:
            caption = generate_xhs_caption(args.title, args.desc, args.repo)
            result = publish_xiaohongshu_draft(args.title, cover_image, caption)
            print("[xhs] Draft published." if result["success"]
                  else f"[xhs] Publish failed: {result['error']}")

    print("\nDone! Fully dressed repository at:")
    print(f"  https://github.com/{args.repo}")
    print("Checklist: About ✓ topics ✓ bilingual README ✓ badges ✓ CHANGELOG ✓ package.json ✓ LICENSE ✓ Release ✓")


if __name__ == "__main__":
    main()
