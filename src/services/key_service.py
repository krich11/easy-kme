"""
Key service for Easy-KME server.
Handles key generation, management, and distribution.
"""

import secrets
import base64
import uuid
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from ..config import get_settings
from ..models.data_models import Key, Session, KeyPool
from ..models.api_models import KeyRequest, KeyContainer, Key as APIKey
from .storage_service import StorageService

logger = logging.getLogger(__name__)


class KeyService:
    """Key management service for KME operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.storage_service = StorageService()
    
    def generate_key(self, key_size: int = 256) -> Tuple[str, str]:
        """Generate a cryptographically secure random key."""
        # Generate random bytes
        key_bytes = secrets.token_bytes(key_size // 8)
        
        # Generate unique key ID
        key_id = str(uuid.uuid4())
        
        # Encode key material as base64
        key_material = base64.b64encode(key_bytes).decode('utf-8')
        
        return key_id, key_material
    
    def generate_keys(self, number: int, key_size: int) -> List[Key]:
        """Generate multiple keys."""
        keys = []
        for _ in range(number):
            key_id, key_material = self.generate_key(key_size)
            key = Key(
                key_id=key_id,
                key_material=key_material,
                key_size=key_size
            )
            keys.append(key)
        return keys
    
    def refill_key_pool(self) -> bool:
        """Refill the key pool if it's below threshold."""
        try:
            key_pool = self.storage_service.get_key_pool()
            
            if key_pool.current_size >= key_pool.refill_threshold:
                return True  # Pool is sufficiently full
            
            # Calculate how many keys to generate
            keys_to_generate = key_pool.max_size - key_pool.current_size
            
            # Generate new keys
            new_keys = self.generate_keys(keys_to_generate, key_pool.key_size)
            
            # Get existing keys
            existing_keys = self.storage_service.get_keys()
            
            # Add new keys
            all_keys = existing_keys + new_keys
            
            # Update key pool
            key_pool.current_size = len(all_keys)
            key_pool.last_refill = datetime.utcnow()
            
            # Save to storage
            self.storage_service.save_keys(all_keys)
            self.storage_service.update_key_pool(key_pool)
            
            logger.info(f"Refilled key pool with {len(new_keys)} keys")
            return True
            
        except Exception as e:
            logger.error(f"Error refilling key pool: {e}")
            return False
    
    def get_keys_for_master_sae(self, master_sae_id: str, slave_sae_id: str, 
                                key_request: KeyRequest) -> Optional[KeyContainer]:
        """Get keys for master SAE (Get key API)."""
        try:
            # Validate request (lab: strict input acceptance per ETSI simple rules)
            if key_request.size is not None and key_request.size % 8 != 0:
                logger.error("size shall be a multiple of 8")
                return None
            if key_request.number is not None and key_request.number > self.settings.max_key_per_request:
                logger.error("number exceeds max_key_per_request")
                return None
            if key_request.size is not None and (key_request.size < self.settings.key_min_size or key_request.size > self.settings.key_max_size):
                logger.error("size outside allowed bounds")
                return None
            if key_request.additional_slave_sae_ids and len(key_request.additional_slave_sae_ids) > self.settings.max_sae_id_count:
                logger.error("additional_slave_SAE_IDs exceeds max_SAE_ID_count")
                return None

            # Ensure key pool is sufficiently full
            self.refill_key_pool()
            
            # Get available keys
            all_keys = self.storage_service.get_keys()
            available_keys = [k for k in all_keys if not k.is_used and not k.master_sae_id]
            
            if len(available_keys) < key_request.number:
                logger.error(f"Insufficient keys available. Requested: {key_request.number}, Available: {len(available_keys)}")
                return None
            
            # Select keys for this request
            selected_keys = available_keys[: key_request.number or 1]
            
            # Mark keys as used and assign to master SAE
            for key in selected_keys:
                key.is_used = True
                key.master_sae_id = master_sae_id
                key.slave_sae_ids = [slave_sae_id]
                
                # Add additional slave SAEs if specified
                if key_request.additional_slave_sae_ids:
                    key.slave_sae_ids.extend(key_request.additional_slave_sae_ids)
            
            # Create session
            session = Session(
                session_id=str(uuid.uuid4()),
                master_sae_id=master_sae_id,
                slave_sae_ids=[slave_sae_id] + (key_request.additional_slave_sae_ids or []),
                key_ids=[k.key_id for k in selected_keys]
            )
            
            # Save updated data
            self.storage_service.save_keys(all_keys)
            
            sessions = self.storage_service.get_sessions()
            sessions.append(session)
            self.storage_service.save_sessions(sessions)
            
            # Create API response
            api_keys = [
                APIKey(
                    key_id=key.key_id,
                    key_material=key.key_material,
                    key_size=key.key_size
                )
                for key in selected_keys
            ]
            
            key_container = KeyContainer(
                keys=api_keys,
                key_number=len(api_keys),
                key_size=key_request.size or self.settings.key_size
            )
            
            logger.info(f"Generated {len(selected_keys)} keys for master SAE {master_sae_id}")
            return key_container
            
        except Exception as e:
            logger.error(f"Error getting keys for master SAE {master_sae_id}: {e}")
            return None
    
    def get_keys_for_slave_sae(self, slave_sae_id: str, master_sae_id: str, 
                               key_ids: List[str]) -> Optional[KeyContainer]:
        """Get keys for slave SAE (Get key with key IDs API)."""
        try:
            # Get all keys
            all_keys = self.storage_service.get_keys()
            
            # Find requested keys
            requested_keys = []
            for key_id in key_ids:
                key = next((k for k in all_keys if k.key_id == key_id), None)
                if not key:
                    logger.error(f"Key {key_id} not found")
                    return None
                
                # Verify slave SAE is authorized
                if slave_sae_id not in key.slave_sae_ids:
                    logger.error(f"Slave SAE {slave_sae_id} not authorized for key {key_id}")
                    return None
                
                # Verify master SAE matches
                if key.master_sae_id != master_sae_id:
                    logger.error(f"Key {key_id} does not belong to master SAE {master_sae_id}")
                    return None
                
                requested_keys.append(key)
            
            # Create API response
            api_keys = [
                APIKey(
                    key_id=key.key_id,
                    key_material=key.key_material,
                    key_size=key.key_size
                )
                for key in requested_keys
            ]
            
            key_container = KeyContainer(
                keys=api_keys,
                key_number=len(api_keys),
                key_size=requested_keys[0].key_size if requested_keys else 256
            )
            
            logger.info(f"Retrieved {len(requested_keys)} keys for slave SAE {slave_sae_id}")
            return key_container
            
        except Exception as e:
            logger.error(f"Error getting keys for slave SAE {slave_sae_id}: {e}")
            return None
    
    def get_status(self, master_sae_id: str | None = None, slave_sae_id: str | None = None) -> dict:
        """Get KME status information.

        Parameters are placeholders to align with ETSI 'Get status' semantics.
        """
        try:
            key_pool = self.storage_service.get_key_pool()
            keys = self.storage_service.get_keys()
            sessions = self.storage_service.get_sessions()
            sae_registry = self.storage_service.get_sae_registry()
            
            return {
                "status": "operational",
                "kme_id": self.settings.kme_id,
                "version": "1.0.0",
                "key_pool_size": key_pool.current_size,
                "max_key_pool_size": key_pool.max_size,
                "active_sessions": len([s for s in sessions if s.is_active]),
                "registered_saes": len([s for s in sae_registry if s.is_active]),
                "total_keys": len(keys),
                "available_keys": len([k for k in keys if not k.is_used])
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                "status": "error",
                "kme_id": self.settings.kme_id,
                "version": "1.0.0",
                "error": str(e)
            } 
