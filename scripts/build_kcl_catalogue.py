#!/usr/bin/env python3
"""Build King's College London catalogue rows from the official Contensis API."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "src" / "data" / "kclPrograms.ts"
CHECKED = dt.date.today().isoformat()
UG_URL = "https://www.kcl.ac.uk/study/undergraduate/courses"
PGT_URL = "https://www.kcl.ac.uk/study/postgraduate-taught/courses"
PGR_URL = "https://www.kcl.ac.uk/study/postgraduate-research/areas"
API_URL = "https://api-kcl.cloud.contensis.com/api/delivery/projects/website/entries/search?linkDepth=1"


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 University-Application-Skill/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Request failed (TLS verification remains enabled) for {url}: {exc}") from exc


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def ts_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def extract_startup_url(page_html: str, page_url: str) -> str:
    match = re.search(r'<script\s+src="([^"]*startup-[^"]+\.js)"', page_html)
    if not match:
        raise RuntimeError(f"Could not find KCL startup asset on {page_url}")
    return urllib.parse.urljoin(page_url, match.group(1))


def extract_access_token(startup_js: str) -> str:
    match = re.search(r'accessToken:\s*"([^"]+)"', startup_js)
    if not match:
        match = re.search(r'ACCESS_TOKEN\s*=\s*"([^"]+)"', startup_js)
    if not match:
        raise RuntimeError("Could not find public Contensis access token in KCL startup asset")
    return match.group(1)


def post_json(payload: dict[str, Any], access_token: str) -> dict[str, Any]:
    request = urllib.request.Request(
        API_URL,
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
        with urllib.request.urlopen(request, timeout=40) as response:
            return json.loads(response.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Request failed (TLS verification remains enabled) for {API_URL}: {exc}") from exc


def title_of(value: Any) -> str:
    if isinstance(value, dict):
        return clean_text(str(value.get("title") or value.get("entryTitle") or ""))
    return clean_text(str(value or ""))


def titles_of(value: Any) -> list[str]:
    if isinstance(value, list):
        return [title_of(item) for item in value if title_of(item)]
    title = title_of(value)
    return [title] if title else []


def field_grade(value: Any) -> str:
    if isinstance(value, dict):
        return clean_text(str(value.get("grade") or value.get("level") or ""))
    return ""


def award_from_item(item: dict[str, Any]) -> str:
    awards = titles_of(item.get("qualification"))
    if awards:
        return "/".join(awards)
    title = clean_text(str(item.get("entryTitle") or item.get("title") or ""))
    match = re.search(r"\b(BA|BSc|MSci|MEng|iBSc|LLB|MBBS|MSc|MA|MRes|MPhil|PhD|MD\(Res\)|PG Dip|PG Cert)\b", title)
    return match.group(1) if match else "See official programme page"


def mode_from_item(item: dict[str, Any], fallback: str) -> str:
    modes = titles_of(item.get("studyMode"))
    if modes:
        return "; ".join(modes)
    modes = titles_of(item.get("deliveryMode"))
    if modes:
        return "; ".join(modes)
    return fallback


def status_from_item(item: dict[str, Any]) -> str:
    parts: list[str] = []
    if item.get("applicationStatus"):
        parts.append(f"Application status: {clean_text(str(item['applicationStatus']))}")
    if item.get("ucasCode"):
        parts.append(f"UCAS: {clean_text(str(item['ucasCode']))}")
    grade = field_grade(item.get("entryRequirement"))
    if grade:
        parts.append(f"Entry requirement: {grade}")
    language = title_of(item.get("languageRequirementBand"))
    if language:
        parts.append(f"English band: {language}")
    return "; ".join(parts)


def query_catalogue(content_type_ids: list[str], access_token: str, page_size: int = 100) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page_index = 0
    while True:
        where_content = (
            {"field": "sys.contentTypeId", "equalTo": content_type_ids[0]}
            if len(content_type_ids) == 1
            else {"field": "sys.contentTypeId", "in": content_type_ids}
        )
        payload: dict[str, Any] = {
            "where": [
                where_content,
                {"field": "sys.uri", "exists": True},
                {"field": "sys.versionStatus", "equalTo": "published"},
            ],
            "fields": [
                "entryTitle",
                "title",
                "qualification",
                "duration",
                "studyMode",
                "deliveryMode",
                "applicationStatus",
                "ucasCode",
                "entryRequirement",
                "languageRequirementBand",
                "sys.id",
                "sys.uri",
                "sys.contentTypeId",
            ],
            "pageSize": page_size,
            "pageIndex": page_index,
            "orderBy": [{"asc": "entryTitle"}],
        }
        result = post_json(payload, access_token)
        rows.extend(result.get("items", []))
        if page_index >= int(result.get("pageCount", 1)) - 1:
            break
        page_index += 1
    return rows


def row_from_item(item: dict[str, Any], level: str, prefix: str, note: str, fallback_mode: str) -> dict[str, str] | None:
    sys = item.get("sys")
    if not isinstance(sys, dict) or not sys.get("uri"):
        return None
    url = urllib.parse.urljoin("https://www.kcl.ac.uk", str(sys["uri"]))
    title = clean_text(str(item.get("title") or item.get("entryTitle") or ""))
    if not title:
        return None
    item_id = f"{prefix}{slugify(str(sys['uri']))}"
    duration = clean_text(str(item.get("duration") or "")) or "See official programme page"
    return {
        "id": item_id,
        "name": title,
        "level": level,
        "award": award_from_item(item),
        "url": url,
        "note": note,
        "duration": duration,
        "mode": mode_from_item(item, fallback_mode),
        "status": status_from_item(item),
    }


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
    token = extract_access_token(fetch(extract_startup_url(fetch(UG_URL), UG_URL)))
    ug_items = query_catalogue(["undergraduateCourse"], token)
    pgt_items = query_catalogue(["postgraduateCourse"], token)
    pgr_items = query_catalogue(["postgraduateResearchDegree"], token)

    ug_rows = dedupe(
        [
            row
            for item in ug_items
            if (row := row_from_item(item, "Undergraduate", "kcl-ug-", "Official KCL undergraduate API row", "Undergraduate"))
        ]
    )
    pgt_rows = dedupe(
        [
            row
            for item in pgt_items
            if (row := row_from_item(item, "Postgraduate", "kcl-pgt-", "Official KCL postgraduate taught API row", "Taught"))
        ]
    )
    pgr_rows = dedupe(
        [
            row
            for item in pgr_items
            if (row := row_from_item(item, "Postgraduate", "kcl-pgr-", "Official KCL postgraduate research API row", "Research"))
        ]
    )

    if len(ug_rows) != 152:
        raise RuntimeError(f"Expected 152 KCL UG rows, got {len(ug_rows)}")
    if len(pgt_rows) != 237:
        raise RuntimeError(f"Expected 237 KCL PGT rows, got {len(pgt_rows)}")
    if len(pgr_rows) != 88:
        raise RuntimeError(f"Expected 88 KCL PGR rows, got {len(pgr_rows)}")

    output = "\n".join(
        [
            'import type { CatalogueProgramOption } from "../types";',
            "",
            f"export const kclCatalogueChecked = {ts_string(CHECKED)};",
            f"export const kclUndergraduateCount = {len(ug_rows)};",
            f"export const kclTaughtCount = {len(pgt_rows)};",
            f"export const kclResearchCount = {len(pgr_rows)};",
            "",
            render_rows("kclUndergraduatePrograms", ug_rows),
            "",
            render_rows("kclTaughtPrograms", pgt_rows),
            "",
            render_rows("kclResearchPrograms", pgr_rows),
            "",
            "export const kclPrograms: CatalogueProgramOption[] = [",
            "  ...kclUndergraduatePrograms,",
            "  ...kclTaughtPrograms,",
            "  ...kclResearchPrograms,",
            "];",
            "",
        ]
    )
    OUT.write_text(output, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(ug_rows)} UG rows, {len(pgt_rows)} taught rows, {len(pgr_rows)} research rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
