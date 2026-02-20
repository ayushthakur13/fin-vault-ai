"""
Fundamental Data Fetcher (yfinance version)
Provides pre-computed financial ratios, KPIs, and company fundamentals

Data Source: yfinance (Yahoo Finance)
- FREE, no API key required
- Includes 100+ financial metrics and ratios
- Financial statements (Income, Balance, Cash Flow)
- Analyst estimates and recommendations
- Company profile and statistics
"""
import yfinance as yf
import pandas as pd
from pathlib import Path
import json
from typing import Dict, List
from datetime import datetime


from app.config import DATA_OUTPUT_DIR


class FundamentalDataFetcher:
    """Fetch fundamental financial data using yfinance (Yahoo Finance)"""
    
    def __init__(self, data_dir: str | None = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_OUTPUT_DIR / "fundamental_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.statements_dir = self.data_dir / "statements"
        self.ratios_dir = self.data_dir / "ratios"
        self.info_dir = self.data_dir / "info"
        self.analysis_dir = self.data_dir / "analysis"
        
        for dir in [self.statements_dir, self.ratios_dir, self.info_dir, self.analysis_dir]:
            dir.mkdir(exist_ok=True)
    
    def get_company_info(self, ticker: str) -> Dict:
        """
        Get comprehensive company information and statistics
        
        Returns dict with 100+ fields including:
        - Valuation: P/E, PEG, P/B, P/S, EV/EBITDA
        - Profitability: ROE, ROA, Profit Margins
        - Financial Health: Current Ratio, Debt/Equity
        - Growth: Revenue/Earnings growth rates
        - Analyst data: Target prices, recommendations
        """
        print(f"🏢 Fetching company info for {ticker}...")
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or len(info) == 0:
            print(f"❌ No data found for {ticker}")
            return {}
        
        # Save to JSON
        json_path = self.info_dir / f"{ticker}_info.json"
        with open(json_path, 'w') as f:
            json.dump(info, f, indent=2, default=str)
        
        print(f"💾 Saved: {json_path}")
        
        return info
    
    def get_income_statement(self, ticker: str, quarterly: bool = False) -> pd.DataFrame:
        """Get income statement (annual or quarterly)"""
        period = "quarterly" if quarterly else "annual"
        print(f"📊 Fetching {period} income statement for {ticker}...")
        
        stock = yf.Ticker(ticker)
        df = stock.quarterly_financials if quarterly else stock.financials
        
        if df is None or df.empty:
            print(f"❌ No income statement data for {ticker}")
            return pd.DataFrame()
        
        # Transpose so dates are rows
        df = df.T
        
        # Save to CSV
        csv_path = self.statements_dir / f"{ticker}_income_{period}.csv"
        df.to_csv(csv_path)
        print(f"💾 Saved: {csv_path}")
        
        return df
    
    def get_balance_sheet(self, ticker: str, quarterly: bool = False) -> pd.DataFrame:
        """Get balance sheet (annual or quarterly)"""
        period = "quarterly" if quarterly else "annual"
        print(f"📊 Fetching {period} balance sheet for {ticker}...")
        
        stock = yf.Ticker(ticker)
        df = stock.quarterly_balance_sheet if quarterly else stock.balance_sheet
        
        if df is None or df.empty:
            print(f"❌ No balance sheet data for {ticker}")
            return pd.DataFrame()
        
        df = df.T
        
        csv_path = self.statements_dir / f"{ticker}_balance_{period}.csv"
        df.to_csv(csv_path)
        print(f"💾 Saved: {csv_path}")
        
        return df
    
    def get_cash_flow(self, ticker: str, quarterly: bool = False) -> pd.DataFrame:
        """Get cash flow statement (annual or quarterly)"""
        period = "quarterly" if quarterly else "annual"
        print(f"📊 Fetching {period} cash flow for {ticker}...")
        
        stock = yf.Ticker(ticker)
        df = stock.quarterly_cashflow if quarterly else stock.cashflow
        
        if df is None or df.empty:
            print(f"❌ No cash flow data for {ticker}")
            return pd.DataFrame()
        
        df = df.T
        
        csv_path = self.statements_dir / f"{ticker}_cashflow_{period}.csv"
        df.to_csv(csv_path)
        print(f"💾 Saved: {csv_path}")
        
        return df
    
    def create_kpi_summary(self, ticker: str) -> Dict:
        """
        Create comprehensive KPI summary with all key metrics
        Perfect for agent's "Quick Mode"
        """
        print(f"\n{'='*80}")
        print(f"📊 KPI SUMMARY: {ticker}")
        print(f"{'='*80}\n")
        
        info = self.get_company_info(ticker)
        
        if not info:
            print("❌ Insufficient data for KPI summary")
            return {}
        
        # Extract key metrics
        summary = {
            'ticker': ticker,
            'company_name': info.get('longName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'date_updated': str(datetime.now().date()),
            
            # Market Data
            'current_price': f"${info.get('currentPrice', info.get('regularMarketPrice', 0)):.2f}",
            'market_cap': f"${info.get('marketCap', 0) / 1e9:.2f}B",
            'enterprise_value': f"${info.get('enterpriseValue', 0) / 1e9:.2f}B" if info.get('enterpriseValue') else "N/A",
            
            # Valuation Ratios
            'pe_ratio': f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A",
            'forward_pe': f"{info.get('forwardPE', 0):.2f}" if info.get('forwardPE') else "N/A",
            'peg_ratio': f"{info.get('pegRatio', 0):.2f}" if info.get('pegRatio') else "N/A",
            'pb_ratio': f"{info.get('priceToBook', 0):.2f}" if info.get('priceToBook') else "N/A",
            'ps_ratio': f"{info.get('priceToSalesTrailing12Months', 0):.2f}" if info.get('priceToSalesTrailing12Months') else "N/A",
            'ev_to_ebitda': f"{info.get('enterpriseToEbitda', 0):.2f}" if info.get('enterpriseToEbitda') else "N/A",
            'ev_to_revenue': f"{info.get('enterpriseToRevenue', 0):.2f}" if info.get('enterpriseToRevenue') else "N/A",
            
            # Profitability Metrics
            'profit_margin': f"{info.get('profitMargins', 0) * 100:.2f}%" if info.get('profitMargins') else "N/A",
            'operating_margin': f"{info.get('operatingMargins', 0) * 100:.2f}%" if info.get('operatingMargins') else "N/A",
            'gross_margin': f"{info.get('grossMargins', 0) * 100:.2f}%" if info.get('grossMargins') else "N/A",
            'roe': f"{info.get('returnOnEquity', 0) * 100:.2f}%" if info.get('returnOnEquity') else "N/A",
            'roa': f"{info.get('returnOnAssets', 0) * 100:.2f}%" if info.get('returnOnAssets') else "N/A",
            
            # Financial Health
            'current_ratio': f"{info.get('currentRatio', 0):.2f}" if info.get('currentRatio') else "N/A",
            'quick_ratio': f"{info.get('quickRatio', 0):.2f}" if info.get('quickRatio') else "N/A",
            'debt_to_equity': f"{info.get('debtToEquity', 0) / 100:.2f}" if info.get('debtToEquity') else "N/A",
            'total_debt': f"${info.get('totalDebt', 0) / 1e9:.2f}B" if info.get('totalDebt') else "N/A",
            'total_cash': f"${info.get('totalCash', 0) / 1e9:.2f}B" if info.get('totalCash') else "N/A",
            
            # Growth Metrics
            'revenue_growth': f"{info.get('revenueGrowth', 0) * 100:.2f}%" if info.get('revenueGrowth') else "N/A",
            'earnings_growth': f"{info.get('earningsGrowth', 0) * 100:.2f}%" if info.get('earningsGrowth') else "N/A",
            
            # Per Share Metrics
            'eps_trailing': f"${info.get('trailingEps', 0):.2f}" if info.get('trailingEps') else "N/A",
            'eps_forward': f"${info.get('forwardEps', 0):.2f}" if info.get('forwardEps') else "N/A",
            'book_value_per_share': f"${info.get('bookValue', 0):.2f}" if info.get('bookValue') else "N/A",
            'free_cash_flow_per_share': f"${info.get('freeCashflow', 0) / info.get('sharesOutstanding', 1):.2f}" if info.get('freeCashflow') and info.get('sharesOutstanding') else "N/A",
            
            # Dividend Info
            'dividend_yield': f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "N/A",
            'payout_ratio': f"{info.get('payoutRatio', 0) * 100:.2f}%" if info.get('payoutRatio') else "N/A",
            
            # Analyst Data
            'target_price': f"${info.get('targetMeanPrice', 0):.2f}" if info.get('targetMeanPrice') else "N/A",
            'recommendation': info.get('recommendationKey', 'N/A'),
            'num_analysts': info.get('numberOfAnalystOpinions', 0),
        }
        
        # Print formatted summary
        print("🏢 COMPANY INFO:")
        print(f"   • Name: {summary['company_name']}")
        print(f"   • Sector: {summary['sector']}")
        print(f"   • Industry: {summary['industry']}")
        
        print("\n💰 MARKET DATA:")
        print(f"   • Current Price: {summary['current_price']}")
        print(f"   • Market Cap: {summary['market_cap']}")
        print(f"   • Enterprise Value: {summary['enterprise_value']}")
        
        print("\n📊 VALUATION RATIOS:")
        print(f"   • P/E Ratio (Trailing): {summary['pe_ratio']}")
        print(f"   • P/E Ratio (Forward): {summary['forward_pe']}")
        print(f"   • PEG Ratio: {summary['peg_ratio']}")
        print(f"   • P/B Ratio: {summary['pb_ratio']}")
        print(f"   • P/S Ratio: {summary['ps_ratio']}")
        print(f"   • EV/EBITDA: {summary['ev_to_ebitda']}")
        
        print("\n📈 PROFITABILITY:")
        print(f"   • ROE: {summary['roe']}")
        print(f"   • ROA: {summary['roa']}")
        print(f"   • Profit Margin: {summary['profit_margin']}")
        print(f"   • Operating Margin: {summary['operating_margin']}")
        print(f"   • Gross Margin: {summary['gross_margin']}")
        
        print("\n💵 FINANCIAL HEALTH:")
        print(f"   • Current Ratio: {summary['current_ratio']}")
        print(f"   • Quick Ratio: {summary['quick_ratio']}")
        print(f"   • Debt/Equity: {summary['debt_to_equity']}")
        print(f"   • Total Debt: {summary['total_debt']}")
        print(f"   • Total Cash: {summary['total_cash']}")
        
        print("\n🚀 GROWTH:")
        print(f"   • Revenue Growth: {summary['revenue_growth']}")
        print(f"   • Earnings Growth: {summary['earnings_growth']}")
        
        print("\n💸 PER SHARE:")
        print(f"   • EPS (Trailing): {summary['eps_trailing']}")
        print(f"   • EPS (Forward): {summary['eps_forward']}")
        print(f"   • Book Value: {summary['book_value_per_share']}")
        print(f"   • FCF Per Share: {summary['free_cash_flow_per_share']}")
        
        if summary['dividend_yield'] != "N/A" and summary['dividend_yield'] != "0.00%":
            print("\n💰 DIVIDEND:")
            print(f"   • Dividend Yield: {summary['dividend_yield']}")
            print(f"   • Payout Ratio: {summary['payout_ratio']}")
        
        print("\n🎯 ANALYST DATA:")
        print(f"   • Target Price: {summary['target_price']}")
        print(f"   • Recommendation: {summary['recommendation'].upper()}")
        print(f"   • Number of Analysts: {summary['num_analysts']}")
        
        # Save summary
        json_path = self.analysis_dir / f"{ticker}_kpi_summary.json"
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n💾 Saved: {json_path}")
        
        return summary
    
    def compare_companies(self, tickers: List[str]) -> pd.DataFrame:
        """
        Compare key metrics across multiple companies
        Perfect for peer benchmarking
        """
        print(f"\n{'='*80}")
        print(f"📊 PEER COMPARISON: {', '.join(tickers)}")
        print(f"{'='*80}\n")
        
        comparison_data = []
        
        for ticker in tickers:
            print(f"Fetching data for {ticker}...")
            
            info = self.get_company_info(ticker)
            
            if not info:
                continue
            
            row = {
                'Ticker': ticker,
                'Company': info.get('shortName', ticker),
                'Market Cap ($B)': round(info.get('marketCap', 0) / 1e9, 2) if info.get('marketCap') else None,
                'P/E': round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else None,
                'P/B': round(info.get('priceToBook', 0), 2) if info.get('priceToBook') else None,
                'ROE (%)': round(info.get('returnOnEquity', 0) * 100, 2) if info.get('returnOnEquity') else None,
                'ROA (%)': round(info.get('returnOnAssets', 0) * 100, 2) if info.get('returnOnAssets') else None,
                'Profit Margin (%)': round(info.get('profitMargins', 0) * 100, 2) if info.get('profitMargins') else None,
                'Debt/Equity': round(info.get('debtToEquity', 0) / 100, 2) if info.get('debtToEquity') else None,
                'Current Ratio': round(info.get('currentRatio', 0), 2) if info.get('currentRatio') else None,
                'Revenue Growth (%)': round(info.get('revenueGrowth', 0) * 100, 2) if info.get('revenueGrowth') else None,
                'Earnings Growth (%)': round(info.get('earningsGrowth', 0) * 100, 2) if info.get('earningsGrowth') else None,
                'Dividend Yield (%)': round(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else None,
                'Recommendation': info.get('recommendationKey', 'N/A'),
            }
            
            comparison_data.append(row)
        
        df = pd.DataFrame(comparison_data)
        
        if df.empty:
            print("❌ No data to compare")
            return df
        
        # Save comparison
        csv_path = self.analysis_dir / f"comparison_{'_'.join(tickers)}.csv"
        df.to_csv(csv_path, index=False)
        
        print(f"\n📊 Comparison Table:")
        print(df.to_string(index=False))
        print(f"\n💾 Saved: {csv_path}")
        
        return df
    
    def get_complete_fundamental_data(self, ticker: str) -> Dict:
        """
        Get all fundamental data for a company
        One-stop function for complete analysis
        """
        print("\n" + "="*80)
        print(f"🎯 FETCHING COMPLETE FUNDAMENTAL DATA: {ticker}")
        print("="*80)
        
        result = {}
        
        # 1. Company Info & KPIs
        print("\n📋 Company Info & Key Metrics")
        result['kpi_summary'] = self.create_kpi_summary(ticker)
        
        # 2. Financial Statements
        print("\n📊 Financial Statements")
        result['income_statement'] = self.get_income_statement(ticker)
        result['balance_sheet'] = self.get_balance_sheet(ticker)
        result['cash_flow'] = self.get_cash_flow(ticker)
        
        print("\n" + "="*80)
        print("✅ COMPLETE FUNDAMENTAL DATA FETCHED")
        print("="*80)
        
        return result
