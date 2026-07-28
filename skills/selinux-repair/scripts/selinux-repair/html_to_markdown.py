#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
from html.parser import HTMLParser
from pathlib import Path


SKIP_CLASS_TOKENS = {
    "nocontent",
    "devsite-banner",
    "devsite-article-meta",
    "devsite-breadcrumb",
    "devsite-page-rating",
    "devsite-recommendations",
}


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def should_drop_line(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered in {
        "",
        "on this page",
        "contents",
        "ai-generated key takeaways",
    }


class DevsiteArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_article_body = False
        self.article_div_depth = 0
        self.skip_depth = 0
        self.current_tag: str | None = None
        self.current_chunks: list[str] = []
        self.lines: list[str] = []
        self.pre_mode = False
        self.pre_chunks: list[str] = []
        self.title = ""
        self.capture_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = set((attrs_dict.get("class") or "").split())

        if tag == "h1" and not self.title:
            self.capture_title = True

        if not self.in_article_body:
            if tag == "div" and "devsite-article-body" in classes:
                self.in_article_body = True
                self.article_div_depth = 1
            return

        if tag == "div":
            self.article_div_depth += 1

        if self.skip_depth:
            if tag in {"div", "section", "aside", "nav"}:
                self.skip_depth += 1
            return

        if classes & SKIP_CLASS_TOKENS:
            self.skip_depth = 1
            return

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li"}:
            self._flush_current()
            self.current_tag = tag
            self.current_chunks = []
            return

        if tag == "pre":
            self._flush_current()
            self.pre_mode = True
            self.pre_chunks = []
            return

        if tag == "br":
            if self.pre_mode:
                self.pre_chunks.append("\n")
            else:
                self.current_chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.capture_title and tag == "h1":
            self.capture_title = False

        if not self.in_article_body:
            return

        if self.skip_depth:
            if tag in {"div", "section", "aside", "nav"}:
                self.skip_depth -= 1
            return

        if tag == "pre" and self.pre_mode:
            code = "".join(self.pre_chunks).strip("\n")
            if code:
                self.lines.append("```")
                self.lines.extend(code.splitlines())
                self.lines.append("```")
                self.lines.append("")
            self.pre_mode = False
            self.pre_chunks = []
            return

        if tag == self.current_tag and tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li"}:
            self._flush_current()

        if tag == "div":
            self.article_div_depth -= 1
            if self.article_div_depth == 0:
                self._flush_current()
                self.in_article_body = False

    def handle_data(self, data: str) -> None:
        if self.capture_title and not self.title:
            title = normalize_ws(data)
            if title:
                self.title = title

        if not self.in_article_body or self.skip_depth:
            return

        if self.pre_mode:
            self.pre_chunks.append(data)
        else:
            self.current_chunks.append(data)

    def _flush_current(self) -> None:
        if not self.current_tag:
            self.current_chunks = []
            return

        text = normalize_ws("".join(self.current_chunks))
        if not text:
            self.current_tag = None
            self.current_chunks = []
            return

        if self.current_tag == "h1":
            self.lines.append(f"# {text}")
        elif self.current_tag == "h2":
            self.lines.append(f"## {text}")
        elif self.current_tag == "h3":
            self.lines.append(f"### {text}")
        elif self.current_tag == "h4":
            self.lines.append(f"#### {text}")
        elif self.current_tag == "h5":
            self.lines.append(f"##### {text}")
        elif self.current_tag == "h6":
            self.lines.append(f"###### {text}")
        elif self.current_tag == "li":
            self.lines.append(f"- {text}")
        else:
            self.lines.append(text)

        self.lines.append("")
        self.current_tag = None
        self.current_chunks = []


def convert_html_to_markdown(html_text: str, source_url: str) -> str:
    parser = DevsiteArticleParser()
    parser.feed(html_text)
    title = parser.title or "AOSP SELinux Reference"
    cleaned_lines: list[str] = []
    seen_title = False
    for line in parser.lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            heading_text = stripped[2:].strip()
            if heading_text == title and not seen_title:
                seen_title = True
                continue
        if should_drop_line(stripped):
            continue
        cleaned_lines.append(line.rstrip())

    body = "\n".join(cleaned_lines).strip()

    return (
        f"# {title}\n\n"
        f"Source: {source_url}\n\n"
        f"Converted from the downloaded AOSP HTML snapshot bundled with this skill.\n\n"
        f"{body}\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_html")
    ap.add_argument("output_md")
    ap.add_argument("--source-url", required=True)
    args = ap.parse_args()

    input_path = Path(args.input_html)
    output_path = Path(args.output_md)
    markdown = convert_html_to_markdown(input_path.read_text(errors="ignore"), args.source_url)
    output_path.write_text(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
