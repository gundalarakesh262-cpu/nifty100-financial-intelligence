# 📈 Nifty 100 Financial Intelligence Platform

An end-to-end financial intelligence and analytics platform for the Nifty 100 index. The project automates financial data processing, ratio analysis, peer benchmarking, stock screening, valuation, and interactive visualization using Streamlit.

---

# Features

## Dashboard Modules

- 🏠 Home Dashboard
- 🏢 Company Profile
- 🔍 Stock Screener
- 👥 Peer Comparison
- 📊 Sector Analysis
- 📈 Trend Analysis
- 💰 Valuation Dashboard
- 🏦 Capital Allocation
- 📑 Reports & CSV Export

---

# Analytics Features

- Financial Ratio Analysis
- Revenue & Profit CAGR
- Free Cash Flow Analysis
- Debt Analysis
- Peer Group Benchmarking
- Composite Quality Score
- Sector-wise Ranking
- Valuation Classification
- Screener Presets
- Capital Allocation Pattern Detection

---

# Tech Stack

- Python 3.11
- Streamlit
- Pandas
- Plotly
- SQLite
- OpenPyXL

---

# Project Structure

```
nifty100-financial-intelligence/

├── config/
├── data/
├── output/
│   ├── screener_full_ranked_universe.csv
│   ├── screener_output.xlsx
│   ├── valuation_summary.xlsx
│   ├── valuation_flags.csv
│   └── capital_allocation.csv
│
├── scripts/
├── src/
│   ├── analytics/
│   └── dashboard/
│
├── tests/
├── requirements.txt
└── README.md
```

---

# Installation

Clone the repository

```bash
git clone <repository-url>
```

Move into the project

```bash
cd nifty100-financial-intelligence
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Dashboard

Launch Streamlit

```bash
streamlit run src/dashboard/app.py
```

The dashboard will be available at

```
http://localhost:8501
```

---

# Dashboard Screens

## Home

Displays

- Company Summary
- KPI Cards
- Preset Overview
- Quick Screener

---

## Company Profile

Displays

- Company Information
- Financial KPIs
- Revenue & Profit Trends
- Balance Sheet
- Cash Flow
- Financial Ratios

---

## Screener

Supports filtering using

- ROE
- Debt/Equity
- Revenue Growth
- Profit Growth
- Composite Score
- Peer Score

Includes CSV export.

---

## Peer Comparison

Provides

- Peer Group Selection
- KPI Comparison
- Company Benchmarking

---

## Sector Analysis

Displays

- Sector KPIs
- Sector Distribution
- Company Rankings
- Peer Distribution

---

## Trend Analysis

Displays

- Historical Financial Trends
- Sector Trends
- Multi-year Performance
- Top Performing Companies

---

## Valuation Dashboard

Provides

- Composite Score
- EPS
- Book Value
- Free Cash Flow
- PE Classification
- Valuation Classification

Exports

- valuation_summary.xlsx
- valuation_flags.csv

---

## Capital Allocation

Displays

- Operating Cash Flow
- Investing Cash Flow
- Financing Cash Flow
- Capital Allocation Pattern

---

## Reports

Supports

- Preset Reports
- CSV Downloads
- Screener Summary
- Company Reports

---

# Outputs Generated

The project generates

- screener_output.xlsx
- screener_full_ranked_universe.csv
- valuation_summary.xlsx
- valuation_flags.csv
- capital_allocation.csv

---

# Libraries Used

- pandas
- numpy
- streamlit
- plotly
- sqlite3
- openpyxl

---

# Future Enhancements

- Live NSE/BSE Data Integration
- Portfolio Tracking
- Watchlists
- AI-based Stock Recommendation
- Automated Report Generation
- Price Prediction Models

---

# Author

Developed as part of the **Nifty 100 Financial Intelligence Platform** project using Python, Streamlit, SQLite, and financial analytics techniques.