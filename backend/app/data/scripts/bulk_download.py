"""
Bulk Data Downloader
Download financial data for multiple companies at once
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List
import pandas as pd
from datetime import datetime

BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import DATA_OUTPUT_DIR
from app.data.pipeline.sec_data_fetcher import SECDataFetcher
from app.data.pipeline.financial_data_parser import FinancialDataParser


def download_company_data(
    ticker: str, 
    fetcher: SECDataFetcher, 
    parser: FinancialDataParser,
    num_years: int = 10
) -> dict:
    """
    Download and process data for a single company
    
    Args:
        ticker: Stock ticker symbol
        fetcher: SECDataFetcher instance
        parser: FinancialDataParser instance
        num_years: Number of years to include
        
    Returns:
        Dictionary with company data
    """
    print(f"\n📥 Downloading {ticker}...")
    
    try:
        facts = fetcher.get_company_data_by_ticker(ticker)
        
        if not facts:
            print(f"   ❌ Failed to fetch {ticker}")
            return None
        
        company_name = facts.get('entityName', ticker)
        cik = facts.get('cik', 'Unknown')
        
        print(f"   ✅ {company_name} (CIK: {cik})")
        
        # Parse financial data
        summary = parser.create_financial_summary(facts, num_periods=num_years)
        
        if 'annual' not in summary or summary['annual'].empty:
            print(f"   ⚠️  No annual data available for {ticker}")
            return None
        
        # Enhance with calculations
        annual = parser.calculate_derived_metrics(summary['annual'])
        annual = parser.calculate_growth_rates(annual)
        
        print(f"   ✅ Processed {len(annual)} years of data")
        
        return {
            'ticker': ticker,
            'company_name': company_name,
            'cik': cik,
            'annual_data': annual,
            'quarterly_data': summary.get('quarterly')
        }
        
    except Exception as e:
        print(f"   ❌ Error processing {ticker}: {e}")
        return None


def bulk_download(tickers: List[str], num_years: int = 10, export_format: str = 'csv'):
    """
    Download data for multiple companies
    
    Args:
        tickers: List of ticker symbols
        num_years: Number of years to download
        export_format: Export format ('csv', 'json', or 'both')
    """
    print("\n" + "="*80)
    print(f"📦 BULK DATA DOWNLOAD - {len(tickers)} companies")
    print("="*80)
    
    # Initialize
    fetcher = SECDataFetcher(cache_hours=24)
    parser = FinancialDataParser()
    
    # Create output directory
    output_dir = DATA_OUTPUT_DIR / "bulk_download"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Download data
    results = []
    successful = 0
    failed = 0
    
    for ticker in tickers:
        data = download_company_data(ticker, fetcher, parser, num_years)
        
        if data:
            results.append(data)
            successful += 1
            
            # Export individual company files
            if export_format in ['csv', 'both']:
                csv_file = output_dir / f"{ticker}_annual.csv"
                data['annual_data'].to_csv(csv_file, index=False)
                print(f"   💾 Saved: {csv_file}")
            
            if export_format in ['json', 'both']:
                json_file = output_dir / f"{ticker}_data.json"
                with open(json_file, 'w') as f:
                    json.dump({
                        'ticker': data['ticker'],
                        'company_name': data['company_name'],
                        'cik': data['cik'],
                        'annual_data': data['annual_data'].to_dict('records')
                    }, f, indent=2, default=str)
        else:
            failed += 1
    
    # Create summary file
    if results:
        print("\n" + "─"*80)
        print("📊 Creating summary...")
        
        # Compile latest data from all companies
        summary_rows = []
        
        for data in results:
            annual = data['annual_data']

            summary_rows.append({
                'Ticker': data['ticker'],
                'Company': data['company_name'],
                'CIK': data['cik'],
                'Latest Year': annual.iloc[0].get('fy', 'N/A'),
                'Revenue': parser.get_latest_non_null(annual, 'Revenue'),
                'Net Income': parser.get_latest_non_null(annual, 'NetIncome'),
                'Total Assets': parser.get_latest_non_null(annual, 'Assets'),
                'Equity': parser.get_latest_non_null(annual, 'Equity'),
                'Profit Margin %': parser.get_latest_non_null(annual, 'ProfitMargin'),
                'ROE %': parser.get_latest_non_null(annual, 'ROE'),
                'Revenue Growth %': parser.get_latest_non_null(annual, 'Revenue_YoY_%'),
            })
        
        summary_df = pd.DataFrame(summary_rows)
        
        # Save summary
        summary_file = output_dir / f"summary_{timestamp}.csv"
        summary_df.to_csv(summary_file, index=False)
        
        print(f"\n✅ Summary saved: {summary_file}")
        
        # Display summary
        print("\n" + "─"*80)
        print("📈 DOWNLOAD SUMMARY")
        print("─"*80)
        print(summary_df.to_string(index=False))
    
    # Final statistics
    print("\n" + "="*80)
    print("📊 DOWNLOAD STATISTICS")
    print("="*80)
    print(f"Total companies: {len(tickers)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Output directory: {output_dir}")
    
    # Cache stats
    cache_stats = fetcher.get_cache_stats()
    print(f"\n💾 Cache statistics:")
    print(f"   Cached items: {cache_stats['size']}")
    print(f"   Cache volume: {cache_stats['volume']:,} bytes")


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='Bulk download financial data from SEC EDGAR'
    )
    
    parser.add_argument(
        'tickers',
        nargs='+',
        help='Stock ticker symbols (e.g., AAPL MSFT GOOGL)'
    )
    
    parser.add_argument(
        '-y', '--years',
        type=int,
        default=10,
        help='Number of years to download (default: 10)'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['csv', 'json', 'both'],
        default='csv',
        help='Export format (default: csv)'
    )
    
    args = parser.parse_args()
    
    # Convert tickers to uppercase
    tickers = [t.upper() for t in args.tickers]
    
    # Run bulk download
    bulk_download(tickers, num_years=args.years, export_format=args.format)


if __name__ == "__main__":
    main()
