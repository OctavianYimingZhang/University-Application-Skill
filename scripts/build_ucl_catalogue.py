#!/usr/bin/env python3
"""Build UCL catalogue rows from official programme listing pages."""

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
OUT = ROOT / "web" / "src" / "data" / "uclPrograms.ts"
CHECKED = dt.date.today().isoformat()

CATALOGUES = {
    "undergraduate": {
        "url": "https://www.ucl.ac.uk/prospective-students/undergraduate/degrees",
        "path": "/prospective-students/undergraduate/degrees/",
        "prefix": "ucl-ug-",
        "level": "Undergraduate",
        "mode": "Undergraduate",
        "note": "Official UCL undergraduate degree row",
        "minimum": 400,
    },
    "taught": {
        "url": "https://www.ucl.ac.uk/prospective-students/graduate/taught-degrees",
        "path": "/prospective-students/graduate/taught-degrees/",
        "prefix": "ucl-pgt-",
        "level": "Postgraduate",
        "mode": "Taught",
        "note": "Official UCL graduate taught degree row",
        "minimum": 500,
    },
    "research": {
        "url": "https://www.ucl.ac.uk/prospective-students/graduate/research-degrees",
        "path": "/prospective-students/graduate/research-degrees/",
        "prefix": "ucl-pgr-",
        "level": "Postgraduate",
        "mode": "Research",
        "note": "Official UCL graduate research degree row",
        "minimum": 120,
    },
}

AWARD_SUFFIXES = [
    "MPhil/PhD",
    "MPhil/PhD with Integrated Research Methods Training",
    "Doctorate in Clinical Psychology",
    "Doctorate in Educational and Child Psychology",
    "Doctorate in Educational Psychology",
    "Doctorate in Professional Educational, Child and Adolescent Psychology",
    "Doctorate in Psychotherapy",
    "MA (International)",
    "BSc (Econ)",
    "PG Cert",
    "PG Dip",
    "Grad Dip",
    "MClinDent",
    "MSc",
    "MRes",
    "MArch",
    "MPlan",
    "MASc",
    "MFA",
    "MPA",
    "MPH",
    "MBA",
    "MA",
    "LLM",
    "PGCE",
    "EdD",
    "EngD",
    "DClinPsy",
    "DEdPsy",
    "DPsych",
    "DDent",
    "DPA",
    "MD(Res)",
    "PhD",
    "MPhil Stud",
    "MPhil",
    "MLA",
    "MS",
    "MBBS",
    "MPharm",
    "MSci",
    "MEng",
    "BASc",
    "BSc",
    "BEng",
    "BA",
    "BFA",
    "LLB",
    "iBSc",
]


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
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def split_award(title: str) -> tuple[str, str]:
    cleaned = clean_text(title)
    for award in AWARD_SUFFIXES:
        if cleaned == award:
            break
        if cleaned.endswith(f" {award}"):
            name = cleaned[: -len(award)].strip()
            if name:
                return name, award
    return cleaned, "See official programme page"


def id_from_href(prefix: str, href: str) -> str:
    path = urllib.parse.urlparse(href).path.rstrip("/")
    slug = path.split("/")[-1] if path else href
    slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    return f"{prefix}{slug}"


class UclParser(HTMLParser):
    def __init__(self, config: dict[str, str | int]) -> None:
        super().__init__(convert_charrefs=True)
        self.config = config
        self.in_row = False
        self.row_depth = 0
        self.in_link = False
        self.href = ""
        self.text: list[str] = []
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = (attrs_dict.get("class") or "").split()
        if tag == "div" and "result-item" in classes and not self.in_row:
            self.in_row = True
            self.row_depth = 1
            self.in_link = False
            self.href = ""
            self.text = []
            return

        if not self.in_row:
            return

        if tag == "div":
            self.row_depth += 1
        elif tag == "a" and not self.in_link:
            href = attrs_dict.get("href") or ""
            if urllib.parse.urlparse(href).path.startswith(str(self.config["path"])):
                self.in_link = True
                self.href = href
                self.text = []

    def handle_data(self, data: str) -> None:
        if self.in_link:
            self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_row:
            return

        if tag == "a" and self.in_link:
            self.finish_link()
            self.in_link = False
        elif tag == "div":
            self.row_depth -= 1
            if self.row_depth == 0:
                self.in_row = False

    def finish_link(self) -> None:
        title = clean_text("".join(self.text))
        if not title or not self.href:
            return
        name, award = split_award(title)
        self.rows.append(
            {
                "id": id_from_href(str(self.config["prefix"]), self.href),
                "name": name,
                "level": str(self.config["level"]),
                "award": award,
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
        key = row["url"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def parse_catalogue(key: str) -> list[dict[str, str]]:
    config = CATALOGUES[key]
    parser = UclParser(config)
    parser.feed(fetch(str(config["url"])))
    rows = dedupe(parser.rows)
    minimum = int(config["minimum"])
    if len(rows) < minimum:
        raise RuntimeError(f"Expected at least {minimum} UCL {key} rows, got {len(rows)}")
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
    research_rows = parse_catalogue("research")
    output = "\n".join(
        [
            'import type { CatalogueProgramOption } from "../types";',
            "",
            f"export const uclCatalogueChecked = {ts_string(CHECKED)};",
            f"export const uclUndergraduateCount = {len(ug_rows)};",
            f"export const uclTaughtCount = {len(taught_rows)};",
            f"export const uclResearchCount = {len(research_rows)};",
            "",
            render_rows("uclUndergraduatePrograms", ug_rows),
            "",
            render_rows("uclTaughtPrograms", taught_rows),
            "",
            render_rows("uclResearchPrograms", research_rows),
            "",
            "export const uclPrograms: CatalogueProgramOption[] = [",
            "  ...uclUndergraduatePrograms,",
            "  ...uclTaughtPrograms,",
            "  ...uclResearchPrograms,",
            "];",
            "",
        ]
    )
    OUT.write_text(output, encoding="utf-8")
    print(
        f"Wrote {OUT.relative_to(ROOT)}: "
        f"{len(ug_rows)} UG rows, {len(taught_rows)} taught rows, {len(research_rows)} research rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
