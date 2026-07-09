#!/usr/bin/env python3
"""Build Cambridge catalogue rows from official UG and PG course pages."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "src" / "data" / "cambridgePrograms.ts"
UG_URL = "https://www.undergraduate.study.cam.ac.uk/courses"
PG_URL = "https://www.postgraduate.study.cam.ac.uk/courses"
CHECKED = dt.date.today().isoformat()


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "University-Application-Skill/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Request failed (TLS verification remains enabled) for {url}: {exc}") from exc


def slug_from_url(url: str, prefix: str) -> str:
    path = urllib.parse.urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1]
    slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    return f"{prefix}{slug}"


def parse_ug_award(text: str) -> tuple[str, str]:
    cleaned = " ".join(text.split())
    match = re.match(r"^(.*?), ((?:BA|MB|VetMB|Pre-degree course).*)$", cleaned)
    if not match:
        return cleaned, "UG"
    return match.group(1), match.group(2)


class UndergraduateParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h4_depth = 0
        self.in_link = False
        self.href = ""
        self.text: list[str] = []
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "h4":
            self.h4_depth += 1
        if tag == "a" and self.h4_depth:
            href = attrs_dict.get("href") or ""
            if href.startswith("/courses/"):
                self.in_link = True
                self.href = urllib.parse.urljoin(UG_URL, href)
                self.text = []

    def handle_data(self, data: str) -> None:
        if self.in_link:
            self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_link:
            label = " ".join(" ".join(self.text).split())
            if label:
                name, award = parse_ug_award(label)
                self.rows.append(
                    {
                        "id": slug_from_url(self.href, "cambridge-ug-"),
                        "name": name,
                        "level": "Undergraduate",
                        "award": award,
                        "url": self.href,
                        "note": "Official Cambridge undergraduate course page",
                    }
                )
            self.in_link = False
        if tag == "h4" and self.h4_depth:
            self.h4_depth -= 1


class PostgraduateParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_tr = False
        self.in_td = False
        self.in_a = False
        self.cells: list[dict[str, Any]] = []
        self.current: dict[str, Any] | None = None
        self.rows: list[dict[str, str]] = []
        self.last_page = 0
        self.current_href = ""
        self.current_link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "tr":
            self.in_tr = True
            self.cells = []
        elif tag == "td" and self.in_tr:
            self.in_td = True
            self.current = {"text": [], "link_text": "", "href": ""}
        elif tag == "a":
            href = attrs_dict.get("href") or ""
            if self.in_td and href.startswith("/courses/directory/") and self.current is not None:
                self.in_a = True
                self.current_href = urllib.parse.urljoin(PG_URL, href)
                self.current_link_text = []
            page_match = re.search(r"[?&]page=(\d+)", href)
            if page_match:
                self.last_page = max(self.last_page, int(page_match.group(1)))
        elif tag in {"br", "li"} and self.in_td and self.current is not None:
            self.current["text"].append("\n")

    def handle_data(self, data: str) -> None:
        if self.in_td and self.current is not None:
            self.current["text"].append(data)
        if self.in_a:
            self.current_link_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_a and self.current is not None:
            self.current["href"] = self.current_href
            self.current["link_text"] = " ".join(" ".join(self.current_link_text).split())
            self.in_a = False
        elif tag == "td" and self.in_td and self.current is not None:
            self.current["clean_text"] = clean_text("".join(self.current["text"]))
            self.cells.append(self.current)
            self.current = None
            self.in_td = False
        elif tag == "tr" and self.in_tr:
            self.finish_row()
            self.in_tr = False

    def finish_row(self) -> None:
        if len(self.cells) < 4:
            return
        first = self.cells[0]
        href = first.get("href") or ""
        name = first.get("link_text") or ""
        if not href or not name:
            return

        raw_first = first.get("clean_text", "")
        lines = [line.strip() for line in re.split(r"\n+", raw_first) if line.strip()]
        award = ""
        for line in reversed(lines):
            if line != name and "Closed this cycle" not in line and "EPSRC CDT" not in line:
                award = line
                break
        if not award:
            award = self.cells[1].get("clean_text", "Graduate") or "Graduate"

        status_parts: list[str] = []
        if "Closed this cycle" in raw_first:
            status_parts.append("Closed this cycle")
        if "EPSRC CDT" in raw_first:
            status_parts.append("EPSRC CDT")
        note = "Official Cambridge postgraduate directory row"
        if status_parts:
            note = f"{note}; {'; '.join(status_parts)}"

        self.rows.append(
            {
                "id": slug_from_url(href, "cambridge-pg-"),
                "name": name,
                "level": "Postgraduate",
                "award": award,
                "url": href,
                "note": note,
                "duration": self.cells[3].get("clean_text", "") or "See official programme page",
                "mode": self.cells[2].get("clean_text", "") or "See official programme page",
                "status": "; ".join(status_parts) or "Open in official directory",
            }
        )


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{2,}", "\n", value)
    return value.strip()


def parse_ug() -> list[dict[str, str]]:
    parser = UndergraduateParser()
    parser.feed(fetch(UG_URL))
    rows = dedupe(parser.rows)
    if len(rows) < 30:
        raise RuntimeError(f"Expected at least 30 Cambridge UG course rows, got {len(rows)}")
    return rows


def parse_pg() -> list[dict[str, str]]:
    first_html = fetch(PG_URL)
    first_parser = PostgraduateParser()
    first_parser.feed(first_html)
    rows = list(first_parser.rows)
    last_page = first_parser.last_page

    for page in range(1, last_page + 1):
        parser = PostgraduateParser()
        parser.feed(fetch(f"{PG_URL}?page={page}"))
        rows.extend(parser.rows)

    rows = dedupe(rows)
    if len(rows) < 300:
        raise RuntimeError(f"Expected more than 300 Cambridge PG course rows, got {len(rows)}")
    return rows


def dedupe(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for row in rows:
        key = row["id"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def ts_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_rows(name: str, rows: list[dict[str, str]]) -> str:
    lines = [f"export const {name}: CatalogueProgramOption[] = ["]
    for row in rows:
        fields = [
            f"id: {ts_string(row['id'])}",
            f"name: {ts_string(row['name'])}",
            f"level: {ts_string(row['level'])}",
            f"award: {ts_string(row['award'])}",
            f"url: {ts_string(row['url'])}",
            f"note: {ts_string(row['note'])}",
        ]
        for optional in ["duration", "mode", "status"]:
            if row.get(optional):
                fields.append(f"{optional}: {ts_string(row[optional])}")
        lines.append(f"  {{ {', '.join(fields)} }},")
    lines.append("];")
    return "\n".join(lines)


def main() -> int:
    ug_rows = parse_ug()
    pg_rows = parse_pg()
    output = "\n".join(
        [
            'import type { CatalogueProgramOption } from "../types";',
            "",
            f"export const cambridgeCatalogueChecked = {ts_string(CHECKED)};",
            f"export const cambridgeUndergraduateCount = {len(ug_rows)};",
            f"export const cambridgePostgraduateCount = {len(pg_rows)};",
            "",
            render_rows("cambridgeUndergraduatePrograms", ug_rows),
            "",
            render_rows("cambridgePostgraduatePrograms", pg_rows),
            "",
            "export const cambridgePrograms: CatalogueProgramOption[] = [",
            "  ...cambridgeUndergraduatePrograms,",
            "  ...cambridgePostgraduatePrograms,",
            "];",
            "",
        ]
    )
    OUT.write_text(output, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(ug_rows)} UG rows, {len(pg_rows)} PG rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
