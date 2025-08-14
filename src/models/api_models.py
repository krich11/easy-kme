"""
API request and response models for ETSI GS QKD 014 KME server.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class KeyRequest(BaseModel):
    """Internal key request model (snake_case)."""
    number: Optional[int] = Field(default=1, ge=1, description="Number of keys requested")
    size: Optional[int] = Field(default=256, ge=8, description="Key size in bits")
    additional_slave_sae_ids: Optional[List[str]] = Field(default=None)


class KeyRequestSpec(BaseModel):
    """ETSI 014 Key request model (field names per spec)."""
    number: Optional[int] = Field(default=None)
    size: Optional[int] = Field(default=None)
    additional_slave_SAE_IDs: Optional[List[str]] = Field(default=None)
    extension_mandatory: Optional[List[dict]] = Field(default=None)
    extension_optional: Optional[List[dict]] = Field(default=None)


class Key(BaseModel):
    """Internal individual key model."""
    key_id: str
    key_material: str
    key_size: int


class CertificateExtension(BaseModel):
    """Certificate information extension for API responses (vendor-specific)."""
    client_verified: str = Field(..., description="Certificate verification status from nginx")
    client_dn: str = Field(..., description="Client certificate Distinguished Name")
    client_issuer: str = Field(..., description="Certificate issuer Distinguished Name")
    ssl_protocol: str = Field(..., description="SSL/TLS protocol version used")
    ssl_cipher: str = Field(..., description="SSL/TLS cipher suite used")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the request")
    sae_id: str = Field(..., description="Extracted SAE ID from certificate DN")


class SpecKey(BaseModel):
    """ETSI 014 key object."""
    key_ID: str = Field(..., description="Unique key identifier (UUID)")
    key: str = Field(..., description="Base64-encoded key material")
    key_ID_extension: Optional[dict] = Field(default=None)
    key_extension: Optional[dict] = Field(default=None)


class KeyContainer(BaseModel):
    """Internal response container (legacy)."""
    keys: List[Key]
    key_number: int
    key_size: int


class SpecKeyContainer(BaseModel):
    """ETSI 014 key container."""
    keys: List[SpecKey]
    key_container_extension: Optional[dict] = Field(default=None)
    easy_kme_certificate_extension: Optional[CertificateExtension] = Field(default=None, description="Easy-KME vendor-specific certificate information")


class KeyID(BaseModel):
    """Internal single key ID."""
    key_id: str


class KeyIDs(BaseModel):
    """Internal key IDs list (legacy)."""
    key_ids: List[str]


class KeyIDRef(BaseModel):
    """ETSI 014 key ID reference object."""
    key_ID: str


class KeyIDsSpec(BaseModel):
    """ETSI 014 Key IDs request model."""
    key_IDs: List[KeyIDRef]


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error_code: int = Field(..., description="HTTP error code")
    error_message: str = Field(..., description="Error description")
    details: Optional[str] = Field(default=None, description="Additional error details")
    easy_kme_certificate_extension: Optional[CertificateExtension] = Field(default=None, description="Easy-KME vendor-specific certificate information if available")


class StatusResponse(BaseModel):
    """Legacy status response."""
    status: str
    kme_id: str
    version: str = "1.0.0"
    key_pool_size: int
    max_key_pool_size: int


class StatusSpec(BaseModel):
    """ETSI 014 Status data format."""
    source_KME_ID: str
    target_KME_ID: str
    master_SAE_ID: str
    slave_SAE_ID: str
    key_size: int
    stored_key_count: int
    max_key_count: int
    max_key_per_request: int
    max_key_size: int
    min_key_size: int
    max_SAE_ID_count: int
    status_extension: Optional[dict] = None
    easy_kme_certificate_extension: Optional[CertificateExtension] = Field(default=None, description="Easy-KME vendor-specific certificate information")
