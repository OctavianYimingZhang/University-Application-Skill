#!/usr/bin/env python3
"""Validate admissions setup JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_BY_TASK = {
    'shortlist': ['degree_level', 'subject_area', 'target_country_or_region', 'academic_background', 'intake_term'],
    'requirement_check': ['program_name_or_url', 'applicant_qualification', 'source_policy'],
    'visa_readiness': ['citizenship', 'destination_country', 'intended_intake', 'funding_plan'],
    'essay_plan': ['program_name', 'prompt', 'word_limit', 'applicant_background'],
}


def fail(message: str) -> None:
    print(f'ERROR: {message}', file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('setup_json', type=Path)
    args = parser.parse_args()
    data = json.loads(args.setup_json.read_text(encoding='utf-8'))
    task_type = data.get('task_type')
    if not task_type:
        fail('missing task_type')
    if not data.get('output_format'):
        fail('missing output_format')
    missing = [key for key in REQUIRED_BY_TASK.get(task_type, []) if not data.get(key)]
    if missing:
        fail('missing required fields for task: ' + ', '.join(missing))
    print('OK: setup validation passed')


if __name__ == '__main__':
    main()
