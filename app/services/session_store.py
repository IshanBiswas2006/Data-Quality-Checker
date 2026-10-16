import time
import uuid
from typing import Dict, Any, Optional
import pandas as pd

class SessionStore:
    """
    In-memory session manager for temporary analysis sessions.
    Stores original dataset, working copy, applied operations, and metadata.
    """
    _sessions: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def create_session(cls, df: pd.DataFrame, filename: str) -> str:
        cls.cleanup_old_sessions()
        analysis_id = str(uuid.uuid4())
        cls._sessions[analysis_id] = {
            "id": analysis_id,
            "original_filename": filename,
            "created_at": time.time(),
            "original_df": df.copy(),
            "cleaned_df": df.copy(),
            "operations_history": [],
            "custom_rules": []
        }
        return analysis_id
        
    @classmethod
    def get_session(cls, analysis_id: str) -> Optional[Dict[str, Any]]:
        return cls._sessions.get(analysis_id)
        
    @classmethod
    def update_cleaned(cls, analysis_id: str, new_df: pd.DataFrame, log_entry: Dict[str, Any]) -> bool:
        session = cls.get_session(analysis_id)
        if not session:
            return False
        session["cleaned_df"] = new_df.copy()
        if log_entry:
            session["operations_history"].append(log_entry)
        return True
        
    @classmethod
    def reset_session(cls, analysis_id: str) -> bool:
        session = cls.get_session(analysis_id)
        if not session:
            return False
        session["cleaned_df"] = session["original_df"].copy()
        session["operations_history"] = []
        return True
        
    @classmethod
    def cleanup_old_sessions(cls, max_age_seconds: int = 7200) -> None:
        now = time.time()
        expired = [sid for sid, s in cls._sessions.items() if now - s["created_at"] > max_age_seconds]
        for sid in expired:
            del cls._sessions[sid]
            
    @classmethod
    def clear_all(cls) -> None:
        """For testing purposes."""
        cls._sessions.clear()
