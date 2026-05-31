#!/usr/bin/env python3
"""Create a minimal admissions setup template."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_template(task_type: str, output_format: str) -> dict:
    return {
        'task_type': task_type,
        'output_format': output_format,
        'degree_level': '',
        'subject_area': '',
        'target_country_or_region': '',
        'academic_background': '',
        'language_scores': {},
        'budget': '',
        'intake_term': '',
        'source_policy': 'official_sources_required',
        'constraints': [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--task-type', default='shortlist')
    parser.add_argument('--output-format', default='chat_summary')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    data = build_template(args.task_type, args.output_format)
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
