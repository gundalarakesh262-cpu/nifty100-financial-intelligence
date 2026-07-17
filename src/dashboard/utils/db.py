import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


# =====================================================
# Companies
# =====================================================

@st.cache_data(ttl=600)
def get_companies():

    conn = get_connection()

    df = pd.read_sql(
        """
        SELECT *
        FROM companies
        ORDER BY company_name
        """,
        conn
    )

    conn.close()

    return df


@st.cache_data(ttl=600)
def get_company_list():

    conn = get_connection()

    df = pd.read_sql(
        """
        SELECT
            id,
            company_name
        FROM companies
        ORDER BY company_name
        """,
        conn
    )

    conn.close()

    return df


# =====================================================
# Financial Ratios
# =====================================================

@st.cache_data(ttl=600)
def get_ratios(company_id, year=None):

    conn = get_connection()

    if year is None:

        df = pd.read_sql(
            """
            SELECT *
            FROM financial_ratios
            WHERE company_id=?
            ORDER BY year DESC
            """,
            conn,
            params=(company_id,)
        )

    else:

        df = pd.read_sql(
            """
            SELECT *
            FROM financial_ratios
            WHERE company_id=?
            AND year=?
            ORDER BY year DESC
            """,
            conn,
            params=(company_id, year)
        )

    conn.close()

    return df


# =====================================================
# Profit & Loss
# =====================================================

@st.cache_data(ttl=600)
def get_pl(company_id):

    conn = get_connection()

    df = pd.read_sql(
        """
        SELECT *
        FROM profitandloss
        WHERE company_id=?
        ORDER BY year DESC
        """,
        conn,
        params=(company_id,)
    )

    conn.close()

    return df


# =====================================================
# Balance Sheet
# =====================================================

@st.cache_data(ttl=600)
def get_bs(company_id):

    conn = get_connection()

    df = pd.read_sql(
        """
        SELECT *
        FROM balancesheet
        WHERE company_id=?
        ORDER BY year DESC
        """,
        conn,
        params=(company_id,)
    )

    conn.close()

    return df


# =====================================================
# Cash Flow
# =====================================================

@st.cache_data(ttl=600)
def get_cf(company_id):

    conn = get_connection()

    df = pd.read_sql(
        """
        SELECT *
        FROM cashflow
        WHERE company_id=?
        ORDER BY year DESC
        """,
        conn,
        params=(company_id,)
    )

    conn.close()

    return df


# =====================================================
# Sectors
# =====================================================

@st.cache_data(ttl=600)
def get_sectors():

    conn = get_connection()

    df = pd.read_sql(
        """
        SELECT *
        FROM sectors
        ORDER BY broad_sector
        """,
        conn
    )

    conn.close()

    return df


# =====================================================
# Peer Groups
# =====================================================

@st.cache_data(ttl=600)
def get_peers(group_name):

    conn = get_connection()

    df = pd.read_sql(
        """
        SELECT *
        FROM peer_groups
        WHERE peer_group_name=?
        """,
        conn,
        params=(group_name,)
    )

    conn.close()

    return df


# =====================================================
# Valuation
# =====================================================

@st.cache_data(ttl=600)
def get_valuation(company_id):

    conn = get_connection()

    df = pd.read_sql(
        """
        SELECT *
        FROM financial_ratios
        WHERE company_id=?
        ORDER BY year DESC
        LIMIT 1
        """,
        conn,
        params=(company_id,)
    )

    conn.close()

    return df


# =====================================================
# Database Summary
# =====================================================

@st.cache_data(ttl=600)
def get_database_summary():

    conn = get_connection()

    summary = {

        "companies": pd.read_sql(
            """
            SELECT COUNT(*)
            FROM companies
            """,
            conn
        ).iloc[0, 0],

        "sectors": pd.read_sql(
            """
            SELECT COUNT(DISTINCT broad_sector)
            FROM sectors
            """,
            conn
        ).iloc[0, 0],

        "peer_groups": pd.read_sql(
            """
            SELECT COUNT(DISTINCT peer_group_name)
            FROM peer_groups
            """,
            conn
        ).iloc[0, 0],

        "financial_records": pd.read_sql(
            """
            SELECT COUNT(*)
            FROM financial_ratios
            """,
            conn
        ).iloc[0, 0]

    }

    conn.close()

    return summary