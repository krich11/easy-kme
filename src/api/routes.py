"""
API routes for Easy-KMS server implementing ETSI GS QKD 014 specification.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List
import logging

from ..models.api_models import (
    KeyRequest, KeyContainer, KeyIDs, StatusResponse, ErrorResponse
)
from ..services.key_service import KeyService
from ..services.auth_service import AuthService
from .middleware import authenticate_client, get_sae_id

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/keys", tags=["KME API"])

# Initialize services
key_service = KeyService()
auth_service = AuthService()


@router.get("/status", response_model=StatusResponse)
async def get_status(request: Request):
    """
    Get KME status (ETSI GS QKD 014 Get status API).
    
    Returns operational status and key pool information.
    """
    try:
        # Authenticate client
        sae_id = authenticate_client(request)
        
        # Get status information
        status_data = key_service.get_status()
        
        return StatusResponse(
            status=status_data["status"],
            kme_id=status_data["kme_id"],
            version=status_data["version"],
            key_pool_size=status_data["key_pool_size"],
            max_key_pool_size=status_data["max_key_pool_size"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_status: {e}")
        raise HTTPException(status_code=503, detail="Internal server error")


@router.post("/{slave_sae_id}/enc_keys", response_model=KeyContainer)
async def get_key(
    slave_sae_id: str,
    key_request: KeyRequest,
    request: Request
):
    """
    Get keys for master SAE (ETSI GS QKD 014 Get key API).
    
    Args:
        slave_sae_id: URL-encoded SAE ID of slave SAE
        key_request: Key request parameters
        request: FastAPI request object
    
    Returns:
        KeyContainer with requested keys
    """
    try:
        # Authenticate client
        master_sae_id = authenticate_client(request)
        
        # Validate slave SAE ID
        if not slave_sae_id:
            raise HTTPException(status_code=400, detail="Slave SAE ID is required")
        
        # Get keys for master SAE
        key_container = key_service.get_keys_for_master_sae(
            master_sae_id=master_sae_id,
            slave_sae_id=slave_sae_id,
            key_request=key_request
        )
        
        if not key_container:
            raise HTTPException(status_code=503, detail="Failed to generate keys")
        
        return key_container
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_key: {e}")
        raise HTTPException(status_code=503, detail="Internal server error")


@router.post("/{master_sae_id}/dec_keys", response_model=KeyContainer)
async def get_key_with_key_ids(
    master_sae_id: str,
    key_ids: KeyIDs,
    request: Request
):
    """
    Get keys for slave SAE (ETSI GS QKD 014 Get key with key IDs API).
    
    Args:
        master_sae_id: URL-encoded SAE ID of master SAE
        key_ids: Key IDs to retrieve
        request: FastAPI request object
    
    Returns:
        KeyContainer with requested keys
    """
    try:
        # Authenticate client
        slave_sae_id = authenticate_client(request)
        
        # Validate master SAE ID
        if not master_sae_id:
            raise HTTPException(status_code=400, detail="Master SAE ID is required")
        
        # Validate key IDs
        if not key_ids.key_ids:
            raise HTTPException(status_code=400, detail="Key IDs are required")
        
        # Check authorization
        if not auth_service.is_sae_authorized(slave_sae_id, key_ids.key_ids):
            raise HTTPException(status_code=401, detail="Not authorized for requested keys")
        
        # Get keys for slave SAE
        key_container = key_service.get_keys_for_slave_sae(
            slave_sae_id=slave_sae_id,
            master_sae_id=master_sae_id,
            key_ids=key_ids.key_ids
        )
        
        if not key_container:
            raise HTTPException(status_code=503, detail="Failed to retrieve keys")
        
        return key_container
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_key_with_key_ids: {e}")
        raise HTTPException(status_code=503, detail="Internal server error")


# Error handlers
@router.exception_handler(400)
async def bad_request_handler(request: Request, exc: HTTPException):
    """Handle bad request errors."""
    return ErrorResponse(
        error_code=400,
        error_message="Bad request format",
        details=str(exc.detail)
    )


@router.exception_handler(401)
async def unauthorized_handler(request: Request, exc: HTTPException):
    """Handle unauthorized errors."""
    return ErrorResponse(
        error_code=401,
        error_message="Unauthorized",
        details=str(exc.detail)
    )


@router.exception_handler(503)
async def server_error_handler(request: Request, exc: HTTPException):
    """Handle server errors."""
    return ErrorResponse(
        error_code=503,
        error_message="Error on server side",
        details=str(exc.detail)
    ) 