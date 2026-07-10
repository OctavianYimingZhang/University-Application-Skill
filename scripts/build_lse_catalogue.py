#!/usr/bin/env python3
"""Build LSE catalogue rows from official programme search and availability pages."""

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
from typing import Any

from catalogue_io import write_programmes

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_ID = "lse"
OUT = ROOT / "catalogues" / "institutions" / f"{CATALOGUE_ID}.json"
CHECKED = dt.date.today().isoformat()
SEARCH_URL = "https://www.lse.ac.uk/programmes/search-courses"
GRADUATE_URL = "https://www.lse.ac.uk/study-at-lse/Graduate/Available-programmes"
API_URL = "https://api-lse.cloud.contensis.com/api/delivery/projects/website/entries/search?linkDepth=1"


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 University-Application-Skill/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Request failed (TLS verification remains enabled) for {url}: {exc}") from exc


def post_json(url: str, payload: dict[str, Any], access_token: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "User-Agent": "Mozilla/5.0 University-Application-Skill/0.1",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "accessToken": access_token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Request failed (TLS verification remains enabled) for {url}: {exc}") from exc


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{2,}", "\n", value)
    return value.strip()


def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def extract_startup_url(search_html: str) -> str:
    match = re.search(r'<script\s+src="([^"]*startup-[^"]+\.js)"', search_html)
    if not match:
        raise RuntimeError("Could not find LSE startup asset on programme search page")
    return urllib.parse.urljoin(SEARCH_URL, match.group(1))


def extract_access_token(startup_js: str) -> str:
    match = re.search(r'accessToken:\s*"([^"]+)"', startup_js)
    if not match:
        match = re.search(r'ACCESS_TOKEN\s*=\s*"([^"]+)"', startup_js)
    if not match:
        raise RuntimeError("Could not find public Contensis access token in LSE startup asset")
    return match.group(1)


def study_type(item: dict[str, Any]) -> str:
    value = item.get("studyType")
    if isinstance(value, dict):
        return str(value.get("entryTitle") or "")
    return str(value or "")


def programme_uri(item: dict[str, Any]) -> str:
    programme = item.get("programme")
    if isinstance(programme, dict):
        sys = programme.get("sys")
        if isinstance(sys, dict) and sys.get("uri"):
            return urllib.parse.urljoin(SEARCH_URL, str(sys["uri"]))
    sys = item.get("sys")
    if isinstance(sys, dict) and sys.get("uri"):
        return urllib.parse.urljoin(SEARCH_URL, str(sys["uri"]))
    return ""


def title_from_item(item: dict[str, Any]) -> str:
    programme = item.get("programme")
    if isinstance(programme, dict) and programme.get("entryTitle"):
        return clean_text(str(programme["entryTitle"]))
    return clean_text(str(item.get("entryTitle") or ""))


LSE_PREFIX_AWARDS = [
    "Executive MSc",
    "Executive Global Master's",
    "MPhil/PhD",
    "MRes/PhD",
    "MSc",
    "MA",
    "LLM",
    "MPA",
    "MPP",
    "MRes",
    "PhD",
    "BA",
    "BSc",
    "LLB",
]


def split_lse_title(title: str) -> tuple[str, str]:
    title = clean_text(title.replace("*NEW*", ""))
    title = re.sub(r"^[A-Z0-9]{4}\s+", "", title).strip()
    if title.startswith("Global Master's"):
        return title, "Master's"
    if title.startswith("Visiting Research Student"):
        return title, "Visiting Research Student"
    for award in LSE_PREFIX_AWARDS:
        if title == award:
            return title, award
        if title.startswith(f"{award} "):
            return title[len(award) + 1 :].strip(), award
    return title, "See official programme page"


def lse_code(raw_title: str) -> str:
    title = clean_text(raw_title.replace("*NEW*", ""))
    match = re.match(r"^([A-Z0-9]{4})\s+", title)
    return match.group(1) if match else ""


def parse_undergraduate_rows() -> list[dict[str, str]]:
    search_html = fetch(SEARCH_URL)
    token = extract_access_token(fetch(extract_startup_url(search_html)))
    payload: dict[str, Any] = {
        "where": [
            {"field": "sys.contentTypeId", "equalTo": "programmeSearchData"},
            {"field": "sys.versionStatus", "equalTo": "published"},
        ],
        "fields": ["entryTitle", "location", "studyType", "summary", "sys.id", "sys.uri", "programme"],
        "pageSize": 300,
        "pageIndex": 0,
        "orderBy": [{"asc": "entryTitle"}],
    }
    result = post_json(API_URL, payload, token)
    rows: list[dict[str, str]] = []
    for item in result.get("items", []):
        if study_type(item) != "Undergraduate":
            continue
        title = title_from_item(item)
        url = programme_uri(item)
        if not title or not url:
            continue
        name, award = split_lse_title(title)
        item_id = f"lse-ug-{slugify(title)}"
        rows.append(
            {
                "id": item_id,
                "name": name,
                "level": "Undergraduate",
                "award": award,
                "url": url,
                "note": "Official LSE programme search API row",
                "duration": "See official programme page",
                "mode": "Undergraduate",
            }
        )
    rows = dedupe(rows)
    if len(rows) != 43:
        raise RuntimeError(f"Expected 43 LSE undergraduate rows, got {len(rows)}")
    return rows


class LSEGraduateParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_section = False
        self.section_depth = 0
        self.section_title = ""
        self.in_h2 = False
        self.h2_text: list[str] = []
        self.in_tr = False
        self.in_cell = False
        self.in_a = False
        self.cells: list[dict[str, str]] = []
        self.cell_text: list[str] = []
        self.href = ""
        self.link_text: list[str] = []
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = (attrs_dict.get("class") or "").split()
        if tag == "section" and "accordion" in classes:
            self.in_section = True
            self.section_depth = 1
            self.section_title = ""
            return
        if self.in_section:
            self.section_depth += 1
        if self.in_section and tag == "h2" and "accordion__title" in classes:
            self.in_h2 = True
            self.h2_text = []
        elif self.in_section and tag == "tr":
            self.in_tr = True
            self.cells = []
        elif self.in_tr and tag in {"td", "th"}:
            self.in_cell = True
            self.cell_text = []
            self.href = ""
            self.link_text = []
        elif self.in_cell and tag == "a":
            href = attrs_dict.get("href") or ""
            if "/study-at-lse/graduate/" in href and "how-to-apply" not in href:
                self.in_a = True
                self.href = urllib.parse.urljoin(GRADUATE_URL, href)
                self.link_text = []
        elif self.in_cell and tag in {"br", "div", "p"}:
            self.cell_text.append("\n")

    def handle_data(self, data: str) -> None:
        if self.in_h2:
            self.h2_text.append(data)
        if self.in_cell:
            self.cell_text.append(data)
        if self.in_a:
            self.link_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.in_h2 and tag == "h2":
            self.section_title = clean_text(" ".join(self.h2_text))
            self.in_h2 = False
        elif self.in_a and tag == "a":
            self.in_a = False
        elif self.in_cell and tag in {"td", "th"}:
            self.cells.append(
                {
                    "text": clean_text("".join(self.cell_text)),
                    "href": self.href,
                    "link": clean_text(" ".join(self.link_text)),
                }
            )
            self.in_cell = False
        elif self.in_tr and tag == "tr":
            self.finish_row()
            self.in_tr = False

        if self.in_section:
            self.section_depth -= 1
            if self.section_depth <= 0:
                self.in_section = False

    def finish_row(self) -> None:
        if len(self.cells) < 3 or not self.cells[0]["href"]:
            return
        raw_title = self.cells[0]["text"]
        code = lse_code(raw_title)
        name, award = split_lse_title(raw_title)
        slug = slugify(f"{code} {name}" if code else name)
        status = f"Home: {self.cells[1]['text']}; Overseas: {self.cells[2]['text']}; Section: {self.section_title}"
        self.rows.append(
            {
                "id": f"lse-pg-{slug}",
                "name": name,
                "level": "Postgraduate",
                "award": award,
                "url": self.cells[0]["href"],
                "note": "Official LSE graduate availability row",
                "duration": "See official programme page",
                "mode": "Research" if "PhD" in award or "Visiting Research" in award else "Taught",
                "status": status,
            }
        )


def parse_graduate_rows() -> list[dict[str, str]]:
    parser = LSEGraduateParser()
    parser.feed(fetch(GRADUATE_URL))
    rows = dedupe(parser.rows)
    if len(rows) < 215:
        raise RuntimeError(f"Expected at least 215 LSE graduate availability rows, got {len(rows)}")
    return rows


def dedupe(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for row in rows:
        key = row["id"]
        if key in seen:
            key = f"{key}-{len(unique)}"
            row = {**row, "id": key}
        seen.add(key)
        unique.append(row)
    return unique


def main() -> int:
    ug_rows = parse_undergraduate_rows()
    graduate_rows = parse_graduate_rows()
    write_programmes(ROOT, CATALOGUE_ID, [*ug_rows, *graduate_rows], CHECKED)
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(ug_rows)} UG rows, {len(graduate_rows)} graduate rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
