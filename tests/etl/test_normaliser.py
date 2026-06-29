import sys
import os
import pytest


current_dir = os.path.abspath(os.path.dirname(__file__))
while current_dir and current_dir != os.path.dirname(current_dir):
    if os.path.exists(os.path.join(current_dir, 'src')):
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        break
    current_dir = os.path.dirname(current_dir)


from src.etl.normaliser import normalize_year, normalize_ticker

class TestNormalizeYear:
    """Test year normalization"""
    
    def test_mar_format(self):
        assert normalize_year("Mar-23") == "2023-03"
    
    def test_fy_format(self):
        assert normalize_year("FY24") == "2024-03"
    
    def test_dec_format(self):
        assert normalize_year("Dec-22") == "2022-12"
    
    def test_plain_year(self):
        assert normalize_year("2023") == "2023-03"
    
    def test_already_normalized(self):
        assert normalize_year("2023-03") == "2023-03"
    
    def test_with_spaces(self):
        assert normalize_year("  Mar-23  ") == "2023-03"
    
    def test_jun_format(self):
        assert normalize_year("Jun-23") == "2023-06"
    
    def test_sep_format(self):
        assert normalize_year("Sep-23") == "2023-09"

class TestNormalizeTicker:
    """Test ticker normalization"""
    
    def test_lowercase(self):
        assert normalize_ticker("tcs") == "TCS"
    
    def test_with_spaces(self):
        assert normalize_ticker("  INFY  ") == "INFY"
    
    def test_special_chars(self):
        assert normalize_ticker("m&m") == "M&M"
    
    def test_hyphen(self):
        assert normalize_ticker("bajaj-auto") == "BAJAJ-AUTO"
    
    def test_mixed_case(self):
        assert normalize_ticker("HdFc") == "HDFC"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])