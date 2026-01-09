from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class ServiceCreateRequest(BaseModel):
    """Request model for creating a new service"""
    service_name: str = Field(..., description="Name of the service (used for subdomain)")
    docker_image: str = Field(..., description="Docker image to use")
    internal_port: int = Field(..., description="Internal port of the container")
    environment_vars: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")
    volumes: Optional[List[str]] = Field(default=None, description="Volume mounts")
    enable_ssl: bool = Field(default=True, description="Enable SSL via Let's Encrypt")


class ServiceCreateResponse(BaseModel):
    """Response model for service creation"""
    success: bool
    service_name: str
    subdomain: str
    container_id: Optional[str] = None
    network_name: Optional[str] = None
    npm_proxy_host_id: Optional[int] = None
    dns_record_id: Optional[int] = None
    message: str
    errors: Optional[List[str]] = None


class ServiceInfo(BaseModel):
    """Model for service information"""
    id: int
    service_name: str
    subdomain: str
    docker_image: str
    container_id: str
    network_name: str
    subnet: str
    internal_port: int
    npm_proxy_host_id: int
    dns_record_id: int
    created_at: str
    status: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    docker: bool
    npm: bool
    ovh: bool
    docker_error: Optional[str] = None
    npm_error: Optional[str] = None
    ovh_error: Optional[str] = None


class DNSProxyCreateRequest(BaseModel):
    """Request model for creating DNS + NPM host without Docker"""
    subdomain: str = Field(..., description="Subdomain name")
    create_dns: bool = Field(default=True, description="Create DNS CNAME record")
    cname_target: str = Field(default="@", description="CNAME target (@ for zone root)")
    ttl: int = Field(default=3600, description="TTL in seconds (default 3600 = 1 hour)")
    target_host: str = Field(..., description="Target host/IP for NPM")
    target_port: int = Field(..., description="Target port")
    enable_ssl: bool = Field(default=True, description="Enable SSL via Let's Encrypt")


class DNSProxyCreateResponse(BaseModel):
    """Response model for DNS + NPM creation"""
    success: bool
    subdomain: str
    full_domain: str
    dns_record_id: Optional[int] = None
    npm_proxy_host_id: Optional[int] = None
    message: str
    errors: Optional[List[str]] = None


class NPMConfigResponse(BaseModel):
    """Response model for NPM configuration"""
    npm_url: str
    npm_email: str
    npm_password_masked: str


class NPMConfigUpdateRequest(BaseModel):
    """Request model for updating NPM configuration"""
    npm_url: str = Field(..., description="NPM API URL")
    npm_email: str = Field(..., description="NPM admin email")
    npm_password: Optional[str] = Field(default=None, description="NPM admin password (leave empty to keep current)")


class ConfigUpdateResponse(BaseModel):
    """Response model for configuration update"""
    success: bool
    message: str
    requires_restart: bool = True


class DNSConfigResponse(BaseModel):
    """Response model for DNS configuration"""
    dns_provider: str
    ovh_endpoint: str
    ovh_application_key: str
    ovh_application_key_masked: str
    ovh_application_secret_masked: str
    ovh_consumer_key_masked: str
    ovh_zone_name: str
    cloudflare_api_token_masked: str
    cloudflare_zone_id: str


class DNSConfigUpdateRequest(BaseModel):
    """Request model for updating DNS configuration"""
    dns_provider: str = Field(..., description="DNS provider: 'ovh' or 'cloudflare'")

    # OVH fields (optional if using Cloudflare)
    ovh_endpoint: Optional[str] = Field(default=None, description="OVH API endpoint")
    ovh_application_key: Optional[str] = Field(default=None, description="OVH application key")
    ovh_application_secret: Optional[str] = Field(default=None, description="OVH application secret")
    ovh_consumer_key: Optional[str] = Field(default=None, description="OVH consumer key")
    ovh_zone_name: Optional[str] = Field(default=None, description="OVH zone name")

    # Cloudflare fields (optional if using OVH)
    cloudflare_api_token: Optional[str] = Field(default=None, description="Cloudflare API token")
    cloudflare_zone_id: Optional[str] = Field(default=None, description="Cloudflare zone ID")
