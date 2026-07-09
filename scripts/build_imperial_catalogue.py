#!/usr/bin/env python3
"""Build Imperial catalogue rows from official paginated course search pages."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "src" / "data" / "imperialPrograms.ts"
CHECKED = dt.date.today().isoformat()
COURSE_SEARCH_URL = "https://www.imperial.ac.uk/study/courses/"

CATALOGUES = {
    "undergraduate": {
        "course_type": "Undergraduate",
        "prefix": "imperial-ug-",
        "level": "Undergraduate",
        "mode": "Undergraduate",
        "note": "Official Imperial undergraduate course search row",
        "minimum": 50,
    },
    "taught": {
        "course_type": "Postgraduate taught",
        "prefix": "imperial-pgt-",
        "level": "Postgraduate",
        "mode": "Taught",
        "note": "Official Imperial postgraduate taught course search row",
        "minimum": 120,
    },
}

URL_AWARD_SUFFIXES = {
    "bsc": "BSc",
    "msci": "MSci",
    "meng": "MEng",
    "beng": "BEng",
    "mbbs": "MBBS",
}


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 University-Application-Skill/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Request failed (TLS verification remains enabled) for {url}: {exc}") from exc


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def id_from_url(prefix: str, url: str) -> str:
    path = urllib.parse.urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1] if path else url
    slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    return f"{prefix}{slug}"


def award_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1].lower() if path else ""
    for suffix, award in URL_AWARD_SUFFIXES.items():
        if slug.endswith(f"-{suffix}") or slug == suffix:
            return award
    return "See official programme page"


class ImperialParser(HTMLParser):
    def __init__(self, config: dict[str, str | int]) -> None:
        super().__init__(convert_charrefs=True)
        self.config = config
        self.in_title = False
        self.in_title_link = False
        self.href = ""
        self.text: list[str] = []
        self.rows: list[dict[str, str]] = []
        self.last_page = 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = (attrs_dict.get("class") or "").split()
        if tag in {"h3", "h4"} and "course-card__title" in classes:
            self.in_title = True
        elif tag == "a":
            href = attrs_dict.get("href") or ""
            page_match = re.search(r"[?&]page=(\d+)", href)
            if page_match:
                self.last_page = max(self.last_page, int(page_match.group(1)))
            if self.in_title and href.startswith("/study/courses/"):
                self.in_title_link = True
                self.href = urllib.parse.urljoin(COURSE_SEARCH_URL, href)
                self.text = []

    def handle_data(self, data: str) -> None:
        if self.in_title_link:
            self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_title_link:
            self.finish_row()
            self.in_title_link = False
        elif tag in {"h3", "h4"} and self.in_title:
            self.in_title = False

    def finish_row(self) -> None:
        name = clean_text("".join(self.text))
        if not name or not self.href:
            return
        self.rows.append(
            {
                "id": id_from_url(str(self.config["prefix"]), self.href),
                "name": name,
                "level": str(self.config["level"]),
                "award": award_from_url(self.href),
                "url": self.href,
                "note": str(self.config["note"]),
                "duration": "See official programme page",
                "mode": str(self.config["mode"]),
            }
        )


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
    course_type = urllib.parse.quote(str(config["course_type"]))
    first = fetch(f"{COURSE_SEARCH_URL}?courseType={course_type}")
    parser = ImperialParser(config)
    parser.feed(first)
    rows = list(parser.rows)
    for page in range(2, parser.last_page + 1):
        page_parser = ImperialParser(config)
        page_parser.feed(fetch(f"{COURSE_SEARCH_URL}?courseType={course_type}&page={page}"))
        rows.extend(page_parser.rows)
    rows = dedupe(rows)
    minimum = int(config["minimum"])
    if len(rows) < minimum:
        raise RuntimeError(f"Expected at least {minimum} Imperial {key} rows, got {len(rows)}")
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
    taught_rows = parse_catalogue("taught")
    output = "\n".join(
        [
            'import type { CatalogueProgramOption } from "../types";',
            "",
            f"export const imperialCatalogueChecked = {ts_string(CHECKED)};",
            f"export const imperialUndergraduateCount = {len(ug_rows)};",
            f"export const imperialTaughtCount = {len(taught_rows)};",
            "",
            render_rows("imperialUndergraduatePrograms", ug_rows),
            "",
            render_rows("imperialTaughtPrograms", taught_rows),
            "",
            "export const imperialPrograms: CatalogueProgramOption[] = [",
            "  ...imperialUndergraduatePrograms,",
            "  ...imperialTaughtPrograms,",
            "];",
            "",
        ]
    )
    OUT.write_text(output, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(ug_rows)} UG rows, {len(taught_rows)} taught rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
