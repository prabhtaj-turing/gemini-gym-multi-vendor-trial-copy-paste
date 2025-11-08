"""
CES Infobot Configuration System

This module provides a configuration system for CES services that integrate with Infobot.
Each CES service gets its own configuration manager instance with service-specific settings.
"""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any


@dataclass
class CESInfobotConfig:
    """Configuration for a CES service's Infobot integration"""
    
    # GCP/Infobot Instance Settings
    gcp_project: str = "gbot-experimentation"
    location: str = "us-east1"
    app_id: str = "78151603-8f03-4385-9c2a-42a2431f04e0"
    api_version: str = "v1beta"
    api_endpoint: str = "https://autopush-ces-googleapis.sandbox.google.com"
    
    # Authentication
    service_account_info: str = ""  # Base64 encoded
    scopes: List[str] = field(default_factory=lambda: ["https://www.googleapis.com/auth/cloud-platform"])
    ca_bundle: str = "/etc/ssl/certs/ca-certificates.crt"
    
    # Service-specific tool resources
    tool_resources: Dict[str, str] = field(default_factory=dict)
    
    @property
    def parent_resource(self) -> str:
        """Generate parent resource string from config"""
        return f"projects/{self.gcp_project}/locations/{self.location}/apps/{self.app_id}"
    
    @property
    def full_api_endpoint(self) -> str:
        """Generate full API endpoint from config"""
        return f"{self.api_endpoint}/{self.api_version}/{self.parent_resource}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CESInfobotConfig':
        """Create config from dictionary"""
        return cls(**data)


class CESInfobotConfigManager:
    """Base configuration manager - each service gets its own instance"""
    
    def __init__(self, service_name: str, default_tool_resources: Optional[Dict[str, str]] = None):
        """Initialize configuration manager for a specific CES service
        
        Args:
            service_name: Name of the CES service (e.g., "ces_account_management")
            default_tool_resources: Default tool resource IDs for this service
        """
        self.service_name = service_name
        self.config_file = f"{service_name}_infobot_config.json"
        # Store the original default tool resources for reset functionality
        self._default_tool_resources = (default_tool_resources or {}).copy()
        self._config = CESInfobotConfig(
            tool_resources=self._default_tool_resources.copy()
        )
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or environment variables"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                self._config = CESInfobotConfig.from_dict(data)
                return
            except Exception as e:
                print(f"Warning: Could not load config from {self.config_file}: {e}")
        
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from service-specific environment variables"""
        prefix = f"{self.service_name.upper()}_INFOBOT_"
        
        env_mappings = {
            'gcp_project': f'{prefix}GCP_PROJECT',
            'location': f'{prefix}LOCATION',
            'app_id': f'{prefix}APP_ID',
            'api_version': f'{prefix}API_VERSION',
            'api_endpoint': f'{prefix}API_ENDPOINT',
            'service_account_info': f'{prefix}SERVICE_ACCOUNT_INFO',
        }
        
        for attr, env_var in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                setattr(self._config, attr, value)
    
    def get_config(self) -> CESInfobotConfig:
        """Get current configuration"""
        return self._config
    
    def update_config(self, **kwargs):
        """Update configuration values
        
        Args:
            **kwargs: Configuration key-value pairs to update
        """
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
    
    def save_config(self, filepath: Optional[str] = None):
        """Save configuration to file
        
        Args:
            filepath: Optional path to save config. Defaults to service-specific config file
        """
        save_path = filepath or self.config_file
        with open(save_path, 'w') as f:
            json.dump(self._config.to_dict(), f, indent=2)
        print(f"Configuration saved to {save_path}")
    
    def load_config(self, filepath: str):
        """Load configuration from file
        
        Args:
            filepath: Path to configuration file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        self._config = CESInfobotConfig.from_dict(data)
        print(f"Configuration loaded from {filepath}")
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self._config = CESInfobotConfig(tool_resources=self._default_tool_resources.copy())
        print("Configuration reset to defaults")
    
    def show_config(self):
        """Display current configuration"""
        print(f"{self.service_name} Infobot Configuration:")
        print(json.dumps(self._config.to_dict(), indent=2))

