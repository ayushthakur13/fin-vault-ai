"""
Market Data Fetcher
Provides price data, earnings surprises, and post-earnings reactions

Data Source: yfinance (Yahoo Finance)
- Free, no API key required
- Reliable for MVP
- Includes earnings calendar, analyst estimates, price history
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List


from app.config import DATA_OUTPUT_DIR


class MarketDataFetcher:
    """Fetch market data using yfinance"""
    
    def __init__(self, data_dir: str | None = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_OUTPUT_DIR / "market_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.prices_dir = self.data_dir / "prices"
        self.earnings_dir = self.data_dir / "earnings"
        self.analysis_dir = self.data_dir / "analysis"
        
        for dir in [self.prices_dir, self.earnings_dir, self.analysis_dir]:
            dir.mkdir(exist_ok=True)
    
    def get_price_history(
        self, 
        ticker: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Get historical price data
        
        Args:
            ticker: Stock ticker symbol
            period: Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            interval: Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        
        Returns:
            DataFrame with OHLCV data
        """
        print(f"📊 Fetching price history for {ticker} ({period})...")
        
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        
        if df.empty:
            print(f"❌ No price data found for {ticker}")
            return pd.DataFrame()
        
        # Save to CSV
        csv_path = self.prices_dir / f"{ticker}_{period}_{interval}.csv"
        df.to_csv(csv_path)
        print(f"💾 Saved: {csv_path}")
        
        return df
    
    def get_earnings_dates(self, ticker: str) -> pd.DataFrame:
        """
        Get upcoming and historical earnings dates
        
        Returns:
            DataFrame with earnings dates and estimates
        """
        print(f"📅 Fetching earnings calendar for {ticker}...")
        
        stock = yf.Ticker(ticker)
        
        try:
            earnings_dates = stock.earnings_dates
            
            if earnings_dates is not None and not earnings_dates.empty:
                # Save to CSV
                csv_path = self.earnings_dir / f"{ticker}_earnings_calendar.csv"
                earnings_dates.to_csv(csv_path)
                print(f"💾 Saved: {csv_path}")
                
                return earnings_dates
            else:
                print(f"⚠️  No earnings dates available for {ticker}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error fetching earnings dates: {e}")
            return pd.DataFrame()
    
    def get_earnings_history(self, ticker: str) -> Dict:
        """
        Get historical earnings (quarterly and annual)
        
        Returns:
            Dict with 'quarterly' and 'annual' earnings DataFrames
        """
        print(f"📈 Fetching earnings history for {ticker}...")
        
        stock = yf.Ticker(ticker)
        
        result = {
            'quarterly': stock.quarterly_earnings,
            'annual': stock.earnings
        }
        
        # Save to JSON
        json_path = self.earnings_dir / f"{ticker}_earnings_history.json"
        
        save_data = {}
        if result['quarterly'] is not None and not result['quarterly'].empty:
            save_data['quarterly'] = result['quarterly'].to_dict()
        if result['annual'] is not None and not result['annual'].empty:
            save_data['annual'] = result['annual'].to_dict()
        
        with open(json_path, 'w') as f:
            json.dump(save_data, f, indent=2, default=str)
        
        print(f"💾 Saved: {json_path}")
        
        return result
    
    def get_analyst_estimates(self, ticker: str) -> Dict:
        """
        Get analyst estimates and recommendations
        
        Returns:
            Dict with estimates and recommendations
        """
        print(f"🎯 Fetching analyst data for {ticker}...")
        
        stock = yf.Ticker(ticker)
        
        result = {
            'recommendations': stock.recommendations,
            'analyst_price_targets': stock.analyst_price_targets,
            'earnings_estimate': stock.earnings_estimate,
            'revenue_estimate': stock.revenue_estimate
        }
        
        # Save to JSON
        json_path = self.analysis_dir / f"{ticker}_analyst_data.json"
        
        save_data = {}
        for key, value in result.items():
            if value is not None and not (isinstance(value, pd.DataFrame) and value.empty):
                if isinstance(value, pd.DataFrame):
                    save_data[key] = value.to_dict()
                else:
                    save_data[key] = value
        
        with open(json_path, 'w') as f:
            json.dump(save_data, f, indent=2, default=str)
        
        print(f"💾 Saved: {json_path}")
        
        return result
    
    def calculate_post_earnings_reaction(
        self,
        ticker: str,
        earnings_date: datetime,
        days_before: int = 1,
        days_after: int = 5
    ) -> Dict:
        """
        Calculate stock price reaction after earnings announcement
        
        Args:
            ticker: Stock ticker
            earnings_date: Date of earnings announcement
            days_before: Days before earnings to calculate baseline
            days_after: Days after earnings to track reaction
        
        Returns:
            Dict with price changes and analysis
        """
        print(f"🔍 Analyzing post-earnings reaction for {ticker} on {earnings_date.date()}...")
        
        # Get price data around earnings date
        start_date = earnings_date - timedelta(days=days_before + 5)
        end_date = earnings_date + timedelta(days=days_after + 5)
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date, interval="1d")
        
        if df.empty:
            print(f"❌ No price data available around {earnings_date.date()}")
            return {}
        
        # Find closest trading day to earnings date
        df['date_diff'] = abs((df.index - earnings_date).days)
        earnings_day_idx = df['date_diff'].idxmin()
        
        # Get before/after prices
        try:
            day_before_price = df.loc[:earnings_day_idx].iloc[-2]['Close']
            earnings_day_close = df.loc[earnings_day_idx]['Close']
            
            # Calculate returns over different periods
            reaction = {
                'earnings_date': str(earnings_date.date()),
                'day_before_close': float(day_before_price),
                'earnings_day_close': float(earnings_day_close),
                'immediate_reaction_%': float(((earnings_day_close - day_before_price) / day_before_price) * 100),
            }
            
            # Multi-day reaction
            after_df = df.loc[earnings_day_idx:].iloc[1:days_after+1]
            
            if not after_df.empty:
                for i, (date, row) in enumerate(after_df.iterrows(), 1):
                    reaction[f'day_{i}_close'] = float(row['Close'])
                    reaction[f'day_{i}_return_%'] = float(((row['Close'] - earnings_day_close) / earnings_day_close) * 100)
                    reaction[f'cumulative_return_day_{i}_%'] = float(((row['Close'] - day_before_price) / day_before_price) * 100)
            
            # Determine reaction type
            immediate = reaction['immediate_reaction_%']
            if abs(immediate) < 2:
                reaction['reaction_type'] = "Neutral"
            elif immediate > 0:
                reaction['reaction_type'] = "Positive" if immediate > 5 else "Slightly Positive"
            else:
                reaction['reaction_type'] = "Negative" if immediate < -5 else "Slightly Negative"
            
            print(f"📊 Immediate reaction: {immediate:.2f}% ({reaction['reaction_type']})")
            
            return reaction
            
        except Exception as e:
            print(f"❌ Error calculating reaction: {e}")
            return {}
    
    def get_earnings_surprise(self, ticker: str, limit: int = 8) -> pd.DataFrame:
        """
        Get earnings surprises (actual vs estimated)
        
        Args:
            ticker: Stock ticker
            limit: Number of quarters to retrieve
        
        Returns:
            DataFrame with earnings surprises
        """
        print(f"💡 Fetching earnings surprises for {ticker}...")
        
        # Get earnings dates which includes estimates vs actuals
        earnings_dates = self.get_earnings_dates(ticker)
        
        if earnings_dates.empty:
            return pd.DataFrame()
        
        # Filter to only historical (actuals available)
        surprises = earnings_dates[earnings_dates['Reported EPS'].notna()].head(limit)
        
        if not surprises.empty:
            # Calculate surprise percentage
            surprises = surprises.copy()
            surprises['EPS Surprise %'] = (
                (surprises['Reported EPS'] - surprises['EPS Estimate']) / 
                abs(surprises['EPS Estimate']) * 100
            )
            
            # Save to CSV
            csv_path = self.earnings_dir / f"{ticker}_earnings_surprises.csv"
            surprises.to_csv(csv_path)
            print(f"💾 Saved: {csv_path}")
        
        return surprises
    
    def analyze_earnings_pattern(self, ticker: str) -> Dict:
        """
        Analyze historical earnings surprise patterns
        
        Returns:
            Dict with pattern analysis
        """
        print(f"\n{'='*80}")
        print(f"📊 EARNINGS PATTERN ANALYSIS: {ticker}")
        print(f"{'='*80}\n")
        
        # Get earnings surprises
        surprises = self.get_earnings_surprise(ticker, limit=12)
        
        if surprises.empty:
            print("❌ No earnings surprise data available")
            return {}
        
        analysis = {
            'ticker': ticker,
            'quarters_analyzed': len(surprises),
            'beat_count': 0,
            'miss_count': 0,
            'meet_count': 0,
            'avg_surprise_%': 0,
            'consecutive_beats': 0,
            'consecutive_misses': 0
        }
        
        # Count beats/misses
        for _, row in surprises.iterrows():
            surprise = row['EPS Surprise %']
            if surprise > 1:  # Beat by >1%
                analysis['beat_count'] += 1
            elif surprise < -1:  # Miss by >1%
                analysis['miss_count'] += 1
            else:
                analysis['meet_count'] += 1
        
        analysis['avg_surprise_%'] = float(surprises['EPS Surprise %'].mean())
        analysis['beat_rate_%'] = (analysis['beat_count'] / len(surprises)) * 100
        
        # Check for consecutive patterns
        consecutive_beats = 0
        consecutive_misses = 0
        current_beat_streak = 0
        current_miss_streak = 0
        
        for _, row in surprises.iterrows():
            surprise = row['EPS Surprise %']
            if surprise > 1:
                current_beat_streak += 1
                current_miss_streak = 0
            elif surprise < -1:
                current_miss_streak += 1
                current_beat_streak = 0
            else:
                current_beat_streak = 0
                current_miss_streak = 0
            
            consecutive_beats = max(consecutive_beats, current_beat_streak)
            consecutive_misses = max(consecutive_misses, current_miss_streak)
        
        analysis['max_consecutive_beats'] = consecutive_beats
        analysis['max_consecutive_misses'] = consecutive_misses
        
        # Print summary
        print(f"📈 Pattern Summary:")
        print(f"   • Total Quarters: {analysis['quarters_analyzed']}")
        print(f"   • Beats: {analysis['beat_count']} ({analysis['beat_rate_%']:.1f}%)")
        print(f"   • Misses: {analysis['miss_count']}")
        print(f"   • Meets: {analysis['meet_count']}")
        print(f"   • Avg Surprise: {analysis['avg_surprise_%']:.2f}%")
        print(f"   • Max Consecutive Beats: {analysis['max_consecutive_beats']}")
        
        # Save analysis
        json_path = self.analysis_dir / f"{ticker}_earnings_pattern.json"
        with open(json_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"\n💾 Saved: {json_path}")
        
        return analysis
    
    def get_company_info(self, ticker: str) -> Dict:
        """Get basic company information"""
        stock = yf.Ticker(ticker)
        return stock.info
