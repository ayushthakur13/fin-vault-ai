import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "FinVault AI")
    env: str = os.getenv("ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_quick_model: str = os.getenv("GROQ_QUICK_MODEL", "llama-3.1-8b-instant")
    groq_deep_model: str = os.getenv("GROQ_DEEP_MODEL", "llama-3.3-70b-versatile")
    qdrant_url: str = os.getenv("QDRANT_URL", "")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "")


settings = Settings()


BASE_DIR = Path(__file__).resolve().parent
DATA_OUTPUT_DIR = BASE_DIR / "data" / "output"
CACHE_DIR = DATA_OUTPUT_DIR / "cache"

DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT_NAME = os.getenv("USER_AGENT_NAME", "FinVaultAI")
USER_AGENT_EMAIL = os.getenv("USER_AGENT_EMAIL", "user@example.com")

SEC_HEADERS = {
    "User-Agent": f"{USER_AGENT_NAME} ({USER_AGENT_EMAIL})",
    "Accept-Encoding": "gzip, deflate",
}

SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.2"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

FINANCIAL_METRICS = {
    "Revenue": [
		"RevenueFromContractWithCustomerExcludingAssessedTax",
		"Revenues",
		"SalesRevenueNet",
	],
	"NetIncome": ["NetIncomeLoss", "ProfitLoss"],
	"Assets": ["Assets"],
	"Liabilities": ["Liabilities"],
	"OperatingCashFlow": ["NetCashProvidedByUsedInOperatingActivities"],
	"Capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
	"Equity": ["StockholdersEquity"],
	"CurrentAssets": ["AssetsCurrent"],
	"CurrentLiabilities": ["LiabilitiesCurrent"],
	"LongTermDebt": ["LongTermDebt", "LongTermDebtNoncurrent"],
	"Cash": ["CashAndCashEquivalentsAtCarryingValue", "Cash"],
	"GrossProfit": ["GrossProfit"],
	"OperatingIncome": ["OperatingIncomeLoss"],
	"EBITDA": ["EBITDA"],
	"FreeCashFlow": ["FreeCashFlow"],
}
