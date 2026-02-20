"""
Test Script - Verify SEC Data Fetcher Setup
Quick test to ensure everything is working
"""
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    try:
        import requests
        import pandas as pd
        import diskcache
        from dotenv import load_dotenv
        print("   ✅ Core dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("\n   Run: pip install -r backend/requirements.txt")
        return False


def test_config():
    """Test configuration"""
    print("\n🧪 Testing configuration...")
    try:
        from app import config
        
        # Check User-Agent
        email = config.USER_AGENT_EMAIL
        if "example.com" in email or "@" not in email:
            print(f"   ⚠️  Warning: Default email detected: {email}")
            print("   Please update USER_AGENT_EMAIL in .env file")
            return False
        
        print(f"   ✅ User-Agent configured: {config.SEC_HEADERS['User-Agent']}")
        
        # Check directories
        print(f"   ✅ Cache directory: {config.CACHE_DIR}")
        print(f"   ✅ Output directory: {config.DATA_OUTPUT_DIR}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Config error: {e}")
        return False


def test_sec_fetch():
    """Test SEC data fetching"""
    print("\n🧪 Testing SEC data fetch...")
    try:
        from app.data.pipeline.sec_data_fetcher import SECDataFetcher
        
        fetcher = SECDataFetcher()
        
        # Test ticker lookup
        print("   📥 Testing ticker lookup...")
        cik = fetcher.get_cik_from_ticker("AAPL")
        
        if cik:
            print(f"   ✅ Found AAPL CIK: {cik}")
        else:
            print("   ❌ Failed to find AAPL ticker")
            return False
        
        # Test company facts fetch
        print("   📥 Testing company facts fetch...")
        facts = fetcher.get_company_facts(cik)
        
        if facts and 'entityName' in facts:
            print(f"   ✅ Retrieved data for: {facts['entityName']}")
            
            # Check for financial data
            if 'facts' in facts and 'us-gaap' in facts['facts']:
                num_metrics = len(facts['facts']['us-gaap'])
                print(f"   ✅ Found {num_metrics} financial metrics")
            else:
                print("   ⚠️  No us-gaap metrics found")
                return False
        else:
            print("   ❌ Failed to retrieve company facts")
            return False
        
        # Check cache
        cache_stats = fetcher.get_cache_stats()
        print(f"   ✅ Cache working: {cache_stats['size']} items cached")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Fetch error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parser():
    """Test financial data parser"""
    print("\n🧪 Testing financial data parser...")
    try:
        import pandas as pd
        from app.data.pipeline.sec_data_fetcher import SECDataFetcher
        from app.data.pipeline.financial_data_parser import FinancialDataParser
        
        fetcher = SECDataFetcher()
        parser = FinancialDataParser()
        
        # Get Apple data
        facts = fetcher.get_company_data_by_ticker("AAPL")
        
        if not facts:
            print("   ❌ No data to parse")
            return False
        
        # Test summary creation
        print("   🔧 Creating financial summary...")
        summary = parser.create_financial_summary(facts, num_periods=3)
        
        if 'annual' in summary and not summary['annual'].empty:
            annual = summary['annual']
            print(f"   ✅ Parsed {len(annual)} annual periods")

            # Test metric extraction (allow fallback metrics if revenue missing)
            latest_revenue = parser.get_latest_non_null(annual, "Revenue")
            latest_net_income = parser.get_latest_non_null(annual, "NetIncome")
            latest_assets = parser.get_latest_non_null(annual, "Assets")

            if latest_revenue is not None:
                print(f"   ✅ Latest revenue: ${latest_revenue:,.0f}")
            elif latest_net_income is not None:
                print("   ⚠️  Revenue missing; using NetIncome as availability check")
                print(f"   ✅ Latest net income: ${latest_net_income:,.0f}")
            elif latest_assets is not None:
                print("   ⚠️  Revenue missing; using Assets as availability check")
                print(f"   ✅ Latest assets: ${latest_assets:,.0f}")
            else:
                print("   ❌ No core financial metrics found in parsed data")
                return False

            # Test derived metrics
            enhanced = parser.calculate_derived_metrics(annual)
            margin = parser.get_latest_non_null(enhanced, "ProfitMargin")
            if margin is not None:
                print(f"   ✅ Calculated profit margin: {margin:.2f}%")

            # Test growth calculation
            with_growth = parser.calculate_growth_rates(annual)
            growth = parser.get_latest_non_null(with_growth, "Revenue_YoY_%")
            if growth is not None:
                print(f"   ✅ Calculated YoY growth: {growth:.2f}%")
        else:
            print("   ❌ Failed to create annual summary")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Parser error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export():
    """Test CSV export"""
    print("\n🧪 Testing CSV export...")
    try:
        from app import config
        from app.data.pipeline.sec_data_fetcher import SECDataFetcher
        from app.data.pipeline.financial_data_parser import FinancialDataParser
        
        fetcher = SECDataFetcher()
        parser = FinancialDataParser()
        
        facts = fetcher.get_company_data_by_ticker("AAPL")
        summary = parser.create_financial_summary(facts, num_periods=3)
        
        if 'annual' in summary:
            test_file = Path(config.DATA_OUTPUT_DIR) / "test_export.csv"
            summary['annual'].to_csv(test_file, index=False)
            
            if test_file.exists():
                size = test_file.stat().st_size
                print(f"   ✅ Exported to: {test_file} ({size} bytes)")
                
                # Clean up test file
                test_file.unlink()
                print(f"   ✅ Test file cleaned up")
                return True
            else:
                print("   ❌ Export file not created")
                return False
        else:
            print("   ❌ No data to export")
            return False
            
    except Exception as e:
        print(f"   ❌ Export error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 FIN-VAULT-AI - SETUP VERIFICATION TEST")
    print("="*80)
    
    results = []
    
    # Run tests
    results.append(("Import Dependencies", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("SEC Data Fetch", test_sec_fetch()))
    results.append(("Financial Parser", test_parser()))
    results.append(("CSV Export", test_export()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10s} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("\n" + "─"*80)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("  1. Run: python3 backend/app/data/scripts/bulk_download.py AAPL MSFT")
        print("  2. Check backend/app/data/output for exported files")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Configure .env file with your email")
        print("  3. Check your internet connection")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
