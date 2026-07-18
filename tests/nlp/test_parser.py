import os
import sys

import pandas as pd


current_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.nlp import parser


WORKBOOK_PATH = os.path.join(project_root, 'data', 'raw', 'analysis.xlsx')
PROCESSED_DIR = os.path.join(project_root, 'data', 'processed')


def test_parse_metric_text_handles_expected_patterns():
    assert parser.parse_metric_text('10 Years: 21%') == (10, 21.0)
    assert parser.parse_metric_text('1 Year: -2%') == (1, -2.0)


def test_parse_metric_text_rejects_non_numeric_periods():
    assert parser.parse_metric_text('TTM: 43%') is None
    assert parser.parse_metric_text('Last Year: 12%') is None


def test_main_writes_expected_outputs(tmp_path):
    parsed_df, failures_df, validation_df = parser.main(
        workbook_path=WORKBOOK_PATH,
        output_dir=tmp_path,
        processed_dir=PROCESSED_DIR,
    )

    assert not parsed_df.empty
    assert set(parsed_df.columns) == {'company_id', 'metric_type', 'period_years', 'value_pct'}
    assert not failures_df.empty
    assert 'PATTERN_MISMATCH' in set(failures_df['failure_reason'])
    assert not validation_df.empty
    assert {'company_id', 'metric_type', 'validation_status', 'review_required'}.issubset(validation_df.columns)

    for filename in ('analysis_parsed.csv', 'parse_failures.csv', 'analysis_validation.csv'):
        assert (tmp_path / filename).exists()
