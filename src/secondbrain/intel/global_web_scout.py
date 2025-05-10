"""
Global Web Scout - Advanced Web Intelligence Module.
"""
import aiohttp
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional, Set
from pathlib import Path

from .web_summarizer import WebSummarizer

logger = logging.getLogger(__name__)

class GlobalWebScout:
    def __init__(self):
        self.sources = [
            # Tech News
            "https://www.technologyreview.com/",
            "https://www.theverge.com/tech",
            "https://techcrunch.com/",
            "https://www.wired.com/",
            "https://venturebeat.com/",
            "https://www.zdnet.com/",
            # AI/ML Sources
            "https://arxiv.org/list/cs.AI/recent",
            "https://arxiv.org/list/cs.LG/recent",
            "https://openai.com/blog",
            "https://ai.googleblog.com/",
            "https://deepmind.com/blog",
            "https://blogs.microsoft.com/ai/",
            # Security
            "https://www.darkreading.com/",
            "https://www.schneier.com/",
            "https://krebsonsecurity.com/",
            "https://www.securityweek.com/",
            # Quantum Computing
            "https://quantum-computing.ibm.com/blog",
            "https://quantumzeitgeist.com/",
            "https://www.quantum.gov/news/",
            # Blockchain/Crypto
            "https://cointelegraph.com/",
            "https://decrypt.co/",
            "https://www.coindesk.com/",
            # Research & Innovation
            "https://www.nature.com/subjects/technology",
            "https://www.sciencedaily.com/technology/"
        ]
        self.scan_interval = 1200  # every 20 minutes
        self.last_updates: Dict[str, str] = {}
        self.trends_file = "adaptive_learning.json"
        self.trend_history: List[Dict[str, Any]] = []
        self.trend_categories = {
            "ai_ml": [
                "artificial intelligence", "machine learning", "neural network", 
                "deep learning", "AI model", "GPT", "transformer", "large language model",
                "reinforcement learning", "computer vision", "NLP", "robotics"
            ],
            "quantum": [
                "quantum computer", "qubit", "quantum supremacy", "quantum algorithm",
                "quantum network", "quantum encryption", "quantum sensor", "quantum internet"
            ],
            "security": [
                "vulnerability", "exploit", "cyber attack", "zero-day", "breach", 
                "encryption", "malware", "ransomware", "cybersecurity", "authentication"
            ],
            "blockchain": [
                "blockchain", "cryptocurrency", "smart contract", "web3", "defi", 
                "nft", "dao", "digital currency", "crypto", "distributed ledger"
            ],
            "innovation": [
                "breakthrough", "revolution", "novel", "pioneering", "groundbreaking",
                "disruptive", "cutting-edge", "state-of-the-art", "next-generation"
            ],
            "ethics": [
                "privacy", "bias", "fairness", "transparency", "accountability",
                "regulation", "compliance", "ethical AI", "responsible innovation"
            ]
        }
        self.trend_weights = {
            "ai_ml": 1.2,
            "quantum": 1.3,
            "security": 1.1,
            "blockchain": 0.9,
            "innovation": 1.0,
            "ethics": 1.15
        }
        self.sentiment_keywords = {
            "positive": [
                "breakthrough", "success", "achievement", "improvement", "advance",
                "revolutionary", "innovative", "efficient", "beneficial", "promising"
            ],
            "negative": [
                "concern", "risk", "threat", "problem", "issue", "vulnerability",
                "dangerous", "harmful", "failure", "controversy"
            ],
            "neutral": [
                "research", "study", "analysis", "development", "implementation",
                "testing", "evaluation", "investigation", "observation"
            ]
        }
        self._load_trend_history()
        self.samantha = None  # Will be set by brain controller
        self.summarizer = WebSummarizer()  # Initialize the summarizer

    async def fetch(self, session: aiohttp.ClientSession, url: str) -> Tuple[str, Optional[str]]:
        """Fetch content from a URL."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; SecondBrainBot/1.0; +http://example.com/bot)"
            }
            async with session.get(url, timeout=15, headers=headers) as response:
                text = await response.text()
                logger.info(f"[WebScout] Fetched {url} at {datetime.utcnow()}")
                return url, text[:5000]  # Store larger preview for better analysis
        except Exception as e:
            logger.warning(f"[WebScout] Failed to fetch {url}: {e}")
            return url, None

    async def monitor(self) -> None:
        """Continuously monitor web sources."""
        logger.info("[WebScout] Starting global web monitoring...")
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    tasks = [self.fetch(session, url) for url in self.sources]
                    results = await asyncio.gather(*tasks)
                    await self.analyze(results)
                await asyncio.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"[WebScout] Monitor error: {e}")
                await asyncio.sleep(300)  # retry after 5 minutes

    async def analyze(self, results: List[Tuple[str, Optional[str]]]) -> None:
        """
        Analyze fetched content for trends and updates with intelligent summarization.
        
        Args:
            results: List of (url, content) tuples
        """
        trends = []
        for url, content in results:
            if not content or content == self.last_updates.get(url):
                continue
                
            logger.info(f"[WebScout] Detected update on {url}")
            self.last_updates[url] = content
            
            # Extract key trends
            trend = self._extract_trend(url, content)
            if trend:
                trends.append(trend)
                
                # Get intelligent summary if Samantha is available
                if hasattr(self, 'samantha') and self.samantha:
                    try:
                        # Get detailed summary
                        summary = await self.summarizer.fetch_and_summarize(url)
                        
                        # Format trend announcement
                        source = url.split('//')[-1].split('/')[0]
                        category = trend.get("primary_category", "").replace("_", " ").title()
                        
                        message = (
                            f"New {category} trend detected from {source}.\n\n"
                            f"{summary}"
                        )
                        
                        # Announce through Samantha
                        asyncio.create_task(self.samantha.announce_trend(message, url))
                        
                    except Exception as e:
                        logger.error(f"Error processing trend summary: {e}")
                        # Fallback to basic announcement
                        headline = f"New article available at {source}"
                        asyncio.create_task(self.samantha.announce_trend(headline, url))
                
        if trends:
            await self._process_trends(trends)

    def _extract_trend(self, url: str, content: str) -> Optional[Dict[str, Any]]:
        """Extract trend information with enhanced analysis."""
        try:
            # Calculate category matches
            category_scores = {}
            found_keywords: Set[str] = set()
            sentiment_scores = {"positive": 0, "negative": 0, "neutral": 0}
            
            # Analyze categories and keywords
            for category, keywords in self.trend_categories.items():
                score = 0
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        score += 1
                        found_keywords.add(keyword)
                
                if score > 0:
                    # Apply category weight
                    category_scores[category] = score * self.trend_weights.get(category, 1.0)
            
            # Analyze sentiment
            for sentiment, keywords in self.sentiment_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        sentiment_scores[sentiment] += 1
            
            if category_scores:
                # Calculate confidence and impact
                max_score = max(category_scores.values())
                total_score = sum(category_scores.values())
                confidence = min(0.95, (total_score / len(category_scores)) / 5)
                
                # Calculate overall sentiment
                max_sentiment = max(sentiment_scores.items(), key=lambda x: x[1])[0]
                sentiment_strength = sentiment_scores[max_sentiment] / sum(sentiment_scores.values())
                
                # Determine primary category
                primary_category = max(category_scores.items(), key=lambda x: x[1])[0]
                
                # Extract potential impact metrics
                cross_domain_impact = len([s for s in category_scores.values() if s > 1])
                novelty_score = 1.0 if "innovation" in category_scores else 0.5
                
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": url,
                    "keywords": list(found_keywords),
                    "preview": content[:500],
                    "confidence": confidence,
                    "category_scores": category_scores,
                    "primary_category": primary_category,
                    "impact_score": max_score,
                    "sentiment": {
                        "primary": max_sentiment,
                        "strength": sentiment_strength,
                        "scores": sentiment_scores
                    },
                    "metrics": {
                        "cross_domain_impact": cross_domain_impact,
                        "novelty": novelty_score,
                        "total_relevance": total_score
                    }
                }
        except Exception as e:
            logger.error(f"Error extracting trend: {e}")
        return None

    async def _process_trends(self, trends: List[Dict[str, Any]]) -> None:
        """Process trends with enhanced analysis."""
        try:
            for trend in trends:
                # Add trend to history
                self.trend_history.append(trend)
                
                # Generate detailed summary
                summary = self._generate_trend_summary(trend)
                if summary:
                    trend["summary"] = summary
                
                # Save immediately for real-time access
                await self._save_trend_history()
                
                # Generate alert if significant
                alert = self._generate_trend_alert(trend)
                if alert:
                    logger.info(f"[WebScout] {alert}")
                    
        except Exception as e:
            logger.error(f"Error processing trends: {e}")

    def _generate_trend_summary(self, trend: Dict[str, Any]) -> Optional[str]:
        """Generate a detailed trend summary."""
        try:
            category = trend.get("primary_category", "").replace("_", " ").title()
            scores = trend.get("category_scores", {})
            impact = trend.get("impact_score", 0)
            sentiment = trend.get("sentiment", {})
            metrics = trend.get("metrics", {})
            
            summary_parts = []
            
            # Add category and sentiment context
            sentiment_desc = sentiment.get("primary", "neutral")
            if category:
                summary_parts.append(
                    f"Major {category} development detected with "
                    f"{sentiment_desc} implications"
                )
            
            # Add impact assessment
            if impact > 2:
                cross_impact = metrics.get("cross_domain_impact", 0)
                if cross_impact > 1:
                    summary_parts.append(
                        "showing significant cross-domain implications"
                    )
                else:
                    summary_parts.append(
                        "with potentially significant impact"
                    )
            
            # Add cross-domain insights
            related_categories = [
                cat.replace("_", " ").title()
                for cat, score in scores.items()
                if score > 1 and cat != trend.get("primary_category")
            ]
            if related_categories:
                summary_parts.append(
                    f"showing connections to {' and '.join(related_categories)}"
                )
            
            # Add novelty assessment
            if metrics.get("novelty", 0) > 0.8:
                summary_parts.append(
                    "representing a novel advancement in the field"
                )
            
            if summary_parts:
                return ". ".join(summary_parts) + "."
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
        return None

    def _generate_trend_alert(self, trend: Dict[str, Any]) -> Optional[str]:
        """Generate enhanced trend alert."""
        try:
            if trend.get("impact_score", 0) > 1.5:
                category = trend.get("primary_category", "").replace("_", " ").title()
                confidence = trend.get("confidence", 0)
                keywords = ", ".join(trend.get("keywords", []))
                
                return (
                    f"High-impact {category} trend detected "
                    f"(confidence: {confidence:.2f}): {keywords}"
                )
        except Exception as e:
            logger.error(f"Error generating alert: {e}")
        return None

    def _load_trend_history(self) -> None:
        """Load saved trend history."""
        try:
            if Path(self.trends_file).exists():
                with open(self.trends_file, "r") as f:
                    data = json.load(f)
                    self.trend_history = data.get("trends", [])
        except Exception as e:
            logger.error(f"[WebScout] Failed to load trends: {e}")

    async def _save_trend_history(self) -> None:
        """Save trend history to file."""
        try:
            # Keep last 1000 trends
            data = {"trends": self.trend_history[-1000:]}
            with open(self.trends_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[WebScout] Failed to save trends: {e}")

    def get_latest_trends(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent trends.
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of recent trends
        """
        return self.trend_history[-limit:] 