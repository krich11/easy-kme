"""
API routes for Easy-KME server implementing ETSI GS QKD 014 specification.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List, Optional
import logging

from ..models.api_models import (
    KeyRequest,
    KeyRequestSpec,
    KeyContainer,
    SpecKey,
    SpecKeyContainer,
    KeyIDs,
    KeyIDRef,
    KeyIDsSpec,
    StatusResponse,
    StatusSpec,
    ErrorResponse,
)
from ..services.key_service import KeyService
from ..services.auth_service import AuthService
from . import middleware

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/keys", tags=["KME API"])

# Initialize services
key_service = KeyService()
auth_service = AuthService()


@router.get("/{slave_sae_id}/status", response_model=StatusSpec)
async def get_status(slave_sae_id: str, request: Request):
    """
    Get KME status (ETSI GS QKD 014 Get status API).
    
    Returns operational status and key pool information.
    """
    try:
        # Authenticate client
        master_sae_id = middleware.authenticate_client(request)
        
        # Get status information
        status_data = key_service.get_status(master_sae_id=master_sae_id, slave_sae_id=slave_sae_id)
        settings = key_service.settings

        available_keys = status_data.get("available_keys", 0)

        # Create certificate extension (if enabled)
        cert_extension = None
        if settings.include_certificate_extension:
            cert_extension = middleware.create_certificate_extension(request, master_sae_id)

        return StatusSpec(
            source_KME_ID=settings.kme_id,
            target_KME_ID=settings.kme_id,
            master_SAE_ID=master_sae_id,
            slave_SAE_ID=slave_sae_id,
            key_size=settings.key_size,
            stored_key_count=available_keys,
            max_key_count=status_data.get("max_key_pool_size", settings.key_pool_size),
            max_key_per_request=settings.max_key_per_request,
            max_key_size=settings.key_max_size,
            min_key_size=settings.key_min_size,
            max_SAE_ID_count=settings.max_sae_id_count,
            easy_kme_certificate_extension=cert_extension
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_status: {e}")
        raise HTTPException(status_code=503, detail="Internal server error")


@router.post("/{slave_sae_id}/enc_keys", response_model=SpecKeyContainer)
async def get_key(
    slave_sae_id: str,
    key_request: KeyRequestSpec,
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
        master_sae_id = middleware.authenticate_client(request)
        
        # Log the incoming request for debugging
        logger.debug(f"=== ENC_KEYS REQUEST VALIDATION ===")
        logger.debug(f"Request body: {key_request.dict()}")
        logger.debug(f"Request fields: {list(key_request.dict().keys())}")
        logger.debug(f"Request JSON payload: {key_request.model_dump_json(indent=2)}")
        
        # Validate that required ETSI fields are present (ETSI spec says these are optional with defaults)
        # We'll use defaults if not provided, but we should validate the values if they are provided
        if key_request.number is not None and key_request.number < 1:
            raise HTTPException(status_code=400, detail="ETSI GS QKD 014: 'number' must be >= 1")
        
        if key_request.size is not None and key_request.size < 8:
            raise HTTPException(status_code=400, detail="ETSI GS QKD 014: 'size' must be >= 8")
        
        # Validate that no non-ETSI fields are present
        allowed_fields = {'number', 'size', 'additional_slave_SAE_IDs', 'extension_mandatory', 'extension_optional'}
        received_fields = set(key_request.dict().keys())
        invalid_fields = received_fields - allowed_fields
        
        if invalid_fields:
            logger.warning(f"Invalid fields in request: {invalid_fields}")
            raise HTTPException(
                status_code=400, 
                detail=f"ETSI GS QKD 014: Invalid fields detected: {list(invalid_fields)}. "
                       f"Valid fields are: {list(allowed_fields)}"
            )
        
        # Validate slave SAE ID
        if not slave_sae_id:
            raise HTTPException(status_code=400, detail="Slave SAE ID is required")
        
        # Validate key size is multiple of 8 (ETSI requirement)
        if key_request.size is not None and key_request.size % 8 != 0:
            raise HTTPException(status_code=400, detail="size shall be a multiple of 8")
        
        # Handle extension_mandatory (ETSI requirement)
        if key_request.extension_mandatory:
            # For now, we don't support any mandatory extensions
            # In a real implementation, you would check against supported extensions
            raise HTTPException(
                status_code=400, 
                detail="not all extension_mandatory parameters are supported"
            )
        
        # Handle extension_optional (ETSI requirement)
        # We can ignore these for now, but in a real implementation you might process them
        if key_request.extension_optional:
            logger.info(f"Ignoring extension_optional parameters: {key_request.extension_optional}")
        
        # Map spec request to internal model
        internal_request = KeyRequest(
            number=key_request.number or 1,
            size=key_request.size or key_service.settings.key_size,
            additional_slave_sae_ids=(key_request.additional_slave_SAE_IDs or None),
        )

        # Get keys for master SAE
        key_container = key_service.get_keys_for_master_sae(
            master_sae_id=master_sae_id,
            slave_sae_id=slave_sae_id,
            key_request=internal_request
        )
        
        if not key_container:
            raise HTTPException(status_code=503, detail="Failed to generate keys")
        
        # Create certificate extension (if enabled)
        cert_extension = None
        if key_service.settings.include_certificate_extension:
            cert_extension = middleware.create_certificate_extension(request, master_sae_id)
        
        # Map internal response to spec container
        spec_keys = [SpecKey(key_ID=k.key_id, key=k.key_material) for k in key_container.keys]
        return SpecKeyContainer(keys=spec_keys, easy_kme_certificate_extension=cert_extension)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_key: {e}")
        raise HTTPException(status_code=503, detail="Internal server error")


@router.post("/{master_sae_id}/dec_keys", response_model=SpecKeyContainer)
async def get_key_with_key_ids(
    master_sae_id: str,
    key_ids: KeyIDsSpec,
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
        slave_sae_id = middleware.authenticate_client(request)
        
        # Log the incoming request for debugging
        logger.debug(f"=== DEC_KEYS REQUEST VALIDATION ===")
        logger.debug(f"Request body: {key_ids.dict()}")
        logger.debug(f"Request fields: {list(key_ids.dict().keys())}")
        logger.debug(f"Request JSON payload: {key_ids.model_dump_json(indent=2)}")
        
        # Validate master SAE ID
        if not master_sae_id:
            raise HTTPException(status_code=400, detail="Master SAE ID is required")
        
        # Validate key IDs
        if not key_ids.key_IDs:
            logger.warning(f"Empty key_IDs array in request: {key_ids.dict()}")
            raise HTTPException(status_code=400, detail="Key IDs are required")
        
        # Validate key ID structure
        for i, key_ref in enumerate(key_ids.key_IDs):
            if not key_ref.key_ID:
                logger.warning(f"Empty key_ID at index {i} in request: {key_ids.dict()}")
                raise HTTPException(status_code=400, detail=f"Key ID at index {i} is empty")
        
        # Check authorization
        key_id_list = [ref.key_ID for ref in key_ids.key_IDs]
        if not auth_service.is_slave_authorized_for_keys(slave_sae_id=slave_sae_id, key_ids=key_id_list, master_sae_id=master_sae_id):
            raise HTTPException(status_code=401, detail="Not authorized for requested keys")
        
        # Get keys for slave SAE
        key_container = key_service.get_keys_for_slave_sae(
            slave_sae_id=slave_sae_id,
            master_sae_id=master_sae_id,
            key_ids=key_id_list
        )
        
        if not key_container:
            raise HTTPException(status_code=503, detail="Failed to retrieve keys")
        
        # Create certificate extension (if enabled)
        cert_extension = None
        if key_service.settings.include_certificate_extension:
            cert_extension = middleware.create_certificate_extension(request, slave_sae_id)
        
        spec_keys = [SpecKey(key_ID=k.key_id, key=k.key_material) for k in key_container.keys]
        return SpecKeyContainer(keys=spec_keys, easy_kme_certificate_extension=cert_extension)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_key_with_key_ids: {e}")
        raise HTTPException(status_code=503, detail="Internal server error")


@router.get("/{slave_sae_id}/enc_keys", response_model=SpecKeyContainer)
async def get_key_get(slave_sae_id: str, request: Request, number: Optional[int] = None, size: Optional[int] = None):
    """GET variant for simple cases: number and/or size query params."""
    try:
        master_sae_id = middleware.authenticate_client(request)
        
        # Log the incoming request for debugging
        logger.debug(f"=== ENC_KEYS GET REQUEST VALIDATION ===")
        logger.debug(f"Query parameters: number={number}, size={size}")
        
        # Validate that required ETSI fields are present (for GET, we use defaults if not provided)
        # This is less strict than POST since GET is meant for simple cases
        if number is not None and number < 1:
            raise HTTPException(status_code=400, detail="ETSI GS QKD 014: 'number' must be >= 1")
        
        if size is not None and size < 8:
            raise HTTPException(status_code=400, detail="ETSI GS QKD 014: 'size' must be >= 8")
        
        # Validate key size is multiple of 8 (ETSI requirement)
        if size is not None and size % 8 != 0:
            raise HTTPException(status_code=400, detail="size shall be a multiple of 8")
        
        internal_request = KeyRequest(
            number=number or 1,
            size=size or key_service.settings.key_size,
        )
        key_container = key_service.get_keys_for_master_sae(
            master_sae_id=master_sae_id,
            slave_sae_id=slave_sae_id,
            key_request=internal_request,
        )
        if not key_container:
            raise HTTPException(status_code=503, detail="Failed to generate keys")
        
        # Create certificate extension (if enabled)
        cert_extension = None
        if key_service.settings.include_certificate_extension:
            cert_extension = middleware.create_certificate_extension(request, master_sae_id)
        
        spec_keys = [SpecKey(key_ID=k.key_id, key=k.key_material) for k in key_container.keys]
        return SpecKeyContainer(keys=spec_keys, easy_kme_certificate_extension=cert_extension)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_key_get: {e}")
        raise HTTPException(status_code=503, detail="Internal server error")


@router.get("/{master_sae_id}/dec_keys", response_model=SpecKeyContainer)
async def get_key_with_key_ids_get(master_sae_id: str, request: Request, key_ID: Optional[str] = None):
    """GET variant for simple case: single key_ID query param."""
    try:
        slave_sae_id = middleware.authenticate_client(request)
        if not key_ID:
            raise HTTPException(status_code=400, detail="key_ID is required for GET")
        if not auth_service.is_slave_authorized_for_keys(slave_sae_id=slave_sae_id, key_ids=[key_ID], master_sae_id=master_sae_id):
            raise HTTPException(status_code=401, detail="Not authorized for requested keys")
        key_container = key_service.get_keys_for_slave_sae(
            slave_sae_id=slave_sae_id,
            master_sae_id=master_sae_id,
            key_ids=[key_ID],
        )
        if not key_container:
            raise HTTPException(status_code=503, detail="Failed to retrieve keys")
        
        # Create certificate extension (if enabled)
        cert_extension = None
        if key_service.settings.include_certificate_extension:
            cert_extension = middleware.create_certificate_extension(request, slave_sae_id)
        
        spec_keys = [SpecKey(key_ID=k.key_id, key=k.key_material) for k in key_container.keys]
        return SpecKeyContainer(keys=spec_keys, easy_kme_certificate_extension=cert_extension)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_key_with_key_ids_get: {e}")
        raise HTTPException(status_code=503, detail="Internal server error")


# Note: Router-level exception handlers are not supported in FastAPI
