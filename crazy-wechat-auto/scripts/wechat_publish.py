#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号草稿箱发布工具
用法:
    python wechat_publish.py --title "文章标题" --content-file path/to/article.md
    python wechat_publish.py --title "文章标题" --content-file path/to/article.md --cover cover.jpg
    python wechat_publish.py --title "文章标题" --content "<p>正文HTML</p>"
"""
import argparse
import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path


APP_ID = os.environ.get("WECHAT_MP_APP_ID", "")
APP_SECRET = os.environ.get("WECHAT_MP_APP_SECRET", "")


def get_access_token(appid: str, secret: str) -> str:
    """获取微信公众号 access_token。"""
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in data:
        raise RuntimeError(f"获取 access_token 失败: {data}")
    return data["access_token"]


def upload_cover_image(access_token: str, image_path: str) -> str:
    """上传封面图片为永久素材，返回永久 media_id（draft/add 必须用永久素材）。"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(image_path, "rb") as f:
        image_data = f.read()

    filename = os.path.basename(image_path)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + image_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if data.get("errcode"):
        raise RuntimeError(f"上传封面图片失败: {data}")
    return data["media_id"]


def upload_image(access_token: str, image_path: str) -> str:
    """上传图片到微信素材库（正文内图片），返回 URL。"""
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(image_path, "rb") as f:
        image_data = f.read()

    filename = os.path.basename(image_path)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + image_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if data.get("errcode"):
        raise RuntimeError(f"上传图片失败: {data}")
    return data["url"]


def upload_thumb_media(access_token: str, image_path: str) -> str:
    """上传封面图片（旧版，返回临时 thumb_media_id）。"""
    url = f"https://api.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=thumb"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(image_path, "rb") as f:
        image_data = f.read()

    filename = os.path.basename(image_path)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + image_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if data.get("errcode"):
        raise RuntimeError(f"上传封面图片失败: {data}")
    return data["thumb_media_id"]


def add_draft(access_token: str, title: str, content: str, thumb_media_id: str = "", author: str = "", digest: str = "") -> dict:
    """创建微信公众号草稿。"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"

    article = {
        "title": title,
        "content": content,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    if author:
        article["author"] = author
    if digest:
        article["digest"] = digest
    if thumb_media_id:
        article["thumb_media_id"] = thumb_media_id
        article["show_cover_pic"] = 1

    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if data.get("errcode"):
        raise RuntimeError(f"创建草稿失败: {data}")
    return data


def markdown_to_html(md_text: str) -> str:
    """Markdown 转 HTML，并应用公众号排版规则。"""
    lines = md_text.splitlines()
    html_lines = []
    in_code = False
    code_buffer = []

    for line in lines:
        stripped = line.strip()

        # 代码块
        if stripped.startswith("```"):
            if in_code:
                html_lines.append("<pre><code>" + "\n".join(code_buffer) + "</code></pre>")
                code_buffer = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_buffer.append(line)
            continue

        # 标题（一级/二级按公众号规范处理）
        if stripped.startswith("# "):
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        # 列表
        elif stripped.startswith(("- ", "* ")):
            html_lines.append(f"<li>{stripped[2:]}</li>")
        # 粗体（重点内容用蓝色粗体）
        elif stripped.startswith("**") and stripped.endswith("**"):
            html_lines.append(f"<p><strong><span style=\"color: #576b95;\">{stripped[2:-2]}</span></strong></p>")
        # 链接（带下划线）
        elif "[链接:" in stripped and "]" in stripped:
            import re
            match = re.search(r"\[链接:(.*?)\]", stripped)
            if match:
                link_text = match.group(1)
                html_lines.append(f"<p><a href=\"{link_text}\" style=\"text-decoration: underline;\">{link_text}</a></p>")
            else:
                html_lines.append(f"<p>{stripped}</p>")
        # 普通段落
        elif stripped:
            html_lines.append(f"<p>{stripped}</p>")
        # 空行
        else:
            html_lines.append("")

    return "\n".join(html_lines)


def apply_wechat_template(title: str, author: str, body_html: str, summary_image_url: str = "") -> str:
    """将正文 HTML 包装为用户固定的公众号文章模板。"""
    # 作者署名行
    author_line = f"<p>文:@<strong>{author}</strong></p>" if author else ""

    # 固定结尾
    ending = """<p><br></p>
<p>看到这里，说明你和我的频道很合拍！如果喜欢我的内容，愿请你点赞、点"推荐"，并分享给更多志同道合的朋友。为防走散，记得将公众号设为星标🌟。期待与你共同成长，下篇文章再见！</p>
<p><br></p>
<p>🔗参考资料见"阅读原文"<br>
🗣️合作/建议:kuangketongxue@gmail.com<br>
🌍本文英文版已经发到我的推特：kuangketongxue</p>"""

    # 总结图占位
    summary_block = ""
    if summary_image_url:
        summary_block = f'<p><br></p><img src="{summary_image_url}" style="width: 100%;"><p><br></p>'

    # 组装全文：作者行 + 正文 + 总结图 + 结尾
    full_html = f"{author_line}{body_html}{summary_block}{ending}"
    return full_html


def main():
    parser = argparse.ArgumentParser(description="发布文章到微信公众号草稿箱")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--content-file", help="Markdown 内容文件路径")
    parser.add_argument("--content", help="直接传入 HTML 内容（优先于 content-file）")
    parser.add_argument("--cover", help="封面图片路径（可选）")
    parser.add_argument("--author", default="狂客同学", help="作者名（默认：狂客同学）")
    parser.add_argument("--digest", default="", help="文章摘要（可选）")
    parser.add_argument("--summary-image", help="总结图 URL（可选）")
    args = parser.parse_args()

    # 获取内容
    if args.content:
        body_html = args.content
    elif args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as f:
            md_text = f.read()
        body_html = markdown_to_html(md_text)
    else:
        print("错误: 请提供 --content 或 --content-file", file=sys.stderr)
        sys.exit(1)

    # 应用公众号模板
    full_html = apply_wechat_template(args.title, args.author, body_html, args.summary_image or "")

    # 获取 access_token
    print("[1/3] 获取 access_token...")
    token = get_access_token(APP_ID, APP_SECRET)
    print("     成功")

    # 上传封面（draft/add 必须使用永久素材的 media_id）
    print("[2/3] 上传封面图片...")
    if not args.cover or not os.path.exists(args.cover):
        print("错误: 必须提供有效的封面图片（--cover）", file=sys.stderr)
        sys.exit(1)
    thumb_media_id = upload_cover_image(token, args.cover)
    print(f"     thumb_media_id: {thumb_media_id}")

    # 创建草稿
    print("[3/3] 创建草稿...")
    result = add_draft(token, args.title, full_html, thumb_media_id, args.author, args.digest)
    print(f"     草稿创建成功！media_id: {result.get('media_id')}")


if __name__ == "__main__":
    main()
