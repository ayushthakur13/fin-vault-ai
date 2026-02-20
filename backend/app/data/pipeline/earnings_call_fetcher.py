"""
Earnings Call Data Fetcher
Downloads and analyzes earnings call transcripts, audio, and slides
"""
import json
from typing import Dict, List, Optional
from datetime import datetime

try:
    from earningscall import get_company
except ImportError:
    print("⚠️  earningscall library not installed. Run: pip install earningscall")
    get_company = None

from app.config import DATA_OUTPUT_DIR


class EarningsCallFetcher:
    """Fetches earnings call transcripts and audio files"""
    
    def __init__(self):
        """Initialize earnings call fetcher"""
        self.earnings_dir = DATA_OUTPUT_DIR / "earnings_calls"
        self.transcripts_dir = self.earnings_dir / "transcripts"
        self.audio_dir = self.earnings_dir / "audio"
        self.analysis_dir = self.earnings_dir / "analysis"
        
        # Create directories
        for dir_path in [self.earnings_dir, self.transcripts_dir, self.audio_dir, self.analysis_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_transcript(
        self, 
        ticker: str, 
        year: int, 
        quarter: int,
        level: int = 4
    ) -> Optional[Dict]:
        """
        Get earnings call transcript
        
        Args:
            ticker: Stock ticker symbol
            year: Year of earnings call
            quarter: Quarter (1-4)
            level: Detail level:
                - 1: Basic text only
                - 2: Speaker-separated (with names/titles)
                - 3: Paragraphs separated
                - 4: Prepared remarks vs Q&A separated (BEST for analysis)
                
        Returns:
            Dictionary with transcript data
        """
        if get_company is None:
            print("❌ earningscall library not installed")
            return None
        
        try:
            print(f"\n📞 Fetching {ticker} Q{quarter} {year} earnings call transcript...")
            
            company = get_company(ticker.lower())
            transcript = company.get_transcript(year=year, quarter=quarter, level=level)
            
            result = {
                'ticker': ticker.upper(),
                'year': year,
                'quarter': quarter,
                'level': level,
                'date': getattr(transcript, 'date', None),
            }
            
            if level == 1:
                # Basic text only
                result['text'] = transcript.text
                print(f"   ✅ Retrieved basic transcript ({len(transcript.text)} chars)")
                
            elif level == 2:
                # Speaker-separated
                speakers_data = []
                for speaker in transcript.speakers:
                    speakers_data.append({
                        'name': speaker.speaker_info.name,
                        'title': speaker.speaker_info.title,
                        'text': speaker.text
                    })
                result['speakers'] = speakers_data
                print(f"   ✅ Retrieved transcript with {len(speakers_data)} speakers")
                
            elif level == 4:
                # Prepared remarks vs Q&A
                result['prepared_remarks'] = transcript.prepared_remarks
                result['qa_section'] = transcript.questions_and_answers
                
                print(f"   ✅ Retrieved structured transcript:")
                print(f"      • Prepared remarks: {len(result['prepared_remarks'])} chars")
                print(f"      • Q&A section: {len(result['qa_section'])} chars")
            
            # Save to file
            self._save_transcript(result)
            
            return result
            
        except Exception as e:
            print(f"   ❌ Error fetching transcript: {e}")
            return None
    
    def download_audio(
        self, 
        ticker: str, 
        year: int, 
        quarter: int
    ) -> Optional[str]:
        """
        Download earnings call audio file
        
        Args:
            ticker: Stock ticker symbol
            year: Year of earnings call
            quarter: Quarter (1-4)
            
        Returns:
            Path to downloaded audio file
        """
        if get_company is None:
            print("❌ earningscall library not installed")
            return None
        
        try:
            print(f"\n🎧 Downloading {ticker} Q{quarter} {year} audio...")
            
            company = get_company(ticker.lower())
            
            filename = f"{ticker}_Q{quarter}_{year}.mp3"
            filepath = self.audio_dir / filename
            
            company.download_audio_file(
                year=year, 
                quarter=quarter, 
                file_name=str(filepath)
            )
            
            if filepath.exists():
                size_mb = filepath.stat().st_size / (1024 * 1024)
                print(f"   ✅ Downloaded audio: {filepath} ({size_mb:.1f} MB)")
                return str(filepath)
            else:
                print(f"   ❌ Audio download failed")
                return None
                
        except Exception as e:
            print(f"   ❌ Error downloading audio: {e}")
            return None
    
    def download_slides(
        self, 
        ticker: str, 
        year: int, 
        quarter: int
    ) -> Optional[str]:
        """
        Download earnings call presentation slides
        
        Args:
            ticker: Stock ticker symbol
            year: Year of earnings call
            quarter: Quarter (1-4)
            
        Returns:
            Path to downloaded slides
        """
        if get_company is None:
            print("❌ earningscall library not installed")
            return None
        
        try:
            print(f"\n📊 Downloading {ticker} Q{quarter} {year} slides...")
            
            company = get_company(ticker.lower())
            
            filename = f"{ticker}_Q{quarter}_{year}_slides.pdf"
            filepath = self.earnings_dir / "slides" / filename
            filepath.parent.mkdir(exist_ok=True)
            
            company.download_slides(
                year=year, 
                quarter=quarter, 
                file_name=str(filepath)
            )
            
            if filepath.exists():
                size_mb = filepath.stat().st_size / (1024 * 1024)
                print(f"   ✅ Downloaded slides: {filepath} ({size_mb:.1f} MB)")
                return str(filepath)
            else:
                print(f"   ⚠️  Slides not available")
                return None
                
        except Exception as e:
            print(f"   ⚠️  Slides not available: {e}")
            return None
    
    def analyze_transcript(self, transcript_data: Dict) -> Dict:
        """
        Analyze transcript for key insights
        
        Args:
            transcript_data: Transcript dictionary from get_transcript()
            
        Returns:
            Analysis dictionary with insights
        """
        analysis = {
            'ticker': transcript_data['ticker'],
            'year': transcript_data['year'],
            'quarter': transcript_data['quarter'],
            'insights': {}
        }
        
        if transcript_data.get('level') == 4:
            prepared = transcript_data.get('prepared_remarks', '')
            qa = transcript_data.get('qa_section', '')
            
            # Basic analysis
            analysis['insights'] = {
                'prepared_remarks_length': len(prepared),
                'qa_length': len(qa),
                'prepared_word_count': len(prepared.split()),
                'qa_word_count': len(qa.split()),
                'ratio_qa_to_prepared': len(qa) / len(prepared) if len(prepared) > 0 else 0,
            }
            
            # Keyword analysis
            analysis['insights']['keywords'] = self._extract_keywords(prepared, qa)
            
            print(f"\n📊 Analysis Summary:")
            print(f"   • Prepared remarks: {analysis['insights']['prepared_word_count']} words")
            print(f"   • Q&A section: {analysis['insights']['qa_word_count']} words")
            print(f"   • Q&A to Prepared ratio: {analysis['insights']['ratio_qa_to_prepared']:.2f}")
            
        elif transcript_data.get('level') == 2:
            speakers = transcript_data.get('speakers', [])
            
            # Speaker analysis
            speaker_stats = []
            for speaker in speakers:
                speaker_stats.append({
                    'name': speaker['name'],
                    'title': speaker['title'],
                    'word_count': len(speaker['text'].split()),
                    'char_count': len(speaker['text'])
                })
            
            analysis['insights']['speakers'] = speaker_stats
            analysis['insights']['total_speakers'] = len(speakers)
            
            print(f"\n👥 Speaker Analysis:")
            print(f"   • Total speakers: {len(speakers)}")
            for stat in speaker_stats[:5]:  # Show top 5
                print(f"   • {stat['name']} ({stat['title']}): {stat['word_count']} words")
        
        # Save analysis
        self._save_analysis(analysis)
        
        return analysis
    
    def _extract_keywords(self, prepared: str, qa: str) -> Dict[str, List[str]]:
        """Extract important keywords from prepared vs Q&A sections"""
        
        # Risk-related keywords
        risk_keywords = ['risk', 'concern', 'challenge', 'headwind', 'uncertainty', 
                        'pressure', 'difficult', 'weak', 'decline', 'loss']
        
        # Positive keywords
        positive_keywords = ['growth', 'strong', 'increase', 'improve', 'opportunity',
                           'momentum', 'success', 'gain', 'expand', 'optimize']
        
        # Financial metrics
        metric_keywords = ['revenue', 'margin', 'profit', 'earnings', 'cash flow',
                          'roce', 'roe', 'ebitda', 'guidance', 'outlook']
        
        def count_keywords(text, keywords):
            text_lower = text.lower()
            return {kw: text_lower.count(kw) for kw in keywords if text_lower.count(kw) > 0}
        
        return {
            'risks_in_prepared': count_keywords(prepared, risk_keywords),
            'risks_in_qa': count_keywords(qa, risk_keywords),
            'positive_in_prepared': count_keywords(prepared, positive_keywords),
            'positive_in_qa': count_keywords(qa, positive_keywords),
            'metrics_mentioned': count_keywords(prepared + qa, metric_keywords)
        }
    
    def _save_transcript(self, transcript_data: Dict):
        """Save transcript to JSON file"""
        filename = f"{transcript_data['ticker']}_Q{transcript_data['quarter']}_{transcript_data['year']}_L{transcript_data['level']}.json"
        filepath = self.transcripts_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 Saved transcript: {filepath}")
    
    def _save_analysis(self, analysis: Dict):
        """Save analysis to JSON file"""
        filename = f"{analysis['ticker']}_Q{analysis['quarter']}_{analysis['year']}_analysis.json"
        filepath = self.analysis_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 Saved analysis: {filepath}")
    
    def get_available_calls(self, ticker: str) -> List[Dict]:
        """
        Get list of available earnings calls for a company
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            List of available calls with dates
        """
        if get_company is None:
            print("❌ earningscall library not installed")
            return []
        
        try:
            print(f"\n📋 Checking available calls for {ticker}...")
            company = get_company(ticker.lower())
            
            # Try to get transcripts for recent quarters
            available = []
            current_year = datetime.now().year
            
            for year in range(current_year, current_year - 3, -1):
                for quarter in range(1, 5):
                    try:
                        transcript = company.get_transcript(year=year, quarter=quarter, level=1)
                        if transcript:
                            available.append({
                                'year': year,
                                'quarter': quarter,
                                'date': getattr(transcript, 'date', None)
                            })
                    except:
                        continue
            
            print(f"   ✅ Found {len(available)} available calls")
            return available
            
        except Exception as e:
            print(f"   ❌ Error checking available calls: {e}")
            return []
    
    def create_contradiction_report(self, transcript_data: Dict) -> Dict:
        """
        Detect contradictions between prepared remarks and Q&A
        Useful for bear case analysis
        
        Args:
            transcript_data: Level 4 transcript with prepared/qa separated
            
        Returns:
            Report highlighting potential contradictions
        """
        if transcript_data.get('level') != 4:
            print("⚠️  Contradiction analysis requires level 4 transcripts")
            return {}
        
        prepared = transcript_data.get('prepared_remarks', '').lower()
        qa = transcript_data.get('qa_section', '').lower()
        
        # Keywords that suggest different tones
        optimistic_prepared = ['strong', 'growth', 'success', 'opportunity', 'excellent']
        cautious_qa = ['concern', 'risk', 'challenge', 'pressure', 'difficult']
        
        report = {
            'ticker': transcript_data['ticker'],
            'year': transcript_data['year'],
            'quarter': transcript_data['quarter'],
            'flags': []
        }
        
        # Check if management is optimistic but Q&A reveals concerns
        optimism_count = sum(prepared.count(word) for word in optimistic_prepared)
        concern_count = sum(qa.count(word) for word in cautious_qa)
        
        if optimism_count > 5 and concern_count > optimism_count:
            report['flags'].append({
                'type': 'tone_mismatch',
                'description': 'Management optimistic in prepared remarks, but Q&A reveals analyst concerns',
                'prepared_optimism': optimism_count,
                'qa_concerns': concern_count
            })
        
        # Check for defensive language in Q&A
        defensive_phrases = ['as we mentioned', 'we already discussed', 'to be clear', 'let me clarify']
        defensive_count = sum(qa.count(phrase) for phrase in defensive_phrases)
        
        if defensive_count > 3:
            report['flags'].append({
                'type': 'defensive_responses',
                'description': 'Management using defensive language in Q&A',
                'count': defensive_count
            })
        
        print(f"\n🚩 Contradiction Report:")
        print(f"   • Flags detected: {len(report['flags'])}")
        for flag in report['flags']:
            print(f"   • {flag['type']}: {flag['description']}")
        
        return report
