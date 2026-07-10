#!/usr/bin/env python3
"""Build Edinburgh catalogue rows from official Degree Finder A-Z pages."""

from __future__ import annotations

import datetime as dt
import html
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from catalogue_io import write_programmes

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_ID = "edinburgh"
OUT = ROOT / "catalogues" / "institutions" / f"{CATALOGUE_ID}.json"
BASE_URL = "https://study.ed.ac.uk"
CHECKED = dt.date.today().isoformat()

CATALOGUES = {
    "undergraduate": {
        "url": "https://study.ed.ac.uk/programmes/undergraduate-a-z",
        "prefix": "edinburgh-ug-",
        "level": "Undergraduate",
        "route": "Undergraduate",
        "note": "Official Edinburgh undergraduate Degree Finder row",
        "minimum": 300,
    },
    "taught": {
        "url": "https://study.ed.ac.uk/programmes/postgraduate-taught-a-z",
        "prefix": "edinburgh-pgt-",
        "level": "Postgraduate",
        "route": "Taught",
        "note": "Official Edinburgh postgraduate taught Degree Finder row",
        "minimum": 250,
    },
    "research": {
        "url": "https://study.ed.ac.uk/programmes/postgraduate-research-a-z",
        "prefix": "edinburgh-pgr-",
        "level": "Postgraduate",
        "route": "Research",
        "note": "Official Edinburgh postgraduate research Degree Finder row",
        "minimum": 150,
    },
}

AWARD_SUFFIXES = [
    "PhD with Integrated Study, EngD",
    "Professional Graduate Diploma",
    "PhD with Integrated Study",
    "MVetSci, PgDip (ICL), PgCert (ICL), PgProfDev",
    "MSc, PgDip (ICL), PgCert (ICL), PgCert, PgDip, PgProfDev",
    "PgCert, PgDip, MSc, PgCert (ICL), PgDip (ICL), PgProfDev",
    "MSc, PgDip (ICL), PgCert (ICL), PgProfDev",
    "MSc, PgDip (ICL), PgCert (ICL)",
    "MSc, PgDip (ICL)",
    "MSc, PgCert, PgDip, PgProfDev",
    "MSc, PgDip, PgCert, PgProfDev",
    "PgDip (ICL), PgCert (ICL), PgCert, PgDip, PgProfDev",
    "PgDip (ICL), PgCert (ICL), PgProfDev",
    "PgCert (ICL), PgProfDev",
    "PgCert (ICL)",
    "PgCert, PgProfDev",
    "PhD, MScR",
    "MPhil, MScR",
    "MSc, PgDip, PgCert",
    "LLM, PgDip",
    "LLM by Research",
    "MSc by Research",
    "LLB (Hons), LLB (Ord)",
    "BEng/MEng (Hons)",
    "BA/MA (Hons)",
    "MA (Hons)",
    "BA (Hons)",
    "BSc (Hons)",
    "BEng (Hons)",
    "MEng (Hons)",
    "MPhys (Hons)",
    "MChem (Hons)",
    "MMath (Hons)",
    "LLB (Hons)",
    "BA (Ord)",
    "LLB (Ord)",
    "BN (Hons)",
    "MArch ARB Pt 2",
    "MA (eca)",
    "MA, PgDip",
    "MSc, PgDip",
    "PgDip, PgCert",
    "PGDE",
    "DClinDent",
    "DClinPsychol",
    "DPsychotherapy",
    "DVetMed",
    "DProf",
    "DPT",
    "MD",
    "ChM",
    "EngD",
    "PhD",
    "MScR",
    "MPhil",
    "MRes",
    "MSc",
    "MPhys",
    "MChemPhys",
    "MChem",
    "MEarthSci",
    "MBiol",
    "MMus",
    "MLA",
    "MN(T)",
    "MFM",
    "MCouns",
    "MFA",
    "MEd",
    "MTh",
    "LLM",
    "MBA",
    "MPH",
    "MSW",
    "MInf",
    "MA",
    "BA",
    "BSc",
    "BEng",
    "MEng",
    "BMus",
    "MBChB",
    "BVM&S",
    "BMedSci",
    "Diploma",
    "PgDip",
    "PgCert",
    "PgProfDev",
]


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "University-Application-Skill/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Request failed (TLS verification remains enabled) for {url}: {exc}") from exc


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{2,}", "\n", value)
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


class EdinburghParser(HTMLParser):
    def __init__(self, config: dict[str, str | int]) -> None:
        super().__init__(convert_charrefs=True)
        self.config = config
        self.in_row = False
        self.row_depth = 0
        self.field: str | None = None
        self.field_depth = 0
        self.in_title_link = False
        self.title_href = ""
        self.title_text: list[str] = []
        self.values: dict[str, list[str]] = {}
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = (attrs_dict.get("class") or "").split()
        if tag == "div" and "views-row" in classes and not self.in_row:
            self.in_row = True
            self.row_depth = 1
            self.field = None
            self.field_depth = 0
            self.in_title_link = False
            self.title_href = ""
            self.title_text = []
            self.values = {"level": [], "year": [], "duration": [], "delivery": [], "summary": []}
            return

        if not self.in_row:
            return

        if tag == "div":
            self.row_depth += 1
        if tag == "div" and "views-field" in classes:
            mapped = self.map_field(classes)
            if mapped:
                self.field = mapped
                self.field_depth = 1
        elif tag == "a" and self.field == "title":
            self.title_href = urllib.parse.urljoin(BASE_URL, attrs_dict.get("href") or "")
            self.in_title_link = True
        elif self.field:
            self.field_depth += 1

    def handle_data(self, data: str) -> None:
        if not self.in_row:
            return
        if self.in_title_link:
            self.title_text.append(data)
        elif self.field and self.field != "title":
            self.values.setdefault(self.field, []).append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_row:
            return

        if tag == "a" and self.in_title_link:
            self.in_title_link = False

        if self.field_depth and self.field:
            self.field_depth -= 1
            if self.field_depth == 0:
                self.field = None

        if tag == "div":
            self.row_depth -= 1
            if self.row_depth == 0:
                self.finish_row()
                self.in_row = False

    @staticmethod
    def map_field(classes: list[str]) -> str | None:
        if "views-field-title" in classes:
            return "title"
        if "views-field-field-psw-study-level-ref" in classes:
            return "level"
        if "views-field-field-psw-year-of-entry" in classes:
            return "year"
        if "views-field-field-psw-study-duration" in classes:
            return "duration"
        if "views-field-field-psw-delivery" in classes or "views-field-psw-pg-delivery-field" in classes:
            return "delivery"
        if "views-field-field-summary" in classes:
            return "summary"
        return None

    def finish_row(self) -> None:
        title = clean_text("".join(self.title_text))
        if not title or not self.title_href:
            return
        name, award = split_award(title)
        duration = remove_label(clean_text("".join(self.values.get("duration", []))), "Duration:")
        delivery = remove_label(clean_text("".join(self.values.get("delivery", []))), "Study mode:")
        delivery = remove_label(delivery, "Delivery:")
        mode = str(self.config["route"])
        if delivery:
            mode = f"{mode}; {delivery}"

        self.rows.append(
            {
                "id": id_from_href(str(self.config["prefix"]), self.title_href),
                "name": name,
                "level": str(self.config["level"]),
                "award": award,
                "url": self.title_href,
                "note": str(self.config["note"]),
                "duration": duration or "See official programme page",
                "mode": mode,
            }
        )


def remove_label(value: str, label: str) -> str:
    if value.startswith(label):
        return value[len(label) :].strip()
    return value


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
    parser = EdinburghParser(config)
    parser.feed(fetch(str(config["url"])))
    rows = dedupe(parser.rows)
    minimum = int(config["minimum"])
    if len(rows) < minimum:
        raise RuntimeError(f"Expected at least {minimum} Edinburgh {key} rows, got {len(rows)}")
    return rows


def main() -> int:
    ug_rows = parse_catalogue("undergraduate")
    taught_rows = parse_catalogue("taught")
    research_rows = parse_catalogue("research")
    write_programmes(ROOT, CATALOGUE_ID, [*ug_rows, *taught_rows, *research_rows], CHECKED)
    print(
        f"Wrote {OUT.relative_to(ROOT)}: "
        f"{len(ug_rows)} UG rows, {len(taught_rows)} taught rows, {len(research_rows)} research rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
