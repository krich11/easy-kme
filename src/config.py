"""
Configuration management for Easy-KMS server.
Loads all settings from environment variables with validation.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # KME Server Configuration
    kme_host: str = "0.0.0.0"
    kme_port: int = 8443
    kme_id: str = "KME_LAB_001"
    
    # Certificate Configuration
    kme_cert_path: str = "./certs/kme_cert.pem"
    kme_key_path: str = "./certs/kme_key.pem"
    ca_cert_path: str = "./certs/ca_cert.pem"
    
    # Storage Configuration
    data_dir: str = "./data"
    key_pool_size: int = 1000
    key_size: int = 256
    
    # Security Settings
    require_client_cert: bool = True
    verify_ca: bool = True
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "./logs/kme.log"
    
    # API Configuration
    api_version: str = "v1"
    api_prefix: str = "/api"
    
    @validator('kme_cert_path', 'kme_key_path', 'ca_cert_path')
    def validate_cert_paths(cls, v):
        """Validate certificate file paths exist."""
        if not Path(v).exists():
            raise ValueError(f"Certificate file not found: {v}")
        return v
    
    @validator('data_dir')
    def validate_data_dir(cls, v):
        """Ensure data directory exists."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings 