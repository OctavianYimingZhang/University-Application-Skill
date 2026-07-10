#!/usr/bin/env python3
"""Build conservative US and Singapore programme catalogues from official sources."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup

from catalogue_io import rebuild_index, write_programmes

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_DIR = ROOT / "catalogues" / "institutions"
CHECKED = dt.date.today().isoformat()
UA = "Mozilla/5.0 University-Application-Skill/0.1"


def read_request(request: urllib.request.Request, *, timeout: int) -> str:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Request failed (TLS verification remains enabled) for {request.full_url}: {exc}") from exc


def fetch(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/json",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    return read_request(request, timeout=35)


def fetch_json(url: str) -> dict:
    return json.loads(fetch(url))


def soup(url: str) -> BeautifulSoup:
    data = fetch(url)
    if "Just a moment" in data or "_Incapsula_Resource" in data or "Human Verification" in data:
        raise RuntimeError(f"Source challenge detected for {url}")
    return BeautifulSoup(data, "lxml")


def decode_nuxt_payload(page: BeautifulSoup) -> dict:
    script = page.find("script", id="__NUXT_DATA__")
    if script is None or not script.string:
        raise RuntimeError("Nuxt payload not found")
    payload = json.loads(script.string)
    cache: dict[int, object] = {}
    resolving: set[int] = set()

    def resolve_value(value):
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, int):
            return resolve_index(value) if 0 <= value < len(payload) else value
        if isinstance(value, list):
            if value and value[0] in {"Reactive", "ShallowReactive", "Ref", "ComputedRef"}:
                return resolve_value(value[1]) if len(value) > 1 else None
            if value and value[0] == "Set":
                return [resolve_value(item) for item in value[1:]]
            return [resolve_value(item) for item in value]
        if isinstance(value, dict):
            return {key: resolve_value(item) for key, item in value.items()}
        return value

    def resolve_index(index: int):
        if index in cache:
            return cache[index]
        if index in resolving:
            return None
        resolving.add(index)
        output = resolve_value(payload[index])
        resolving.remove(index)
        cache[index] = output
        return output

    root = resolve_index(0)
    if not isinstance(root, dict):
        raise RuntimeError("Nuxt payload root did not decode to an object")
    return root


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = value.replace("\u00ad", "")
    value = re.sub(r"[\u00a0\t\r\f\v]+", " ", value)
    value = re.sub(r" *\n *", " ", value)
    return re.sub(r" {2,}", " ", value).strip()


def clean_coursedog_text(value: str) -> str:
    text = clean_text(value).strip("\"' ")
    return (
        text.replace("Acad/Prfnl", "Academic/Professional")
        .replace("Dsgntd Emph", "Designated Emphasis")
        .strip()
    )


def slug(value: str) -> str:
    value = clean_text(value).lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "programme"


def absolute(base: str, href: str) -> str:
    return urllib.parse.urljoin(base, href)


def award_from_text(text: str, default: str) -> str:
    text = clean_text(text)
    paren = re.search(r"\(([^()]{1,80})\)\s*$", text)
    if paren:
        return clean_text(paren.group(1))
    comma = re.search(r",\s*([A-Z][A-Za-z./& -]{1,45})(?::|$)", text)
    if comma:
        return clean_text(comma.group(1))
    if "Minor" in text:
        return "Minor"
    if "Major" in text:
        return "Major"
    return default


UG_MARKERS = [
    "Bachelor",
    "A.B.",
    "S.B.",
    "A.L.B.",
    "BA",
    "BS",
    "BSc",
    "B.S.",
    "B.A.",
    "BBA",
    "BFA",
    "BMus",
    "Minor",
    "Major",
    "Undergraduate",
]

PG_MARKERS = [
    "Master",
    "M.A.",
    "M.S.",
    "MSc",
    "MBA",
    "M.B.A.",
    "MEng",
    "M.P.P.",
    "PhD",
    "Ph.D.",
    "Doctor",
    "DNP",
    "JD",
    "J.D.",
    "LLM",
    "LL.M.",
    "MD",
    "M.D.",
    "Graduate",
    "Post-Master",
    "Certificate",
]


def infer_level(award: str, name: str = "") -> str | None:
    combined = f"{award} {name}"
    if any(marker in combined for marker in UG_MARKERS):
        return "Undergraduate"
    if any(marker in combined for marker in PG_MARKERS):
        return "Postgraduate"
    return None


def row(
    institution: str,
    prefix: str,
    level: str,
    name: str,
    award: str,
    url: str,
    note: str,
    *,
    mode: str = "",
    duration: str = "",
    status: str = "",
) -> dict[str, str]:
    name = clean_text(name)
    award = clean_text(award) or "See official programme page"
    fields = {
        "id": f"{prefix}-{level.lower()[:2]}-{slug(name)}-{slug(award)}",
        "name": name,
        "level": level,
        "award": award,
        "url": url,
        "note": note,
    }
    if mode:
        fields["mode"] = clean_text(mode)
    if duration:
        fields["duration"] = clean_text(duration)
    if status:
        fields["status"] = clean_text(status)
    return fields


def dedupe(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    output: list[dict[str, str]] = []
    for item in rows:
        if not item["name"] or item["name"] in set("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            continue
        key = item["id"]
        if key in seen:
            suffix = slug(item["url"].rstrip("/").split("/")[-1])
            key = f"{key}-{suffix}"
            item = {**item, "id": key}
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def link_rows(
    prefix: str,
    level: str,
    source_url: str,
    selector: str,
    note: str,
    *,
    default_award: str,
    href_contains: str | None = None,
    exclude_same_path: bool = True,
    minimum: int = 1,
) -> list[dict[str, str]]:
    page = soup(source_url)
    source_path = urllib.parse.urlparse(source_url).path.rstrip("/")
    rows: list[dict[str, str]] = []
    for anchor in page.select(selector):
        text = clean_text(anchor.get_text(" ", strip=True))
        href = anchor.get("href") or ""
        if not text or href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        url = absolute(source_url, href)
        path = urllib.parse.urlparse(url).path.rstrip("/")
        if exclude_same_path and path == source_path:
            continue
        if href_contains and href_contains not in url:
            continue
        rows.append(row("", prefix, level, text, award_from_text(text, default_award), url, note))
    rows = dedupe(rows)
    if len(rows) < minimum:
        raise RuntimeError(f"Expected at least {minimum} rows from {source_url}, got {len(rows)}")
    return rows


def parse_harvard(level: str) -> list[dict[str, str]]:
    endpoint = "https://www.harvard.edu/wp-json/tribe-core/v1/program-browser"
    records: dict[str, dict] = {}
    expected: int | None = None
    degree = "undergraduate" if level == "Undergraduate" else "graduate"
    for page in range(1, 20):
        params = urllib.parse.urlencode({"degree_levels": degree, "page": page})
        payload = fetch_json(f"{endpoint}?{params}")
        if expected is None:
            expected = int(payload["meta"]["pagination"].get("total_results") or 0)
        page_records = payload.get("records") or []
        if not page_records:
            break
        for record in page_records:
            records[str(record["id"])] = record
        if expected and len(records) >= expected:
            break
    if expected and len(records) != expected:
        raise RuntimeError(f"Harvard {degree} expected {expected} records, got {len(records)}")

    rows: list[dict[str, str]] = []
    for record in records.values():
        certs = record.get("certifications") or []
        if level == "Undergraduate":
            awards = [c.get("initials") or c.get("name") for c in certs if "Bachelor" in c.get("name", "") or c.get("initials") in {"A.B.", "S.B.", "A.L.B."}]
        else:
            awards = [c.get("initials") or c.get("name") for c in certs if "Bachelor" not in c.get("name", "") and c.get("initials") not in {"A.B.", "S.B.", "A.L.B."}]
        rows.append(
            row(
                "",
                "harvard",
                level,
                record["name"],
                ", ".join(a for a in awards if a) or ("UG" if level == "Undergraduate" else "Graduate"),
                record["route"],
                "Official Harvard Program Browser API row",
                mode="Program Browser",
            )
        )
    return dedupe(rows)


def parse_mit() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    source_url = "https://catalog.mit.edu/degree-charts/"
    page = soup(source_url)
    output: dict[str, list[dict[str, str]]] = {"Undergraduate": [], "Postgraduate": []}
    ids = {
        "Undergraduate": "undergraduatedegreestextcontainer",
        "Postgraduate": "graduatedegreestextcontainer",
    }
    for level, container_id in ids.items():
        container = page.find(id=container_id)
        if container is None:
            raise RuntimeError(f"MIT missing {container_id}")
        for anchor in container.select('a[href*="/degree-charts/"]'):
            text = clean_text(anchor.get_text(" ", strip=True))
            url = absolute(source_url, anchor.get("href") or "")
            if not text or url.rstrip("/") == source_url.rstrip("/"):
                continue
            award = award_from_text(text, "Degree chart")
            if level == "Undergraduate" and award.startswith("Course"):
                award = "Undergraduate degree chart"
            output[level].append(row("", "mit", level, text, award, url, "Official MIT degree chart row"))
    if len(output["Undergraduate"]) < 40 or len(output["Postgraduate"]) < 35:
        raise RuntimeError("MIT degree chart counts below expected threshold")
    return dedupe(output["Undergraduate"]), dedupe(output["Postgraduate"])


def parse_jhu() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    source_url = "https://e-catalogue.jhu.edu/programs/"
    page = soup(source_url)
    ug: list[dict[str, str]] = []
    pg: list[dict[str, str]] = []
    for item in page.select("li.item"):
        title = item.select_one(".title")
        link = item.select_one("a[href]")
        if not title or not link:
            continue
        name = clean_text(title.get_text(" ", strip=True))
        keywords = [clean_text(node.get_text(" ", strip=True)) for node in item.select(".keyword")]
        keyword_text = "; ".join(keywords)
        if "Bachelor's" in keywords or "Minors" in keywords:
            level = "Undergraduate"
        elif any(k in keyword_text for k in ["Master", "Doctoral", "Certificate", "Post-Master"]):
            level = "Postgraduate"
        else:
            continue
        award = next((k for k in keywords if k in {"Bachelor's", "Master's", "Doctoral", "Certificate", "Minors"} or "Certificate" in k), award_from_text(name, "Program"))
        target = ug if level == "Undergraduate" else pg
        target.append(
            row(
                "",
                "jhu",
                level,
                name,
                award,
                absolute(source_url, link.get("href") or ""),
                "Official Johns Hopkins Program Explorer row",
                mode="; ".join(k for k in keywords if k in {"Full-time", "Part-time", "Online", "In-person", "Hybrid"}) or "See official programme page",
                status=keyword_text,
            )
        )
    if len(ug) < 100 or len(pg) < 250:
        raise RuntimeError(f"JHU counts below expected threshold: UG {len(ug)}, PG {len(pg)}")
    return dedupe(ug), dedupe(pg)


def parse_duke_ug() -> list[dict[str, str]]:
    source_url = "https://undergraduate.bulletins.duke.edu/"
    data = fetch(source_url)
    pattern = re.compile(
        r'\{"type":\d+,"label":\d+,"pageId":\d+,"slug":\d+,"linkType":\d+,"url":\d+\},'
        r'"([^"]+)","[^"]*","([^"]+)","([^"]+)"'
    )
    rows: list[dict[str, str]] = []
    for match in pattern.finditer(data):
        name, _slug, path = match.groups()
        if "/allprograms/" not in path:
            continue
        rows.append(
            row(
                "",
                "duke",
                "Undergraduate",
                name,
                award_from_text(name, "UG"),
                absolute(source_url, path),
                "Official Duke Undergraduate Instruction Bulletin all-programs row",
            )
        )
    rows = dedupe(rows)
    if len(rows) < 140:
        raise RuntimeError(f"Duke UG count below threshold: {len(rows)}")
    return rows


def parse_duke_pg() -> list[dict[str, str]]:
    school_urls = [
        ("Divinity School", "https://divinity.bulletins.duke.edu/programs/"),
        ("Fuqua School of Business", "https://fuqua.bulletins.duke.edu/programs/"),
        ("Graduate School", "https://graduateschool.bulletins.duke.edu/programs/"),
        ("Law School", "https://law.bulletins.duke.edu/programs/"),
        ("School of Medicine", "https://medicine.bulletins.duke.edu/programs/"),
        ("Nicholas School", "https://nicholas.bulletins.duke.edu/programs/"),
        ("School of Nursing", "https://nursing.bulletins.duke.edu/programs/"),
        ("Pratt Professional", "https://prattprofessional.bulletins.duke.edu/programs/"),
        ("Sanford School", "https://sanford.bulletins.duke.edu/programs/"),
    ]
    skip_labels = {"Overview & Policies", "See All Programs"}
    rows: list[dict[str, str]] = []

    def award_from_path(label: str, path: str) -> str:
        award = award_from_text(label, "")
        if award:
            return award
        parts = [part for part in path.split("/") if part]
        family = parts[1] if len(parts) > 1 else ""
        if family.startswith("dr"):
            return "Doctoral"
        if family == "masters":
            return "Master's"
        if "certificate" in family:
            return "Certificate"
        return "Graduate"

    for school, source_url in school_urls:
        page = soup(source_url)
        root = decode_nuxt_payload(page)
        found: list[tuple[str, str]] = []

        def walk(value) -> None:
            if isinstance(value, dict):
                label = value.get("label")
                path = value.get("url") or value.get("path") or value.get("slug")
                if isinstance(label, str) and isinstance(path, str) and "/allprograms/" in path:
                    parts = [part for part in path.split("/") if part]
                    if len(parts) >= 3:
                        found.append((label, path))
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(root)
        for label, path in found:
            name = clean_text(label)
            if not name or name in skip_labels:
                continue
            rows.append(
                row(
                    "",
                    "duke",
                    "Postgraduate",
                    name,
                    award_from_path(name, path),
                    absolute(source_url, path),
                    "Official Duke school bulletin all-programs row",
                    mode=school,
                )
            )
    rows = dedupe(rows)
    if len(rows) < 200:
        raise RuntimeError(f"Duke PG count below threshold: {len(rows)}")
    return rows


def parse_coursedog_programs(prefix: str, source_url: str, note: str, *, forced_level: str | None = None) -> list[dict[str, str]]:
    page = soup(source_url)
    root = decode_nuxt_payload(page)
    settings = root.get("pinia", {}).get("settings", {})
    school = settings.get("school")
    catalog_id = settings.get("activeCatalog")
    filters = settings.get("programsFilters")
    if not school or not catalog_id or not isinstance(filters, dict):
        raise RuntimeError(f"Coursedog settings missing from {source_url}")

    effective = settings.get("effectiveDatesRange") or {}
    params = {
        "catalogId": catalog_id,
        "skip": "0",
        "limit": "50000",
        "sortBy": "name",
        "columns": "code,name,type,level,degreeDesignation,contacts,transcriptDescription,programGroupId,cipCode,campus,catalogDisplayName",
    }
    if effective.get("effectiveStartDate"):
        params["effectiveDatesRange"] = effective["effectiveStartDate"]
    endpoint = f"https://app.coursedog.com/api/v1/cm/{school}/programs/search/%24filters?{urllib.parse.urlencode(params)}"
    origin = urllib.parse.urlunparse(urllib.parse.urlparse(source_url)._replace(path="", params="", query="", fragment=""))
    request = urllib.request.Request(
        endpoint,
        data=json.dumps({"condition": "AND", "filters": [filters]}, separators=(",", ":")).encode("utf-8"),
        headers={
            "User-Agent": UA,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": source_url,
            "Origin": origin,
            "X-Requested-With": "catalog",
        },
    )
    payload = json.loads(read_request(request, timeout=60))
    records = payload.get("data") or []
    expected = int(payload.get("listLength") or 0)
    if expected and len(records) != expected:
        raise RuntimeError(f"{prefix} Coursedog expected {expected} rows, got {len(records)}")

    def display_name(record: dict) -> str:
        return clean_text(record.get("catalogDisplayName") or record.get("transcriptDescription") or record.get("name") or record.get("code") or "")

    def display_award(record: dict) -> str:
        degree = clean_coursedog_text(record.get("degreeDesignation") or "")
        if degree:
            return degree
        text = clean_coursedog_text(record.get("transcriptDescription") or record.get("type") or "")
        paren = re.search(r"\(([^()]{1,60})\)\s*$", text)
        if paren:
            return clean_text(paren.group(1))
        kind = clean_coursedog_text(record.get("type") or "")
        if kind.startswith("Major -"):
            return "Major"
        if kind.startswith("Minor"):
            return "Minor"
        return kind or "Program"

    def display_level(record: dict) -> str:
        if forced_level:
            return forced_level
        degree = clean_coursedog_text(record.get("degreeDesignation") or "")
        source_level = clean_coursedog_text(record.get("level") or "")
        kind = clean_coursedog_text(record.get("type") or "")
        if "Undergraduate" in source_level or "Bachelor" in degree or "(MIN)" in kind:
            return "Undergraduate"
        return "Postgraduate"

    rows: list[dict[str, str]] = []
    for record in records:
        name = display_name(record)
        group_id = clean_text(record.get("programGroupId") or record.get("id") or record.get("_id") or slug(name))
        if not name or not group_id:
            continue
        level = display_level(record)
        rows.append(
            row(
                "",
                prefix,
                level,
                name,
                display_award(record),
                f"{source_url.rstrip('/')}/{urllib.parse.quote(group_id, safe='')}",
                note,
                mode=clean_coursedog_text(record.get("level") or ""),
                status="; ".join(part for part in [clean_coursedog_text(record.get("type") or ""), clean_coursedog_text(record.get("status") or "")] if part),
            )
        )
    rows = dedupe(rows)
    if len(rows) != expected:
        raise RuntimeError(f"{prefix} Coursedog rendered {len(rows)} rows after dedupe; expected {expected}")
    return rows


def parse_stanford() -> list[dict[str, str]]:
    rows = parse_coursedog_programs("stanford", "https://bulletin.stanford.edu/programs", "Official Stanford Bulletin Coursedog programme row")
    if len(rows) < 300:
        raise RuntimeError(f"Stanford count below threshold: {len(rows)}")
    return rows


def parse_berkeley() -> list[dict[str, str]]:
    ug = parse_coursedog_programs("berkeley", "https://undergraduate.catalog.berkeley.edu/programs", "Official UC Berkeley undergraduate Coursedog programme row", forced_level="Undergraduate")
    pg = parse_coursedog_programs("berkeley", "https://graduate.catalog.berkeley.edu/programs", "Official UC Berkeley graduate Coursedog programme row", forced_level="Postgraduate")
    if len(ug) < 200 or len(pg) < 180:
        raise RuntimeError(f"Berkeley counts below threshold: UG {len(ug)}, PG {len(pg)}")
    return [*ug, *pg]


def parse_cornell() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows = link_rows(
        "cornell",
        "Undergraduate",
        "https://courses.cornell.edu/programs/",
        ".az_sitemap li a[href]",
        "Official Cornell Courses of Study A-Z row",
        default_award="Program",
        href_contains="courses.cornell.edu/programs/",
        minimum=300,
    )
    ug: list[dict[str, str]] = []
    pg: list[dict[str, str]] = []
    for item in rows:
        award = award_from_text(item["name"], item["award"])
        level = infer_level(award, item["name"])
        if not level:
            continue
        adjusted = {**item, "level": level, "award": award, "id": f"cornell-{level.lower()[:2]}-{slug(item['name'])}-{slug(award)}"}
        (ug if level == "Undergraduate" else pg).append(adjusted)
    if len(ug) < 150 or len(pg) < 90:
        raise RuntimeError(f"Cornell counts below expected threshold: UG {len(ug)}, PG {len(pg)}")
    return dedupe(ug), dedupe(pg)


def parse_notre_dame_grad() -> list[dict[str, str]]:
    source_url = "https://graduateschool.nd.edu/degree-programs/"
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    for item in page.select("li.grid-item"):
        link = item.select_one("a.card-link[href]")
        label = item.select_one(".card-label")
        if not link:
            continue
        name = clean_text(link.get_text(" ", strip=True))
        award = clean_text(label.get_text(" ", strip=True)) if label else award_from_text(name, "Graduate")
        rows.append(
            row(
                "",
                "notre-dame",
                "Postgraduate",
                name,
                award,
                absolute(source_url, link.get("href") or ""),
                "Official Notre Dame Graduate School degree programme card",
                mode="Graduate School",
            )
        )
    if len(rows) < 80:
        raise RuntimeError(f"Notre Dame graduate count below expected threshold: {len(rows)}")
    return dedupe(rows)


def parse_dartmouth(level: str, source_url: str) -> list[dict[str, str]]:
    page = soup(source_url)
    marker = "departments-programs-undergraduate" if level == "Undergraduate" else "departments-programs-graduate"
    rows: list[dict[str, str]] = []
    for anchor in page.select("main a[href]"):
        text = clean_text(anchor.get_text(" ", strip=True))
        url = absolute(source_url, anchor.get("href") or "")
        path = urllib.parse.urlparse(url).path.rstrip("/")
        if not text or marker not in path or path.endswith(marker):
            continue
        rows.append(row("", "dartmouth", level, text, award_from_text(text, "Department/Program"), url, "Official Dartmouth ORC department/program row"))
    if len(rows) < (50 if level == "Undergraduate" else 25):
        raise RuntimeError(f"Dartmouth {level} count below threshold: {len(rows)}")
    return dedupe(rows)


def parse_rice(level: str, source_url: str) -> list[dict[str, str]]:
    return link_rows(
        "rice",
        level,
        source_url,
        "table a[href]",
        f"Official Rice {level.lower()} degree chart row",
        default_award="Degree chart",
        href_contains="ga.rice.edu/programs-study/",
        minimum=140,
    )


def parse_cmu_ug() -> list[dict[str, str]]:
    source_url = "http://coursecatalog.web.cmu.edu/degreesoffered/"
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    for container in page.select("div.page_content.tab_content"):
        if container.get("id") == "textcontainer":
            continue
        for li in container.select("li"):
            text = clean_text(li.get_text(" ", strip=True))
            if not text:
                continue
            link = li.select_one("a[href]")
            rows.append(
                row(
                    "",
                    "cmu",
                    "Undergraduate",
                    text,
                    award_from_text(text, "UG"),
                    absolute(source_url, link.get("href")) if link and link.get("href") else source_url,
                    "Official CMU undergraduate degrees offered tab row",
                )
            )
    if len(rows) < 80:
        raise RuntimeError(f"CMU UG count below threshold: {len(rows)}")
    return dedupe(rows)


def parse_cmu_pg() -> list[dict[str, str]]:
    source_url = "http://coursecatalog.web.cmu.edu/degreesoffered/graduate-degrees/"
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    for li in page.select("main li"):
        text = clean_text(li.get_text(" ", strip=True))
        if not text or len(text) < 4:
            continue
        if not any(marker in text for marker in ["M.", "Master", "Ph.D", "PhD", "Doctor"]):
            continue
        rows.append(row("", "cmu", "Postgraduate", text, award_from_text(text, "Graduate"), source_url, "Official CMU graduate degrees offered list row"))
    if len(rows) < 120:
        raise RuntimeError(f"CMU PG count below threshold: {len(rows)}")
    return dedupe(rows)


def parse_emory_ug() -> list[dict[str, str]]:
    source_url = "https://catalog.college.emory.edu/academics/concentrations/index.html"
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    for card in page.select(".card-body"):
        title = card.select_one(".card-title")
        name = clean_text(title.get_text(" ", strip=True)) if title else ""
        if not name:
            continue
        for anchor in card.select('a[href^="majors/"], a[href^="minors/"]'):
            award = clean_text(anchor.get_text(" ", strip=True))
            href = anchor.get("href") or ""
            if not award or not href:
                continue
            rows.append(row("", "emory", "Undergraduate", name, award, absolute(source_url, href), "Official Emory College majors and minors row"))
    if len(rows) < 100:
        raise RuntimeError(f"Emory UG count below threshold: {len(rows)}")
    return dedupe(rows)


def parse_emory_pg() -> list[dict[str, str]]:
    source_url = "https://gs.emory.edu/degree-programs/index.html"
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    for dialog in page.select(".modal-dialog.filter-results__modal-dialog"):
        title = dialog.select_one("h2.modal-title")
        award = dialog.select_one(".filter-results__types")
        website = dialog.find("a", string=re.compile("Program Website", re.I))
        if not title:
            continue
        rows.append(
            row(
                "",
                "emory",
                "Postgraduate",
                clean_text(title.get_text(" ", strip=True)),
                clean_text(award.get_text(" ", strip=True)) if award else "Graduate",
                absolute(source_url, website.get("href")) if website and website.get("href") else source_url,
                "Official Emory Laney Graduate School degree program modal",
                mode="Laney Graduate School",
            )
        )
    if len(rows) < 50:
        raise RuntimeError(f"Emory PG count below threshold: {len(rows)}")
    return dedupe(rows)


def parse_ut(level: str, source_url: str) -> list[dict[str, str]]:
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    for tr in page.select("table tr"):
        cells = [clean_text(td.get_text(" ", strip=True)) for td in tr.select("td")]
        if len(cells) < 2 or not cells[0]:
            continue
        rows.append(row("", "ut-austin", level, cells[0], cells[1], source_url, "Official UT Austin degree programs table row"))
    if len(rows) < 150:
        raise RuntimeError(f"UT Austin {level} count below threshold: {len(rows)}")
    return dedupe(rows)


def parse_ucla_pg() -> list[dict[str, str]]:
    source_url = "https://grad.ucla.edu/programs/"
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    for anchor in page.select('main p a[href*="grad.ucla.edu/programs/"]'):
        text = clean_text(anchor.get_text(" ", strip=True))
        url = absolute(source_url, anchor.get("href") or "")
        if not text or text.endswith("Department") or text.endswith("School") or "Department/" in url.rstrip("/").split("/")[-1]:
            continue
        if text in {"Programs A-Z", "Programs Sorted by Schools"}:
            continue
        rows.append(row("", "ucla", "Postgraduate", text, award_from_text(text, "Graduate"), url, "Official UCLA graduate programs A-Z row"))
    if len(rows) < 120:
        raise RuntimeError(f"UCLA PG count below threshold: {len(rows)}")
    return dedupe(rows)


def parse_brown_pg() -> list[dict[str, str]]:
    source_url = "https://graduateprograms.brown.edu/graduate_programs"
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    for item in page.select(".views-row"):
        link = item.select_one("h2 a[href]")
        if not link:
            continue
        degree = item.select_one(".views-field-field-program-degree-type .field-content")
        name = clean_text(link.get_text(" ", strip=True))
        award = clean_text(degree.get_text(" ", strip=True)) if degree else award_from_text(name, "Graduate")
        rows.append(
            row(
                "",
                "brown",
                "Postgraduate",
                name,
                award,
                absolute(source_url, link.get("href") or ""),
                "Official Brown Graduate Program Finder row",
            )
        )
    rows = dedupe(rows)
    if len(rows) < 90:
        raise RuntimeError(f"Brown PG count below threshold: {len(rows)}")
    return rows


def parse_vanderbilt_catalog(source_url: str, level: str, catalogue_label: str, minimum: int) -> list[dict[str, str]]:
    page_url = source_url.split("#", 1)[0]
    data = fetch(page_url)
    subdomain_match = re.search(r"window\.subdomain\s*=\s*[\"']([^\"']+)", data)
    catalog_match = re.search(r"window\.catalogId\s*=\s*[\"']([^\"']+)", data)
    if not subdomain_match or not catalog_match:
        raise RuntimeError(f"Vanderbilt Kuali catalog settings missing from {source_url}")
    endpoint = f"{subdomain_match.group(1).rstrip('/')}/api/v1/catalog/programs/{catalog_match.group(1)}"
    records = fetch_json(endpoint)
    rows: list[dict[str, str]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        title = clean_text(record.get("title") or record.get("name") or "")
        record_id = clean_text(record.get("id") or "")
        if not title or not record_id:
            continue
        title = re.sub(r"\s+-\s+GS$", "", title).strip()
        title = re.sub(r"\((Major|Minor|Certificate)\s*$", r"(\1)", title, flags=re.I)
        award = "Program"
        paren = re.search(r"\(([^()]{1,80})\)\s*$", title)
        if paren:
            award = clean_text(paren.group(1))
            if award.lower() in {"major", "minor", "certificate"}:
                award = award.title()
        elif "Certificate" in title:
            award = "Certificate"
        elif re.search(r"\b(PhD|Ph\.D\.|Doctor|Doctoral)\b", title):
            award = "Doctoral"
        elif re.search(r"\b(MA|MS|MFA|MEd|M\.Ed\.|MBA|Master)\b", title):
            award = "Master's"
        rows.append(
            row(
                "",
                "vanderbilt",
                level,
                title,
                award,
                f"{page_url}#/programs/{urllib.parse.quote(record_id, safe='')}",
                "Official Vanderbilt Kuali catalog API row",
                mode=catalogue_label,
            )
        )
    rows = dedupe(rows)
    if len(rows) < minimum:
        raise RuntimeError(f"Vanderbilt {catalogue_label} count below threshold: {len(rows)}")
    return rows


def parse_vanderbilt() -> list[dict[str, str]]:
    specs = [
        ("https://www.vanderbilt.edu/catalogs/kuali/undergraduate-26-27.php", "Undergraduate", "Undergraduate Catalog 2026-27", 250),
        ("https://www.vanderbilt.edu/catalogs/kuali/divinity-25-26.php", "Postgraduate", "Divinity School Catalog 2025-26", 4),
        ("https://www.vanderbilt.edu/catalogs/kuali/graduate-25-26.php#/home", "Postgraduate", "Graduate School Catalog 2025-26", 120),
        ("https://www.vanderbilt.edu/catalogs/kuali/law-25-26.php", "Postgraduate", "Law School Catalog 2025-26", 3),
        ("https://www.vanderbilt.edu/catalogs/kuali/owen-25-26.php", "Postgraduate", "Owen Graduate School Catalog 2025-26", 20),
        ("https://www.vanderbilt.edu/catalogs/kuali/peabody-25-26.php", "Postgraduate", "Peabody Professional Catalog 2025-26", 30),
        ("https://www.vanderbilt.edu/catalogs/kuali/som-25-26.php#/home", "Postgraduate", "School of Medicine Catalog 2025-26", 15),
        ("https://www.vanderbilt.edu/catalogs/kuali/nursing-25-26.php", "Postgraduate", "School of Nursing Catalog 2025-26", 40),
    ]
    rows: list[dict[str, str]] = []
    for source_url, level, catalogue_label, minimum in specs:
        rows.extend(parse_vanderbilt_catalog(source_url, level, catalogue_label, minimum))
    rows = dedupe(rows)
    if len(rows) < 500:
        raise RuntimeError(f"Vanderbilt count below threshold: {len(rows)}")
    return rows


def parse_caltech() -> list[dict[str, str]]:
    source_url = "https://catalog.caltech.edu/current/areas-of-study-and-research/"
    page = soup(source_url)
    specs = [
        (
            "Undergraduate",
            "/current/information-for-undergraduate-students/graduation-requirements-all-options/",
            "Official Caltech undergraduate option/minor catalog row",
            "Option",
        ),
        (
            "Postgraduate",
            "/current/information-for-graduate-students/special-regulations-for-graduate-options/",
            "Official Caltech graduate option catalog row",
            "Graduate option",
        ),
    ]
    rows: list[dict[str, str]] = []
    skip_prefixes = ("Core Institute", "Typical First-Year", "Other First-Year")

    def caltech_award(text: str, level: str) -> str:
        if level == "Postgraduate":
            return "Graduate option"
        if "Option and Minor" in text:
            return "Option and Minor"
        if "Minor" in text:
            return "Minor"
        if "Option" in text:
            return "Option"
        return "Undergraduate option"

    for level, path_prefix, note, default_award in specs:
        for anchor in page.select(f'a[href^="{path_prefix}"]'):
            text = clean_text(anchor.get_text(" ", strip=True))
            href = anchor.get("href") or ""
            if not text or text.startswith(skip_prefixes) or href.rstrip("/") == path_prefix.rstrip("/"):
                continue
            rows.append(row("", "caltech", level, text, caltech_award(text, level) or default_award, absolute(source_url, href), note))
    rows = dedupe(rows)
    if len([item for item in rows if item["level"] == "Undergraduate"]) < 30 or len([item for item in rows if item["level"] == "Postgraduate"]) < 30:
        raise RuntimeError(f"Caltech counts below threshold: {len(rows)}")
    return rows


def parse_georgetown_pg() -> list[dict[str, str]]:
    source_url = "https://grad.georgetown.edu/programs/"
    endpoint = "https://grad.georgetown.edu/wp-admin/admin-ajax.php"
    base_fields = [
        ("post-id", "1335"),
        ("filter-by-keyword", ""),
        ("filter-by-maximum-program-length[]", ""),
    ]
    skip_link_labels = {
        "Application",
        "Apply Now",
        "Request More Information",
        "Contact Program",
        "Compare Programs",
        "How to Apply",
        "Admissions Requirements",
    }
    rows: list[dict[str, str]] = []
    for offset in range(0, 600, 15):
        fields = [
            *base_fields,
            ("action", "post-filter-fetch-posts"),
            ("postCount", str(offset)),
            ("verb", "found"),
        ]
        request = urllib.request.Request(
            endpoint,
            data=urllib.parse.urlencode(fields).encode("utf-8"),
            headers={
                "User-Agent": UA,
                "Accept": "application/json",
                "Referer": source_url,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        payload = json.loads(read_request(request, timeout=35))
        cards = BeautifulSoup(payload.get("display", ""), "lxml").select(".aos-list-program")
        for card in cards:
            title = card.select_one("h2.aos-list-title, h2")
            if not title:
                continue
            raw_name = clean_text(title.get_text(" ", strip=True))
            if "," in raw_name and any(marker in raw_name.rsplit(",", 1)[1] for marker in ["Master", "Doctor", "Certificate", "LLM", "J.D.", "Ph.D.", "M.D.", "Bachelor"]):
                name, award = [clean_text(part) for part in raw_name.rsplit(",", 1)]
            else:
                name, award = raw_name, "Graduate"
            preferred_link = None
            for anchor in card.select("a[href]"):
                label = clean_text(anchor.get_text(" ", strip=True))
                if not label or label in skip_link_labels or "School" in label:
                    continue
                preferred_link = anchor
                break
            rows.append(
                row(
                    "",
                    "georgetown",
                    "Postgraduate",
                    name,
                    award,
                    absolute(source_url, preferred_link.get("href")) if preferred_link else source_url,
                    "Official Georgetown graduate programme finder AJAX row",
                )
            )
        if payload.get("hideButton") or not cards:
            break
    rows = dedupe(rows)
    if len(rows) < 130:
        raise RuntimeError(f"Georgetown graduate count below threshold: {len(rows)}")
    return rows


def parse_ucsd_ug() -> list[dict[str, str]]:
    source_url = "https://admissions.ucsd.edu/why/majors/index.html"
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    for major_list in page.select("ul.area_of_study_dept_major_list"):
        for anchor in major_list.select("li > a[href]"):
            parent = anchor.find_parent("li")
            if parent and parent.find("ul"):
                continue
            name = clean_text(anchor.get_text(" ", strip=True)).rstrip("*").strip()
            if not name:
                continue
            award = "B.S." if re.search(r"\bB\.S\.$", name) else "B.A." if re.search(r"\bB\.A\.$", name) else "Major"
            rows.append(row("", "ucsd", "Undergraduate", name, award, absolute(source_url, anchor.get("href") or ""), "Official UC San Diego admissions undergraduate majors row"))
    rows = dedupe(rows)
    if len(rows) < 160:
        raise RuntimeError(f"UCSD undergraduate count below threshold: {len(rows)}")
    return rows


def parse_ucsd_pg() -> list[dict[str, str]]:
    source_url = "https://grad.ucsd.edu/admissions/programs.html"
    page = soup(source_url)
    container = None
    for heading in page.select("h2"):
        if clean_text(heading.get_text(" ", strip=True)) == "All Programs":
            container = heading.find_next_sibling("div")
            break
    if container is None:
        raise RuntimeError("UCSD graduate All Programs container not found")
    rows: list[dict[str, str]] = []
    for item in container.select("ul > li"):
        link = item.select_one("a[href]")
        name = clean_text(item.get_text(" ", strip=True))
        if not name or not link:
            continue
        rows.append(
            row(
                "",
                "ucsd",
                "Postgraduate",
                name,
                award_from_text(name, "Graduate"),
                absolute(source_url, link.get("href") or ""),
                "Official UC San Diego graduate admissions all-programs row",
            )
        )
    rows = dedupe(rows)
    if len(rows) < 45:
        raise RuntimeError(f"UCSD graduate count below threshold: {len(rows)}")
    return rows


def parse_uva_ug() -> list[dict[str, str]]:
    source_url = "https://www.virginia.edu/majors-minors/"
    page = soup(source_url)
    program_list = None
    for heading in page.select("section.body-copy h2, h2"):
        if clean_text(heading.get_text(" ", strip=True)) == "Undergraduate Majors and Minors":
            program_list = heading.find_next("ul", class_="majors-list")
            break
    if program_list is None:
        raise RuntimeError("UVA undergraduate majors/minors list not found")
    rows: list[dict[str, str]] = []
    for anchor in program_list.select("li > a[href]"):
        name = clean_text(anchor.get_text(" ", strip=True))
        if not name:
            continue
        rows.append(
            row(
                "",
                "uva",
                "Undergraduate",
                name,
                "Major/Minor",
                absolute(source_url, anchor.get("href") or ""),
                "Official UVA undergraduate majors and minors row",
            )
        )
    rows = dedupe(rows)
    if len(rows) < 100:
        raise RuntimeError(f"UVA undergraduate count below threshold: {len(rows)}")
    return rows


def parse_uf_ug() -> list[dict[str, str]]:
    source_url = "https://catalog.ufl.edu/UGRD/programs/"
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    for item in page.select("li.item"):
        title = item.select_one(".text--title .title")
        kind = item.select_one(".text--title .type")
        link = item.select_one("a.learn-more[href]")
        name = clean_text(title.get_text(" ", strip=True)) if title else ""
        award = clean_text(kind.get_text(" ", strip=True)) if kind else ""
        if not name or not award or not link:
            continue
        award = award.replace("major", "Major").replace("minor", "Minor").replace("certificate", "Certificate")
        description = item.select_one(".description p")
        rows.append(
            row(
                "",
                "uf",
                "Undergraduate",
                name,
                award,
                absolute(source_url, link.get("href") or ""),
                "Official University of Florida undergraduate programs row",
                status=clean_text(description.get_text(" ", strip=True)) if description else "",
            )
        )
    rows = dedupe(rows)
    if len(rows) < 400:
        raise RuntimeError(f"UF undergraduate count below threshold: {len(rows)}")
    return rows


def parse_wustl() -> list[dict[str, str]]:
    source_url = "https://bulletin.wustl.edu/programs/"
    base = "https://bulletin.wustl.edu/"
    ug_directories = [
        "undergrad/architecture/majors/",
        "undergrad/architecture/minors/",
        "undergrad/art/majors/",
        "undergrad/art/minors/",
        "undergrad/artsci/majors/",
        "undergrad/artsci/minors/",
        "undergrad/artsci/additional/",
        "undergrad/business/majors/",
        "undergrad/business/minors/",
        "undergrad/engineering/majors/",
        "undergrad/engineering/minors/",
        "undergrad/caps/programs/",
    ]
    pg_directories = [
        "grad/architecture/degrees/",
        "grad/artsci/degrees/",
        "grad/business/graduate-masters/",
        "grad/business/dual-degrees/",
        "grad/business/doctoral/",
        "grad/engineering/degrees/",
        "medicine/degrees-offerings/",
        "grad/caps/masters/",
        "grad/caps/additional/",
        "grad/caps/online/",
    ]
    pg_direct_pages = [
        ("MDes for Human-Computer Interaction + Emerging Technology", "MDes", "grad/art/mdes-design/"),
        ("MFA in Illustration & Visual Culture", "MFA", "grad/art/mfa-illustration-visual-culture/"),
        ("MFA in Visual Art", "MFA", "grad/art/mfa-visual-art/"),
        ("Juris Doctor (JD)", "JD", "law/juris-doctor/"),
        ("Master of Laws (LLM)", "LLM", "law/master-of-law/"),
        ("Master of Legal Studies (MLS)", "MLS", "law/master-of-legal-studies/"),
        ("Juris Scientiae Doctoris (JSD)", "JSD", "law/juris-scientiae-doctoris/"),
        ("Master of Public Health", "MPH", "publichealth/mph/"),
        ("PhD in Public Health Sciences", "PhD", "publichealth/phd-public-health-sciences/"),
        ("Master of Social Work", "MSW", "brownschool/msw/"),
        ("Master of Social Policy", "MSP", "brownschool/msp/"),
        ("PhD in Social Work", "PhD", "brownschool/phd-social-work/"),
        ("Division of Biology & Biomedical Sciences", "PhD", "grad/cross-school-phd-programs/dbbs/"),
        ("Division of Computational & Data Sciences", "PhD", "grad/cross-school-phd-programs/dcds/"),
        ("Institute of Materials Science & Engineering", "PhD", "grad/cross-school-phd-programs/imse/"),
    ]
    rows: list[dict[str, str]] = []

    def add_directory(level: str, path: str) -> None:
        directory_url = absolute(base, path)
        directory_page = soup(directory_url)
        for anchor in directory_page.select("#textcontainer a[href], .page_content a[href]"):
            text = clean_text(anchor.get_text(" ", strip=True))
            href = anchor.get("href") or ""
            if not text or href.startswith("#") or len(text) == 1 or text in {"Bulletin", "Undergraduate", "Graduate & Professional"}:
                continue
            url = absolute(directory_url, href)
            target_path = urllib.parse.urlparse(url).path
            directory_path = f"/{path.rstrip('/')}"
            if target_path.startswith(f"{directory_path}/") or target_path.rstrip("/") == directory_path:
                rows.append(row("", "wustl", level, text, award_from_text(text, "Program"), url, "Official WashU Bulletin whitelisted programme row"))

    for directory in ug_directories:
        add_directory("Undergraduate", directory)
    for directory in pg_directories:
        add_directory("Postgraduate", directory)
    for name, award, path in pg_direct_pages:
        rows.append(row("", "wustl", "Postgraduate", name, award, absolute(base, path), "Official WashU Bulletin whitelisted programme row"))

    rows = dedupe(rows)
    if len(rows) < 500:
        raise RuntimeError(f"WashU count below threshold: {len(rows)}")
    return rows


def parse_ntu_ug() -> list[dict[str, str]]:
    source_url = "https://www.ntu.edu.sg/admissions/undergraduate-programmes"
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for anchor in page.select('div.card-rows__item > a.img-card.img-card--horizontal[href*="/education/undergraduate-programme/"]'):
        url = absolute(source_url, anchor.get("href") or "")
        normalized_url = url.split("#", 1)[0].rstrip("/")
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)
        title = anchor.select_one(".img-card__title")
        subtitle = anchor.select_one(".img-card__subtitle")
        desc = anchor.select_one(".img-card__desc")
        name = clean_text(title.get_text(" ", strip=True)) if title else clean_text(anchor.get_text(" ", strip=True))
        if not name:
            continue
        rows.append(
            row(
                "",
                "ntu",
                "Undergraduate",
                name,
                clean_text(subtitle.get_text(" ", strip=True)) if subtitle else "UG",
                url,
                "Official NTU undergraduate programme card",
                status=clean_text(desc.get_text(" ", strip=True)) if desc else "",
            )
        )
    if len(rows) < 200:
        raise RuntimeError(f"NTU UG count below threshold: {len(rows)}")
    return dedupe(rows)


def parse_ntu_pg() -> list[dict[str, str]]:
    source_url = "https://www.ntu.edu.sg/graduate-college/admissions/programme/graduate-programmes"
    page = soup(source_url)
    rows: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for anchor in page.select('div.card-rows__item > a.img-card.img-card--horizontal[href*="/education/graduate-programme/"]'):
        url = absolute(source_url, anchor.get("href") or "")
        normalized_url = url.split("#", 1)[0].rstrip("/")
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)
        title = anchor.select_one(".img-card__title")
        subtitle = anchor.select_one(".img-card__subtitle")
        desc = anchor.select_one(".img-card__desc")
        name = clean_text(title.get_text(" ", strip=True)) if title else clean_text(anchor.get_text(" ", strip=True))
        if not name:
            continue
        rows.append(
            row(
                "",
                "ntu",
                "Postgraduate",
                name,
                award_from_text(name, clean_text(subtitle.get_text(" ", strip=True)) if subtitle else "Graduate"),
                url,
                "Official NTU graduate programme card",
                mode=clean_text(subtitle.get_text(" ", strip=True)) if subtitle else "",
                status=clean_text(desc.get_text(" ", strip=True)) if desc else "",
            )
        )
    if len(rows) < 150:
        raise RuntimeError(f"NTU PG count below threshold: {len(rows)}")
    return dedupe(rows)


def parse_nus_pg() -> list[dict[str, str]]:
    endpoint = "https://study.nus.edu.sg/lwr/apex/v67.0/ShopFrontController/searchProgrammes"
    source_url = "https://study.nus.edu.sg/programme"
    params = {
        "programmeType": "",
        "interestArea": "",
        "keyword": "",
        "modeOfStudy": "",
        "facultyIds": "",
        "intakePeriod": "",
    }
    query = urllib.parse.urlencode({"methodParams": json.dumps(params, separators=(",", ":"))})
    request = urllib.request.Request(
        f"{endpoint}?{query}",
        headers={
            "User-Agent": UA,
            "Accept": "application/json",
            "Referer": source_url,
            "x-sfdc-page-scope-id": "default",
        },
    )
    payload = json.loads(read_request(request, timeout=35))
    rows: list[dict[str, str]] = []
    for wrapper in payload:
        programme = wrapper.get("programme") or {}
        name = clean_text(programme.get("Title__c") or programme.get("Name") or "")
        if not name:
            continue
        faculties = wrapper.get("faculties") or []
        faculty_names = "; ".join(clean_text(f.get("Name") or "") for f in faculties if f.get("Name"))
        rows.append(
            row(
                "",
                "nus",
                "Postgraduate",
                name,
                clean_text(programme.get("Type__c") or "Graduate"),
                absolute(source_url, programme.get("Program_Page_Link__c") or source_url),
                "Official NUS Study programme LWR Apex row",
                mode=clean_text(programme.get("Mode_of_Study__c") or ""),
                status="; ".join(
                    part
                    for part in [
                        f"Faculty: {faculty_names}" if faculty_names else "",
                        f"Intake: {clean_text(programme.get('Intake_Period__c') or '')}" if programme.get("Intake_Period__c") else "",
                    ]
                    if part
                ),
            )
        )
    rows = dedupe(rows)
    if len(rows) != 244:
        raise RuntimeError(f"NUS PG expected 244 rows, got {len(rows)}")
    return rows


def simple_sources() -> dict[str, list[dict[str, str]]]:
    mit_ug, mit_pg = parse_mit()
    cornell_ug, cornell_pg = parse_cornell()
    jhu_ug, jhu_pg = parse_jhu()
    return {
        "harvard": [*parse_harvard("Undergraduate"), *parse_harvard("Postgraduate")],
        "mit": [*mit_ug, *mit_pg],
        "stanford": parse_stanford(),
        "yale": [
            *link_rows("yale", "Undergraduate", "https://catalog.yale.edu/ycps/majors-in-yale-college/", "#content a[href]", "Official Yale College majors row", default_award="Major", href_contains="catalog.yale.edu/ycps/subjects-of-instruction/", minimum=75),
            *link_rows("yale", "Postgraduate", "https://catalog.yale.edu/gsas/degree-granting-departments-programs/", "#content a[href]", "Official Yale GSAS degree-granting departments/programs row", default_award="Graduate", href_contains="catalog.yale.edu/gsas/degree-granting-departments-programs/", minimum=60),
        ],
        "uchicago": link_rows("uchicago", "Undergraduate", "http://collegecatalog.uchicago.edu/thecollege/programsofstudy/", "#content a[href]", "Official UChicago College programme of study row", default_award="Major", href_contains="collegecatalog.uchicago.edu/thecollege/", minimum=60),
        "jhu": [*jhu_ug, *jhu_pg],
        "duke": [*parse_duke_ug(), *parse_duke_pg()],
        "penn": [
            *link_rows("penn", "Undergraduate", "https://catalog.upenn.edu/undergraduate/programs/", ".az_sitemap li a[href]", "Official Penn undergraduate programs A-Z row", default_award="UG", href_contains="catalog.upenn.edu/undergraduate/programs/", minimum=300),
            *link_rows("penn", "Postgraduate", "https://catalog.upenn.edu/graduate/programs/", ".az_sitemap li a[href]", "Official Penn graduate programs A-Z row", default_award="Graduate", href_contains="catalog.upenn.edu/graduate/programs/", minimum=300),
        ],
        "caltech": parse_caltech(),
        "northwestern": [
            *link_rows("northwestern", "Undergraduate", "https://catalogs.northwestern.edu/undergraduate/programs-az/", ".az_sitemap li a[href]", "Official Northwestern undergraduate programs A-Z row", default_award="UG", href_contains="catalogs.northwestern.edu/undergraduate/", minimum=180),
            *link_rows("northwestern", "Postgraduate", "https://www.northwestern.edu/academics/graduate-a-to-z.html", "table a[href]", "Official Northwestern graduate degree programs table row", default_award="Graduate", minimum=180),
        ],
        "brown": [
            *link_rows("brown", "Undergraduate", "https://bulletin.brown.edu/the-college/concentrations/", "#content a[href]", "Official Brown undergraduate concentrations row", default_award="Concentration", href_contains="bulletin.brown.edu/the-college/concentrations/", minimum=80),
            *parse_brown_pg(),
        ],
        "vanderbilt": parse_vanderbilt(),
        "cornell": [*cornell_ug, *cornell_pg],
        "rice": [
            *parse_rice("Undergraduate", "https://ga.rice.edu/undergraduate-students/academic-opportunities/degree-chart/"),
            *parse_rice("Postgraduate", "https://ga.rice.edu/graduate-students/academic-opportunities/degree-chart/"),
        ],
        "wustl": parse_wustl(),
        "dartmouth": [
            *parse_dartmouth("Undergraduate", "https://dartmouth.smartcatalogiq.com/en/current/orc/departments-programs-undergraduate"),
            *parse_dartmouth("Postgraduate", "https://dartmouth.smartcatalogiq.com/en/current/orc/departments-programs-graduate"),
        ],
        "columbia": link_rows("columbia", "Undergraduate", "https://bulletin.columbia.edu/columbia-college/departments-instruction/", "#content a[href]", "Official Columbia College departments/programs row", default_award="Department/Program", href_contains="bulletin.columbia.edu/columbia-college/departments-instruction/", minimum=50),
        "notre-dame": [
            *link_rows("notre-dame", "Undergraduate", "https://catalog.nd.edu/programs/", "table a[href]", "Official Notre Dame academic programs table row", default_award="UG", href_contains="catalog.nd.edu/undergraduate/", minimum=150),
            *parse_notre_dame_grad(),
        ],
        "berkeley": parse_berkeley(),
        "cmu": [*parse_cmu_ug(), *parse_cmu_pg()],
        "emory": [*parse_emory_ug(), *parse_emory_pg()],
        "georgetown": parse_georgetown_pg(),
        "ucla": parse_ucla_pg(),
        "ucsd": [*parse_ucsd_ug(), *parse_ucsd_pg()],
        "unc": link_rows("unc", "Undergraduate", "https://catalog.unc.edu/undergraduate/programs-study/", ".az_sitemap li a[href]", "Official UNC undergraduate programs of study row", default_award="UG", href_contains="catalog.unc.edu/undergraduate/programs-study/", minimum=180),
        "uva": parse_uva_ug(),
        "uf": [
            *parse_uf_ug(),
            *link_rows("uf", "Postgraduate", "https://gradcatalog.ufl.edu/graduate/programs-college/", "#content a[href]", "Official University of Florida graduate majors by college row", default_award="Graduate", href_contains="gradcatalog.ufl.edu/graduate/colleges-departments/", minimum=150),
        ],
        "ut-austin": [
            *parse_ut("Undergraduate", "https://catalog.utexas.edu/undergraduate/the-university/degree-programs/"),
            *parse_ut("Postgraduate", "https://catalog.utexas.edu/graduate/graduate-study/degree-programs/"),
        ],
    }


def write_us(programs: dict[str, list[dict[str, str]]]) -> None:
    for institution, rows in sorted(programs.items()):
        write_programmes(ROOT, institution, rows, CHECKED, refresh_index=False)


def write_singapore() -> int:
    nus_pg_rows = parse_nus_pg()
    ntu_rows = [*parse_ntu_ug(), *parse_ntu_pg()]
    write_programmes(ROOT, "nus", nus_pg_rows, CHECKED, refresh_index=False)
    write_programmes(ROOT, "ntu", ntu_rows, CHECKED, refresh_index=False)
    return len(nus_pg_rows) + len(ntu_rows)


def main() -> int:
    programs = simple_sources()
    write_us(programs)
    total_singapore = write_singapore()
    rebuild_index(ROOT)
    total_us = sum(len(rows) for rows in programs.values())
    print(f"Wrote {CATALOGUE_DIR.relative_to(ROOT)} with {total_us} US rows across {len(programs)} institutions")
    print(f"Wrote {CATALOGUE_DIR.relative_to(ROOT)} with {total_singapore} Singapore rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
