"""
API request and response models for ETSI GS QKD 014 KME server.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class KeyRequest(BaseModel):
    """Key request data model for Get key API."""
    
    number: Optional[int] = Field(default=1, ge=1, le=100, description="Number of keys requested")
    size: Optional[int] = Field(default=256, ge=128, le=512, description="Key size in bits")
    additional_slave_sae_ids: Optional[List[str]] = Field(
        default=None, 
        description="Additional slave SAE IDs for multi-party key sharing"
    )


class Key(BaseModel):
    """Individual key data model."""
    
    key_id: str = Field(..., description="Unique key identifier")
    key_material: str = Field(..., description="Base64 encoded key material")
    key_size: int = Field(..., description="Key size in bits")


class KeyContainer(BaseModel):
    """Key container response model for Get key and Get key with key IDs APIs."""
    
    keys: List[Key] = Field(..., description="List of keys")
    key_number: int = Field(..., description="Number of keys in container")
    key_size: int = Field(..., description="Size of each key in bits")


class KeyID(BaseModel):
    """Individual key ID model."""
    
    key_id: str = Field(..., description="Unique key identifier")


class KeyIDs(BaseModel):
    """Key IDs request model for Get key with key IDs API."""
    
    key_ids: List[str] = Field(..., description="List of key IDs to retrieve")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error_code: int = Field(..., description="HTTP error code")
    error_message: str = Field(..., description="Error description")
    details: Optional[str] = Field(default=None, description="Additional error details")


class StatusResponse(BaseModel):
    """Status response model for Get status API."""
    
    status: str = Field(..., description="KME operational status")
    kme_id: str = Field(..., description="KME identifier")
    version: str = Field(default="1.0.0", description="API version")
    key_pool_size: int = Field(..., description="Current key pool size")
    max_key_pool_size: int = Field(..., description="Maximum key pool size") 