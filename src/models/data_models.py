"""
Internal data models for Easy-KMS server.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Key(BaseModel):
    """Internal key storage model."""
    
    key_id: str = Field(..., description="Unique key identifier")
    key_material: str = Field(..., description="Base64 encoded key material")
    key_size: int = Field(..., description="Key size in bits")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Key creation timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Key expiration timestamp")
    is_used: bool = Field(default=False, description="Whether key has been used")
    master_sae_id: Optional[str] = Field(default=None, description="Master SAE ID that requested this key")
    slave_sae_ids: List[str] = Field(default_factory=list, description="Slave SAE IDs authorized to use this key")


class Session(BaseModel):
    """Key distribution session model."""
    
    session_id: str = Field(..., description="Unique session identifier")
    master_sae_id: str = Field(..., description="Master SAE ID")
    slave_sae_ids: List[str] = Field(..., description="Slave SAE IDs")
    key_ids: List[str] = Field(..., description="Key IDs in this session")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Session expiration timestamp")
    is_active: bool = Field(default=True, description="Whether session is active")


class SAERegistry(BaseModel):
    """SAE registration model."""
    
    sae_id: str = Field(..., description="SAE identifier")
    certificate_subject: str = Field(..., description="Certificate subject DN")
    certificate_serial: str = Field(..., description="Certificate serial number")
    registered_at: datetime = Field(default_factory=datetime.utcnow, description="Registration timestamp")
    is_active: bool = Field(default=True, description="Whether SAE is active")
    last_seen: Optional[datetime] = Field(default=None, description="Last activity timestamp")


class KeyPool(BaseModel):
    """Key pool configuration and status."""
    
    current_size: int = Field(..., description="Current number of keys in pool")
    max_size: int = Field(..., description="Maximum pool size")
    key_size: int = Field(..., description="Default key size in bits")
    last_refill: Optional[datetime] = Field(default=None, description="Last pool refill timestamp")
    refill_threshold: int = Field(default=100, description="Threshold for pool refill")


class StorageData(BaseModel):
    """Complete storage data model."""
    
    keys: List[Key] = Field(default_factory=list, description="All keys in storage")
    sessions: List[Session] = Field(default_factory=list, description="Active sessions")
    sae_registry: List[SAERegistry] = Field(default_factory=list, description="Registered SAEs")
    key_pool: KeyPool = Field(..., description="Key pool status")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last storage update") 