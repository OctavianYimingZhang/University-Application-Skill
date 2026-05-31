#!/usr/bin/env python3
"""Render a simple admissions workbook from structured case JSON."""
from __future__ import annotations

import argparse
import html
import json
import zipfile
from pathlib import Path
from typing import Any


def rows_from(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [row if isinstance(row, dict) else {'value': row} for row in value]
    if isinstance(value, dict):
        return [value]
    return [{'value': value}]


def sheet_xml(rows: list[list[Any]]) -> str:
    body = []
    for r_index, row in enumerate(rows, start=1):
        cells = []
        for c_index, value in enumerate(row, start=1):
            col = ''
            n = c_index
            while n:
                n, rem = divmod(n - 1, 26)
                col = chr(65 + rem) + col
            text = html.escape('' if value is None else str(value))
            cells.append(f'<c r="{col}{r_index}" t="inlineStr"><is><t>{text}</t></is></c>')
        body.append(f'<row r="{r_index}">{"".join(cells)}</row>')
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + \
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + \
        ''.join(body) + '</sheetData></worksheet>'


def table_rows(items: list[dict[str, Any]]) -> list[list[Any]]:
    keys: list[str] = []
    for item in items:
        for key in item:
            if key not in keys:
                keys.append(key)
    if not keys:
        return [['No data']]
    rows = [keys]
    for item in items:
        rows.append([item.get(key, '') for key in keys])
    return rows


def build_sheets(data: dict[str, Any]) -> dict[str, list[list[Any]]]:
    applicant = data.get('applicant', {})
    summary = [
        ['Field', 'Value'],
        ['case_title', data.get('case_title', '')],
        ['target_country_or_region', data.get('target_country_or_region', '')],
        ['degree_level', data.get('degree_level', '')],
        ['subject_area', data.get('subject_area', '')],
        ['intake_term', data.get('intake_term', '')],
    ]
    return {
        'Summary': summary,
        'Applicant': table_rows(rows_from(applicant)),
        'Programs': table_rows(rows_from(data.get('programs'))),
        'Requirements': table_rows(rows_from(data.get('requirements'))),
        'Documents': table_rows(rows_from(data.get('documents'))),
        'Deadlines': table_rows(rows_from(data.get('deadlines'))),
        'Risks_Gaps': table_rows(rows_from(data.get('risks_and_gaps'))),
        'Tasks': table_rows(rows_from(data.get('tasks'))),
        'Source_Log': table_rows(rows_from(data.get('sources'))),
    }


def write_xlsx(sheets: dict[str, list[list[Any]]], output: Path) -> None:
    names = list(sheets)
    workbook_sheets = ''.join(
        f'<sheet name="{html.escape(name)}" sheetId="{idx}" r:id="rId{idx}"/>'
        for idx, name in enumerate(names, start=1)
    )
    workbook = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + \
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ' + \
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + \
        workbook_sheets + '</sheets></workbook>'
    rels = ''.join(
        f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>'
        for idx in range(1, len(names) + 1)
    )
    workbook_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + \
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + rels + '</Relationships>'
    content_types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + \
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' + \
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' + \
        '<Default Extension="xml" ContentType="application/xml"/>' + \
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' + \
        ''.join(f'<Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for idx in range(1, len(names) + 1)) + \
        '</Types>'
    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + \
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + \
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>' + \
        '</Relationships>'
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', root_rels)
        zf.writestr('xl/workbook.xml', workbook)
        zf.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
        for idx, name in enumerate(names, start=1):
            zf.writestr(f'xl/worksheets/sheet{idx}.xml', sheet_xml(sheets[name]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('case_json', type=Path)
    parser.add_argument('output_xlsx', type=Path)
    args = parser.parse_args()
    data = json.loads(args.case_json.read_text(encoding='utf-8'))
    write_xlsx(build_sheets(data), args.output_xlsx)
    print(f'OK: wrote {args.output_xlsx}')


if __name__ == '__main__':
    main()
