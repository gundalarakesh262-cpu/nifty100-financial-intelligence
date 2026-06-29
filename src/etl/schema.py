

from sqlalchemy import create_engine, Column, String, Integer, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    sector = Column(String(50))
    market_cap = Column(Float)

class ProfitLoss(Base):
    __tablename__ = "profitandloss"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), nullable=False)
    year = Column(String(7), nullable=False)  # YYYY-MM format
    revenue = Column(Float)
    cost_of_goods_sold = Column(Float)
    gross_profit = Column(Float)
    operating_expense = Column(Float)
    operating_profit = Column(Float)
    net_profit = Column(Float)

class BalanceSheet(Base):
    __tablename__ = "balancesheet"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), nullable=False)
    year = Column(String(7), nullable=False)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    shareholder_equity = Column(Float)
    cash = Column(Float)
    current_assets = Column(Float)
    current_liabilities = Column(Float)

class CashFlow(Base):
    __tablename__ = "cashflow"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), nullable=False)
    year = Column(String(7), nullable=False)
    operating_cash_flow = Column(Float)
    investing_cash_flow = Column(Float)
    financing_cash_flow = Column(Float)
    free_cash_flow = Column(Float)


class FinancialRatio(Base):
    __tablename__ = "financial_ratios"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), nullable=False)
    year = Column(String(7), nullable=False)
    roe = Column(Float)  # Return on Equity
    roa = Column(Float)  # Return on Assets
    npm = Column(Float)  # Net Profit Margin
    opm = Column(Float)  # Operating Profit Margin
    de_ratio = Column(Float)  # Debt to Equity
    pe_ratio = Column(Float)  # Price to Earnings
    pb_ratio = Column(Float)  # Price to Book
    current_ratio = Column(Float)
    quick_ratio = Column(Float)
    asset_turnover = Column(Float)


class StockPrice(Base):
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), nullable=False)
    date = Column(Date)
    close_price = Column(Float)
    market_cap = Column(Float)


class Sector(Base):
    __tablename__ = "sectors"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True)
    sector = Column(String(50))
    subsector = Column(String(50))


class PeerGroup(Base):
    __tablename__ = "peer_groups"
    
    id = Column(Integer, primary_key=True)
    group_name = Column(String(50))  # e.g., "Private Banks"
    ticker = Column(String(20))


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20))
    year = Column(String(7))
    document_type = Column(String(50))  # Annual Report, etc.
    description = Column(String(500))

class Analysis(Base):
    __tablename__ = "analysis"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20))
    year = Column(String(7))
    analysis_text = Column(String(1000))
    quality_score = Column(Float)

def create_database():
    """Create all tables in database"""
    engine = create_engine('sqlite:///nifty100.db', echo=False)
    Base.metadata.create_all(engine)
    print("Database created successfully!")
    print(" All 10 tables created!")
    return engine

if __name__ == "__main__":
    create_database()