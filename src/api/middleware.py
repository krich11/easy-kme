"""
Authentication middleware for Easy-KMS server.
"""

from fastapi import Request, HTTPException, Depends
from typing import Optional
import logging

from ..services.auth_service import AuthService

logger = logging.getLogger(__name__)


def get_client_certificate(request: Request) -> Optional[bytes]:
    """Extract client certificate from request."""
    # In a real implementation, this would extract the client certificate
    # from the SSL context. For now, we'll use a placeholder.
    # This needs to be implemented based on the specific ASGI server being used.
    
    # For Uvicorn with SSL, the certificate should be available in the scope
    client_cert = request.scope.get("client_cert")
    return client_cert


def authenticate_client(request: Request) -> str:
    """Authenticate client and return SAE ID."""
    auth_service = AuthService()
    
    # Get client certificate
    client_cert = get_client_certificate(request)
    
    if not client_cert:
        raise HTTPException(status_code=401, detail="Client certificate required")
    
    # Authenticate client
    is_authenticated, sae_id = auth_service.authenticate_client(client_cert)
    
    if not is_authenticated:
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    # Store SAE ID in request state for later use
    request.state.sae_id = sae_id
    return sae_id


def get_sae_id(request: Request) -> str:
    """Get SAE ID from request state."""
    return request.state.sae_id 