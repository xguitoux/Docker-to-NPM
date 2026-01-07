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
