"""
File-based storage service for Easy-KME server.
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..models.data_models import StorageData, Key, Session, SAERegistry, KeyPool
from ..config import get_settings

logger = logging.getLogger(__name__)


class StorageService:
    """File-based storage service for KME data."""
    
    def __init__(self):
        self.settings = get_settings()
        self.data_dir = Path(self.settings.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.keys_file = self.data_dir / "keys.json"
        self.sessions_file = self.data_dir / "sessions.json"
        self.sae_registry_file = self.data_dir / "sae_registry.json"
        self.key_pool_file = self.data_dir / "key_pool.json"
        
        # Initialize storage
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage files if they don't exist."""
        if not self.key_pool_file.exists():
            self._create_initial_key_pool()
        
        if not self.sae_registry_file.exists():
            self._save_json(self.sae_registry_file, [])
        
        if not self.keys_file.exists():
            self._save_json(self.keys_file, [])
        
        if not self.sessions_file.exists():
            self._save_json(self.sessions_file, [])
    
    def _create_initial_key_pool(self):
        """Create initial key pool configuration."""
        key_pool = KeyPool(
            current_size=0,
            max_size=self.settings.key_pool_size,
            key_size=self.settings.key_size
        )
        self._save_json(self.key_pool_file, key_pool.dict())
    
    def _load_json(self, file_path: Path) -> Any:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading {file_path}: {e}")
            return None
    
    def _save_json(self, file_path: Path, data: Any):
        """Save JSON data to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")
            raise
    
    def get_key_pool(self) -> KeyPool:
        """Get current key pool status."""
        data = self._load_json(self.key_pool_file)
        if data is None:
            return self._create_initial_key_pool()
        return KeyPool(**data)
    
    def update_key_pool(self, key_pool: KeyPool):
        """Update key pool status."""
        self._save_json(self.key_pool_file, key_pool.dict())
    
    def get_keys(self) -> List[Key]:
        """Get all keys from storage."""
        data = self._load_json(self.keys_file)
        if data is None:
            return []
        return [Key(**key_data) for key_data in data]
    
    def save_keys(self, keys: List[Key]):
        """Save keys to storage."""
        self._save_json(self.keys_file, [key.dict() for key in keys])
    
    def get_sessions(self) -> List[Session]:
        """Get all sessions from storage."""
        data = self._load_json(self.sessions_file)
        if data is None:
            return []
        return [Session(**session_data) for session_data in data]
    
    def save_sessions(self, sessions: List[Session]):
        """Save sessions to storage."""
        self._save_json(self.sessions_file, [session.dict() for session in sessions])
    
    def get_sae_registry(self) -> List[SAERegistry]:
        """Get SAE registry from storage."""
        data = self._load_json(self.sae_registry_file)
        if data is None:
            return []
        return [SAERegistry(**sae_data) for sae_data in data]
    
    def save_sae_registry(self, sae_registry: List[SAERegistry]):
        """Save SAE registry to storage."""
        self._save_json(self.sae_registry_file, [sae.dict() for sae in sae_registry])
    
    def get_storage_data(self) -> StorageData:
        """Get complete storage data."""
        return StorageData(
            keys=self.get_keys(),
            sessions=self.get_sessions(),
            sae_registry=self.get_sae_registry(),
            key_pool=self.get_key_pool()
        )
    
    def save_storage_data(self, data: StorageData):
        """Save complete storage data."""
        self.save_keys(data.keys)
        self.save_sessions(data.sessions)
        self.save_sae_registry(data.sae_registry)
        self.update_key_pool(data.key_pool) 
