"""
Financial Data Parser
Extracts and structures financial data from SEC EDGAR JSON responses
"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

from app.config import FINANCIAL_METRICS


class FinancialDataParser:
    """Parses SEC EDGAR company facts into structured financial data"""
    
    def __init__(self):
        self.metrics_config = FINANCIAL_METRICS
    
    def extract_metric(
        self, 
        facts_data: Dict, 
        metric_names: List[str],
        taxonomy: str = "us-gaap"
    ) -> Optional[pd.DataFrame]:
        """
        Extract a specific metric from company facts
        
        Args:
            facts_data: Company facts JSON from SEC
            metric_names: List of possible metric names to look for
            taxonomy: Accounting taxonomy (default: 'us-gaap')
            
        Returns:
            DataFrame with metric values over time, or None if not found
        """
        if not facts_data or 'facts' not in facts_data:
            return None
        
        taxonomy_data = facts_data['facts'].get(taxonomy, {})
        
        # Try each possible metric name
        for metric_name in metric_names:
            if metric_name in taxonomy_data:
                metric_data = taxonomy_data[metric_name]
                
                # Get USD values (most common)
                if 'units' in metric_data and 'USD' in metric_data['units']:
                    values = metric_data['units']['USD']
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(values)
                    
                    # Convert end date to datetime
                    if 'end' in df.columns:
                        df['end'] = pd.to_datetime(df['end'])
                    
                    return df
        
        return None
    
    def get_latest_annual_value(
        self, 
        metric_df: pd.DataFrame, 
        fiscal_year: Optional[int] = None
    ) -> Optional[float]:
        """
        Get the latest annual (10-K) value for a metric
        
        Args:
            metric_df: DataFrame with metric values
            fiscal_year: Specific fiscal year to get (default: latest)
            
        Returns:
            Latest annual value or None
        """
        if metric_df is None or metric_df.empty:
            return None
        
        # Filter for annual reports (10-K)
        annual = metric_df[metric_df['form'] == '10-K'].copy()
        
        if annual.empty:
            return None
        
        # Filter by fiscal year if specified
        if fiscal_year and 'fy' in annual.columns:
            annual = annual[annual['fy'] == fiscal_year]
        
        if annual.empty:
            return None
        
        # Get most recent entry
        latest = annual.sort_values('end', ascending=False).iloc[0]
        return latest.get('val')
    
    def get_latest_quarterly_value(
        self, 
        metric_df: pd.DataFrame,
        fiscal_year: Optional[int] = None,
        fiscal_period: Optional[str] = None
    ) -> Optional[float]:
        """
        Get the latest quarterly (10-Q) value for a metric
        
        Args:
            metric_df: DataFrame with metric values
            fiscal_year: Specific fiscal year
            fiscal_period: Specific fiscal period (Q1, Q2, Q3, Q4)
            
        Returns:
            Latest quarterly value or None
        """
        if metric_df is None or metric_df.empty:
            return None
        
        # Filter for quarterly reports (10-Q)
        quarterly = metric_df[metric_df['form'].isin(['10-Q', '10-K'])].copy()
        
        if quarterly.empty:
            return None
        
        # Filter by fiscal year if specified
        if fiscal_year and 'fy' in quarterly.columns:
            quarterly = quarterly[quarterly['fy'] == fiscal_year]
        
        # Filter by fiscal period if specified
        if fiscal_period and 'fp' in quarterly.columns:
            quarterly = quarterly[quarterly['fp'] == fiscal_period]
        
        if quarterly.empty:
            return None
        
        # Get most recent entry
        latest = quarterly.sort_values('end', ascending=False).iloc[0]
        return latest.get('val')

    def get_latest_non_null(self, df: pd.DataFrame, column: str) -> Optional[float]:
        """Get the most recent non-null value for a column."""
        if df is None or df.empty or column not in df.columns:
            return None

        ordered = df.sort_values('end', ascending=False)
        for value in ordered[column]:
            if pd.notna(value):
                return value

        return None
    
    def extract_all_metrics(
        self, 
        facts_data: Dict,
        form_type: str = '10-K'
    ) -> pd.DataFrame:
        """
        Extract all configured financial metrics
        
        Args:
            facts_data: Company facts JSON from SEC
            form_type: Form type to filter ('10-K' for annual, '10-Q' for quarterly)
            
        Returns:
            DataFrame with all metrics over time
        """
        all_data = []
        
        for metric_label, metric_names in self.metrics_config.items():
            metric_df = self.extract_metric(facts_data, metric_names)
            
            if metric_df is not None and not metric_df.empty:
                # Filter by form type
                filtered = metric_df[metric_df['form'] == form_type].copy()
                
                if not filtered.empty:
                    # Keep relevant columns
                    filtered = filtered[['end', 'val', 'fy', 'fp', 'form']].copy()
                    filtered['metric'] = metric_label
                    all_data.append(filtered)
        
        if not all_data:
            return pd.DataFrame()
        
        # Combine all metrics
        combined = pd.concat(all_data, ignore_index=True)
        
        # Pivot to wide format for easier analysis
        pivot = combined.pivot_table(
            index=['end', 'fy', 'fp', 'form'],
            columns='metric',
            values='val',
            aggfunc='first'
        ).reset_index()
        
        return pivot
    
    def create_financial_summary(
        self, 
        facts_data: Dict,
        num_periods: int = 5
    ) -> Dict[str, pd.DataFrame]:
        """
        Create comprehensive financial summary
        
        Args:
            facts_data: Company facts JSON from SEC
            num_periods: Number of periods to include (default: 5)
            
        Returns:
            Dictionary with 'annual' and 'quarterly' DataFrames
        """
        summary = {}
        
        # Annual data (10-K)
        annual_df = self.extract_all_metrics(facts_data, form_type='10-K')
        if not annual_df.empty:
            annual_df = annual_df.sort_values('end', ascending=False).head(num_periods)
            summary['annual'] = annual_df
        
        # Quarterly data (10-Q)
        quarterly_df = self.extract_all_metrics(facts_data, form_type='10-Q')
        if not quarterly_df.empty:
            quarterly_df = quarterly_df.sort_values('end', ascending=False).head(num_periods)
            summary['quarterly'] = quarterly_df
        
        return summary
    
    def calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate derived financial metrics
        
        Args:
            df: DataFrame with base financial metrics
            
        Returns:
            DataFrame with additional calculated metrics
        """
        df = df.copy()
        
        # Free Cash Flow = Operating Cash Flow - Capex
        if 'OperatingCashFlow' in df.columns and 'Capex' in df.columns:
            df['CalculatedFCF'] = df['OperatingCashFlow'] - df['Capex'].abs()
        
        # Profit Margin = Net Income / Revenue
        if 'NetIncome' in df.columns and 'Revenue' in df.columns:
            df['ProfitMargin'] = (df['NetIncome'] / df['Revenue'] * 100).round(2)
        
        # Gross Margin = Gross Profit / Revenue
        if 'GrossProfit' in df.columns and 'Revenue' in df.columns:
            df['GrossMargin'] = (df['GrossProfit'] / df['Revenue'] * 100).round(2)
        
        # Current Ratio = Current Assets / Current Liabilities
        if 'CurrentAssets' in df.columns and 'CurrentLiabilities' in df.columns:
            df['CurrentRatio'] = (df['CurrentAssets'] / df['CurrentLiabilities']).round(2)
        
        # Debt to Equity = Long Term Debt / Equity
        if 'LongTermDebt' in df.columns and 'Equity' in df.columns:
            df['DebtToEquity'] = (df['LongTermDebt'] / df['Equity']).round(2)
        
        # Return on Assets = Net Income / Assets
        if 'NetIncome' in df.columns and 'Assets' in df.columns:
            df['ROA'] = (df['NetIncome'] / df['Assets'] * 100).round(2)
        
        # Return on Equity = Net Income / Equity
        if 'NetIncome' in df.columns and 'Equity' in df.columns:
            df['ROE'] = (df['NetIncome'] / df['Equity'] * 100).round(2)
        
        return df
    
    def calculate_growth_rates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Year-over-Year growth rates
        
        Args:
            df: DataFrame with financial metrics sorted by date (newest first)
            
        Returns:
            DataFrame with growth rate columns added
        """
        if df.empty or len(df) < 2:
            return df
        
        df = df.copy().sort_values('end', ascending=False).reset_index(drop=True)
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        for col in numeric_cols:
            if col not in ['fy', 'fp']:
                growth_col = f"{col}_YoY_%"
                df[growth_col] = ((df[col] / df[col].shift(-1) - 1) * 100).round(2)
        
        return df


def format_large_number(num: float) -> str:
    """Format large numbers in readable format (millions, billions)"""
    if pd.isna(num):
        return "N/A"
    
    abs_num = abs(num)
    if abs_num >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"${num/1_000_000:.2f}M"
    elif abs_num >= 1_000:
        return f"${num/1_000:.2f}K"
    else:
        return f"${num:.2f}"
