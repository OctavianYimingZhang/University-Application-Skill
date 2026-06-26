#!/usr/bin/env python3
"""Build Warwick catalogue rows from official SiteBuilder data and PG course page."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import ssl
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "src" / "data" / "warwickPrograms.ts"
CHECKED = dt.date.today().isoformat()

UG_API_URL = "https://sitebuilder.warwick.ac.uk/sitebuilder2/api/dataentry/entries.json?page=%2Fstudy%2Fundergraduate%2Fcourses%2Fcourse-list"
UG_BASE_URL = "https://warwick.ac.uk/study/undergraduate/courses/"
PG_URL = "https://warwick.ac.uk/study/postgraduate/courses/"

AWARD_SUFFIXES = [
    "MPhil/PhD",
    "MASt",
    "MASc/PGDip",
    "MSc/PGDip",
    "PGDip/MSc",
    "MSc/PGCert",
    "LLM",
    "MSc",
    "MRes",
    "MA",
    "MBA",
    "MPA",
    "PGCert",
    "PGDip",
    "PhD",
    "MPhil",
    "MBChB",
    "MMathPhys",
    "MMathStat",
    "MMORSE",
    "MEng",
    "MBio",
    "MChem",
    "MMath",
    "MPhys",
    "MSci",
    "BEng",
    "BA/BSc",
    "BASc",
    "BSc",
    "BA",
    "LLB",
]


def fetch(url: str, referer: str | None = None) -> str:
    headers = {"User-Agent": "Mozilla/5.0 University-Application-Skill/0.1"}
    if referer:
        headers["Referer"] = referer
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except urllib.error.URLError:
        context = ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(request, timeout=30, context=context) as response:
                return response.read().decode("utf-8", "replace")
        except Exception:
            result = subprocess.run(
                ["curl", "-L", "-A", headers["User-Agent"], url],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def split_award(title: str) -> tuple[str, str]:
    cleaned = clean_text(title)
    cleaned = re.sub(r"\s+Part-time$", "", cleaned)
    if cleaned.startswith("MSc in ") and len(cleaned) > len("MSc in "):
        return cleaned[len("MSc in ") :].strip(), "MSc"
    paren = re.search(r"\(([^()]+)\)$", cleaned)
    if paren:
        award = paren.group(1).strip()
        name = cleaned[: paren.start()].strip()
        if name and award:
            return name, award
    for award in AWARD_SUFFIXES:
        if cleaned == award:
            break
        if cleaned.endswith(f" {award}"):
            name = cleaned[: -len(award)].strip()
            if name:
                return name, award
    return cleaned, "See official programme page"


def id_from_url(prefix: str, url: str) -> str:
    path = urllib.parse.urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1] if path else url
    slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    return f"{prefix}{slug}"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_h3 = False
        self.in_link = False
        self.href = ""
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "h3":
            self.in_h3 = True
        elif tag == "a" and self.in_h3:
            self.in_link = True
            self.href = attrs_dict.get("href") or ""
            self.text = []

    def handle_data(self, data: str) -> None:
        if self.in_link:
            self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_link:
            self.in_link = False
        elif tag == "h3":
            self.in_h3 = False


def text_from_html(value: str) -> str:
    return clean_text(re.sub(r"<[^>]+>", " ", value))


def duration_from_body(body: str) -> str:
    text = text_from_html(body)
    match = re.search(r"Duration\s+(.+?)(?:\s+(?:Faculty|Qualification|Study mode|Study option|Subject area):|$)", text)
    if match:
        return match.group(1).strip()
    return "See official programme page"


def mode_from_categories(categories: list[object], fallback: str) -> str:
    labels = [category if isinstance(category, str) else str(category.get("name", "")) for category in categories if category]
    modes: list[str] = []
    for label in labels:
        if label.startswith("Study mode:"):
            modes.append(label.split(":", 1)[1].split("(", 1)[0].strip())
        if label.startswith("Study option:"):
            option = label.split(":", 1)[1].split("(", 1)[0].strip()
            if option and option != "Single subject":
                modes.append(option)
    return "; ".join(dict.fromkeys(modes)) or fallback


def parse_ug() -> list[dict[str, str]]:
    data = json.loads(fetch(UG_API_URL, referer=UG_BASE_URL))
    rows: list[dict[str, str]] = []
    for item in data.get("items", []):
        categories = item.get("categories") or []
        category_labels = [category if isinstance(category, str) else category.get("name", "") for category in categories]
        if "Visibility: Hidden" in category_labels:
            continue

        body = item.get("parsedContentBody") or ""
        parser = LinkParser()
        parser.feed(body)
        title = clean_text("".join(parser.text)) or clean_text(item.get("title") or "")
        href = urllib.parse.urljoin(UG_BASE_URL, parser.href)
        if title == "Missing content block":
            continue
        if not title or not href:
            continue
        name, award = split_award(title)
        rows.append(
            {
                "id": id_from_url("warwick-ug-", href),
                "name": name,
                "level": "Undergraduate",
                "award": award,
                "url": href,
                "note": "Official Warwick undergraduate SiteBuilder API row",
                "duration": duration_from_body(body),
                "mode": mode_from_categories(categories, "Undergraduate"),
            }
        )

    rows = dedupe(rows)
    if len(rows) < 180:
        raise RuntimeError(f"Expected at least 180 Warwick UG rows, got {len(rows)}")
    return rows


class PgParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_link = False
        self.href = ""
        self.text: list[str] = []
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "a":
            href = attrs_dict.get("href") or ""
            if href.startswith("https://warwick.ac.uk/study/postgraduate/courses/") and not href.rstrip("/").endswith("/course-list"):
                self.in_link = True
                self.href = href
                self.text = []

    def handle_data(self, data: str) -> None:
        if self.in_link:
            self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_link:
            title = clean_text("".join(self.text))
            if title:
                name, award = split_award(title)
                route = "Research" if any(token in award for token in ["PhD", "MPhil", "MRes"]) else "Taught"
                self.rows.append(
                    {
                        "id": id_from_url("warwick-pg-", self.href),
                        "name": name,
                        "level": "Postgraduate",
                        "award": award,
                        "url": self.href,
                        "note": "Official Warwick postgraduate course page row",
                        "duration": "See official programme page",
                        "mode": route,
                    }
                )
            self.in_link = False


def parse_pg() -> list[dict[str, str]]:
    parser = PgParser()
    parser.feed(fetch(PG_URL))
    rows = dedupe(parser.rows)
    if len(rows) < 240:
        raise RuntimeError(f"Expected at least 240 Warwick PG rows, got {len(rows)}")
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
            f"export const warwickCatalogueChecked = {ts_string(CHECKED)};",
            f"export const warwickUndergraduateCount = {len(ug_rows)};",
            f"export const warwickPostgraduateCount = {len(pg_rows)};",
            "",
            render_rows("warwickUndergraduatePrograms", ug_rows),
            "",
            render_rows("warwickPostgraduatePrograms", pg_rows),
            "",
            "export const warwickPrograms: CatalogueProgramOption[] = [",
            "  ...warwickUndergraduatePrograms,",
            "  ...warwickPostgraduatePrograms,",
            "];",
            "",
        ]
    )
    OUT.write_text(output, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(ug_rows)} UG rows, {len(pg_rows)} PG rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
