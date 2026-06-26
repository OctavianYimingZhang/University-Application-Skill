#!/usr/bin/env python3
"""Build Manchester catalogue rows from official course-list XML fragments."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "src" / "data" / "manchesterPrograms.ts"
CHECKED = dt.date.today().isoformat()

CATALOGUES = {
    "undergraduate": {
        "url": "https://www.manchester.ac.uk/study/undergraduate/courses/2026/xml/",
        "base": "https://www.manchester.ac.uk/study/undergraduate/courses/2026/",
        "prefix": "manchester-ug-",
        "level": "Undergraduate",
        "mode": "Undergraduate",
        "note": "Official Manchester undergraduate XML row",
        "minimum": 350,
    },
    "masters": {
        "url": "https://www.manchester.ac.uk/study/masters/courses/list/xml/",
        "base": "https://www.manchester.ac.uk/study/masters/courses/list/",
        "prefix": "manchester-pgt-",
        "level": "Postgraduate",
        "mode": "Taught",
        "note": "Official Manchester masters XML row",
        "minimum": 250,
    },
    "research": {
        "url": "https://www.manchester.ac.uk/study/postgraduate-research/programmes/list/xml/",
        "base": "https://www.manchester.ac.uk/study/postgraduate-research/programmes/list/",
        "prefix": "manchester-pgr-",
        "level": "Postgraduate",
        "mode": "Research",
        "note": "Official Manchester postgraduate research XML row",
        "minimum": 200,
    },
}


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "University-Application-Skill/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except urllib.error.URLError:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(request, timeout=30, context=context) as response:
            return response.read().decode("utf-8", "replace")


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{2,}", "\n", value)
    return value.strip()


def id_from_href(prefix: str, href: str, li_id: str) -> str:
    if li_id.startswith("id") and li_id[2:].isdigit():
        return f"{prefix}{li_id[2:]}"
    path = urllib.parse.urlparse(href).path.rstrip("/")
    parts = [part for part in path.split("/") if part]
    if parts and parts[-2:-1] and parts[-2].isdigit():
        return f"{prefix}{parts[-2]}"
    slug = re.sub(r"[^a-z0-9]+", "-", (parts[-1] if parts else href).lower()).strip("-")
    return f"{prefix}{slug}"


class ManchesterListParser(HTMLParser):
    def __init__(self, config: dict[str, str | int]) -> None:
        super().__init__(convert_charrefs=True)
        self.config = config
        self.in_li = False
        self.li_id = ""
        self.alias = False
        self.field: str | None = None
        self.in_link = False
        self.href = ""
        self.skip_depth = 0
        self.values: dict[str, list[str]] = {}
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "li":
            self.in_li = True
            self.li_id = attrs_dict.get("id") or ""
            self.alias = "alias" in (attrs_dict.get("class") or "").split()
            self.field = None
            self.in_link = False
            self.href = ""
            self.skip_depth = 0
            self.values = {"title": [], "degree": [], "duration": [], "ucas": []}
            return

        if not self.in_li:
            return

        if tag == "div":
            classes = (attrs_dict.get("class") or "").split()
            for candidate in ("title", "degree", "duration", "ucas"):
                if candidate in classes:
                    self.field = candidate
                    break
        elif tag == "a" and self.field == "title":
            href = attrs_dict.get("href") or ""
            self.href = urllib.parse.urljoin(str(self.config["base"]), href)
            self.in_link = True
        elif tag == "span" and "screenreader" in (attrs_dict.get("class") or "").split():
            self.skip_depth += 1

    def handle_data(self, data: str) -> None:
        if self.in_li and self.field and self.skip_depth == 0:
            self.values[self.field].append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_li:
            return

        if tag == "span" and self.skip_depth:
            self.skip_depth -= 1
        elif tag == "a" and self.in_link:
            self.in_link = False
        elif tag == "div":
            self.field = None
        elif tag == "li":
            self.finish_row()
            self.in_li = False

    def finish_row(self) -> None:
        name = clean_text("".join(self.values.get("title", [])))
        award = clean_text("".join(self.values.get("degree", []))) or "See official programme page"
        duration = clean_text("".join(self.values.get("duration", []))) or "See official programme page"
        if not name or not self.href:
            return

        note = str(self.config["note"])
        status = ""
        if self.alias:
            note = f"{note}; alias row"
            status = "Alias row"

        row = {
            "id": id_from_href(str(self.config["prefix"]), self.href, self.li_id),
            "name": name,
            "level": str(self.config["level"]),
            "award": award,
            "url": self.href,
            "note": note,
            "duration": duration,
            "mode": str(self.config["mode"]),
        }
        if status:
            row["status"] = status
        self.rows.append(row)


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


def parse_catalogue(key: str) -> list[dict[str, str]]:
    config = CATALOGUES[key]
    parser = ManchesterListParser(config)
    parser.feed(fetch(str(config["url"])))
    rows = dedupe(parser.rows)
    minimum = int(config["minimum"])
    if len(rows) < minimum:
        raise RuntimeError(f"Expected at least {minimum} Manchester {key} rows, got {len(rows)}")
    return rows


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
    ug_rows = parse_catalogue("undergraduate")
    masters_rows = parse_catalogue("masters")
    research_rows = parse_catalogue("research")
    output = "\n".join(
        [
            'import type { CatalogueProgramOption } from "../types";',
            "",
            f"export const manchesterCatalogueChecked = {ts_string(CHECKED)};",
            f"export const manchesterUndergraduateCount = {len(ug_rows)};",
            f"export const manchesterMastersCount = {len(masters_rows)};",
            f"export const manchesterResearchCount = {len(research_rows)};",
            "",
            render_rows("manchesterUndergraduatePrograms", ug_rows),
            "",
            render_rows("manchesterMastersPrograms", masters_rows),
            "",
            render_rows("manchesterResearchPrograms", research_rows),
            "",
            "export const manchesterPrograms: CatalogueProgramOption[] = [",
            "  ...manchesterUndergraduatePrograms,",
            "  ...manchesterMastersPrograms,",
            "  ...manchesterResearchPrograms,",
            "];",
            "",
        ]
    )
    OUT.write_text(output, encoding="utf-8")
    print(
        f"Wrote {OUT.relative_to(ROOT)}: "
        f"{len(ug_rows)} UG rows, {len(masters_rows)} masters rows, {len(research_rows)} research rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
