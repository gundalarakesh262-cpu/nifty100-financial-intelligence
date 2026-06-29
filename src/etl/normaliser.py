import re

def normalize_year(year):
    """
    Examples:
        "Mar-23" -> "2023-03"
        "FY24" -> "2024-03"
        "2023" -> "2023-03"
        "Dec-22" -> "2022-12"
    """
    try:
        year_str = str(year).strip().upper()
        
        # Month-Year format: Mar-23, Apr-23
        match = re.match(r'([A-Z]{3})-(\d{2})', year_str)
        if match:
            month_str, yr = match.groups()
            months = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            month = months.get(month_str, '03')
            full_year = int(f"20{yr}")
            return f"{full_year}-{month}"
            
        # Fiscal Year format: FY24, FY23
        match = re.match(r'FY(\d{2})', year_str)
        if match:
            yr = int(match.group(1))
            full_year = 2000 + yr
            return f"{full_year}-03"
            
        # Plain year: 2023, 2024
        if year_str.isdigit() and len(year_str) == 4:
            return f"{year_str}-03"
            
        if re.match(r'^\d{4}-\d{2}$', year_str):
            return year_str
            
        raise ValueError(f"Cannot parse year: {year}")
        
    except Exception as e:
        print(f"Error normalizing year '{year}': {e}")
        return None


def normalize_ticker(ticker):
    """
    Normalize ticker to uppercase and clean
    
    Examples:
        "tcs" -> "TCS"
        " INFY " -> "INFY"
        "m&m" -> "M&M"
    """
    try:
        normalized = str(ticker).strip().upper()
        return normalized
    except Exception as e:
        print(f"Error normalizing ticker '{ticker}': {e}")
        return None


if __name__ == "__main__":
   
    print("Testing normalize_year():")
    test_years = ["Mar-23", "FY24", "2023", "Dec-22", "Apr-23"]
    for year in test_years:
        result = normalize_year(year)
        print(f"  {year} -> {result}")

    print("\nTesting normalize_ticker():")
    test_tickers = ["INFY", "m&m", "bajaj-auto"]
    for ticker in test_tickers:
        result = normalize_ticker(ticker)
        print(f"  {ticker} -> '{result}'")