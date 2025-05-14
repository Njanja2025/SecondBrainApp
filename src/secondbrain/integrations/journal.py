"""
Journal System Integration Module
"""

import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class JournalSystem:
    """Integration with the journal system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize journal system integration."""
        self.config = config
        self.journal_dir = Path("data/journal")
        self.tags_file = Path("data/journal/tags.json")
        self.stats_file = Path("data/journal/stats.json")
        self.tags = set()
        self.stats = {
            "total_entries": 0,
            "total_words": 0,
            "most_used_tags": {},
            "last_updated": None,
            "entry_dates": [],
            "word_count_history": []
        }
        self._initialize_journal()
        
    def _initialize_journal(self):
        """Initialize journal system and directories."""
        try:
            self.journal_dir.mkdir(parents=True, exist_ok=True)
            self._load_tags()
            self._load_stats()
            logger.info("Journal system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing journal system: {e}")
            raise
    
    def _load_tags(self):
        """Load journal tags from file."""
        try:
            if self.tags_file.exists():
                with open(self.tags_file, "r") as f:
                    self.tags = set(json.load(f))
                logger.info(f"Loaded {len(self.tags)} tags")
        except Exception as e:
            logger.error(f"Error loading tags: {e}")
            self.tags = set()
    
    def _save_tags(self):
        """Save journal tags to file with atomic write."""
        try:
            temp_file = self.tags_file.with_suffix('.json.tmp')
            with open(temp_file, "w") as f:
                json.dump(list(self.tags), f, indent=2)
            temp_file.replace(self.tags_file)
            logger.info("Tags saved successfully")
        except Exception as e:
            logger.error(f"Error saving tags: {e}")
            raise
    
    def _load_stats(self):
        """Load journal statistics from file."""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, "r") as f:
                    self.stats = json.load(f)
                logger.info("Loaded journal statistics")
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
            self.stats = {
                "total_entries": 0,
                "total_words": 0,
                "most_used_tags": {},
                "last_updated": None,
                "entry_dates": [],
                "word_count_history": []
            }
    
    def _save_stats(self):
        """Save journal statistics to file with atomic write."""
        try:
            temp_file = self.stats_file.with_suffix('.json.tmp')
            with open(temp_file, "w") as f:
                json.dump(self.stats, f, indent=2)
            temp_file.replace(self.stats_file)
            logger.info("Statistics saved successfully")
        except Exception as e:
            logger.error(f"Error saving statistics: {e}")
            raise
    
    def _update_stats(self, entry: Dict[str, Any], is_new: bool = True):
        """Update journal statistics."""
        try:
            # Update total entries
            if is_new:
                self.stats["total_entries"] += 1
                self.stats["entry_dates"].append(entry["created_at"])
            
            # Update word count
            word_count = len(entry["content"].split())
            if is_new:
                self.stats["total_words"] += word_count
            else:
                # Adjust total words for edited entry
                old_word_count = len(entry.get("old_content", "").split())
                self.stats["total_words"] = self.stats["total_words"] - old_word_count + word_count
            
            # Update word count history
            self.stats["word_count_history"].append({
                "date": entry["created_at"],
                "count": word_count
            })
            
            # Update tags
            for tag in entry.get("tags", []):
                self.stats["most_used_tags"][tag] = self.stats["most_used_tags"].get(tag, 0) + 1
            
            # Update last updated timestamp
            self.stats["last_updated"] = datetime.now().isoformat()
            
            self._save_stats()
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    def start_journal(self, content: str = "", tags: List[str] = None) -> Dict[str, Any]:
        """Start a new journal entry."""
        try:
            entry_id = f"entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            entry = {
                "id": entry_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "content": content,
                "tags": tags or [],
                "word_count": len(content.split())
            }
            
            # Save entry
            entry_file = self.journal_dir / f"{entry_id}.json"
            with open(entry_file, "w") as f:
                json.dump(entry, f, indent=2)
            
            # Update tags and stats
            self.tags.update(tags or [])
            self._save_tags()
            self._update_stats(entry)
            
            return {
                "status": "success",
                "message": "Journal entry created",
                "entry": entry
            }
        except Exception as e:
            logger.error(f"Error creating journal entry: {e}")
            return {"status": "error", "error": str(e)}
    
    def read_journal(self, entry_id: str = None) -> Dict[str, Any]:
        """Read journal entries."""
        try:
            if entry_id:
                # Read specific entry
                entry_file = self.journal_dir / f"{entry_id}.json"
                if not entry_file.exists():
                    return {"status": "error", "error": "Entry not found"}
                
                with open(entry_file, "r") as f:
                    entry = json.load(f)
                return {
                    "status": "success",
                    "entry": entry
                }
            else:
                # List all entries
                entries = []
                for entry_file in self.journal_dir.glob("entry_*.json"):
                    try:
                        with open(entry_file, "r") as f:
                            entry = json.load(f)
                            entries.append(entry)
                    except Exception as e:
                        logger.error(f"Error reading entry {entry_file}: {e}")
                        continue
                
                # Sort entries by creation date
                entries.sort(key=lambda x: x["created_at"], reverse=True)
                
                return {
                    "status": "success",
                    "entries": entries,
                    "count": len(entries)
                }
        except Exception as e:
            logger.error(f"Error reading journal: {e}")
            return {"status": "error", "error": str(e)}
    
    def edit_entry(self, entry_id: str, content: str = None, tags: List[str] = None) -> Dict[str, Any]:
        """Edit a journal entry."""
        try:
            entry_file = self.journal_dir / f"{entry_id}.json"
            if not entry_file.exists():
                return {"status": "error", "error": "Entry not found"}
            
            # Read current entry
            with open(entry_file, "r") as f:
                entry = json.load(f)
            
            # Store old content for stats update
            entry["old_content"] = entry["content"]
            
            # Update entry
            if content is not None:
                entry["content"] = content
                entry["word_count"] = len(content.split())
            if tags is not None:
                entry["tags"] = tags
            
            entry["updated_at"] = datetime.now().isoformat()
            
            # Save updated entry
            with open(entry_file, "w") as f:
                json.dump(entry, f, indent=2)
            
            # Update tags and stats
            self.tags.update(tags or [])
            self._save_tags()
            self._update_stats(entry, is_new=False)
            
            return {
                "status": "success",
                "message": "Journal entry updated",
                "entry": entry
            }
        except Exception as e:
            logger.error(f"Error editing journal entry: {e}")
            return {"status": "error", "error": str(e)}
    
    def delete_entry(self, entry_id: str) -> Dict[str, Any]:
        """Delete a journal entry."""
        try:
            entry_file = self.journal_dir / f"{entry_id}.json"
            if not entry_file.exists():
                return {"status": "error", "error": "Entry not found"}
            
            # Read entry for stats update
            with open(entry_file, "r") as f:
                entry = json.load(f)
            
            # Delete entry
            entry_file.unlink()
            
            # Update stats
            self.stats["total_entries"] -= 1
            self.stats["total_words"] -= entry["word_count"]
            self.stats["entry_dates"].remove(entry["created_at"])
            self.stats["last_updated"] = datetime.now().isoformat()
            
            # Update tags
            for tag in entry.get("tags", []):
                self.stats["most_used_tags"][tag] = max(0, self.stats["most_used_tags"].get(tag, 0) - 1)
                if self.stats["most_used_tags"][tag] == 0:
                    del self.stats["most_used_tags"][tag]
            
            self._save_stats()
            
            return {
                "status": "success",
                "message": "Journal entry deleted",
                "deleted_entry": entry
            }
        except Exception as e:
            logger.error(f"Error deleting journal entry: {e}")
            return {"status": "error", "error": str(e)}
    
    def search_journal(self, query: str) -> Dict[str, Any]:
        """Search journal entries."""
        try:
            query = query.lower()
            results = []
            
            for entry_file in self.journal_dir.glob("entry_*.json"):
                try:
                    with open(entry_file, "r") as f:
                        entry = json.load(f)
                        if (query in entry["content"].lower() or
                            query in entry["id"].lower() or
                            any(query in tag.lower() for tag in entry.get("tags", []))):
                            results.append(entry)
                except Exception as e:
                    logger.error(f"Error reading entry {entry_file}: {e}")
                    continue
            
            # Sort results by creation date
            results.sort(key=lambda x: x["created_at"], reverse=True)
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Error searching journal: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_tags(self) -> Dict[str, Any]:
        """Get all journal tags."""
        try:
            return {
                "status": "success",
                "tags": list(self.tags),
                "count": len(self.tags)
            }
        except Exception as e:
            logger.error(f"Error getting tags: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get journal statistics."""
        try:
            return {
                "status": "success",
                "stats": self.stats
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_word_count_history(self) -> Dict[str, Any]:
        """Get word count history over time."""
        try:
            return {
                "status": "success",
                "history": self.stats["word_count_history"],
                "total_words": self.stats["total_words"],
                "average_words": self.stats["total_words"] / max(1, self.stats["total_entries"])
            }
        except Exception as e:
            logger.error(f"Error getting word count history: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_most_used_tags(self, limit: int = 10) -> Dict[str, Any]:
        """Get most used tags."""
        try:
            sorted_tags = sorted(
                self.stats["most_used_tags"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return {
                "status": "success",
                "tags": [{"tag": tag, "count": count} for tag, count in sorted_tags],
                "total_tags": len(self.stats["most_used_tags"])
            }
        except Exception as e:
            logger.error(f"Error getting most used tags: {e}")
            return {"status": "error", "error": str(e)} 