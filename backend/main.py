from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from config import settings
from database import get_db, init_db, Service, get_npm_config, get_dns_config, NPMConfig, DNSConfig, SessionLocal
from models import (
    ServiceCreateRequest,
    ServiceCreateResponse,
    ServiceInfo,
    HealthResponse,
    DNSProxyCreateRequest,
    DNSProxyCreateResponse,
    NPMConfigResponse,
    NPMConfigUpdateRequest,
    ConfigUpdateResponse,
    DNSConfigResponse,
    DNSConfigUpdateRequest
)
from services import (
    DockerService,
    SubnetManager
)

# Initialize FastAPI app
app = FastAPI(
    title="Docker Orchestrator API",
    description="API for managing Docker containers with NPM and DNS (OVH/Cloudflare)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize infrastructure services (these don't change)
docker_service = DockerService()
subnet_manager = SubnetManager(settings.subnet_pool, settings.subnet_size)


def get_npm_service():
    """Get NPM service with current database configuration"""
    from services import NPMService
    config = get_npm_config()

    # Create a custom NPM service with database config
    service = NPMService()
    service.base_url = config['npm_url'].rstrip('/')
    service.email = config['npm_email']
    service.password = config['npm_password']
    service.token = None  # Force re-authentication with new creds

    return service


def get_ovh_service():
    """Get OVH service with current database configuration"""
    import ovh
    from services import OVHService
    config = get_dns_config()

    # Create OVH service with database config
    service = OVHService()
    service.client = ovh.Client(
        endpoint=config['ovh_endpoint'],
        application_key=config['ovh_application_key'],
        application_secret=config['ovh_application_secret'],
        consumer_key=config['ovh_consumer_key']
    )
    service.zone_name = config['ovh_zone_name']

    return service


def get_cloudflare_service():
    """Get Cloudflare service with current database configuration"""
    from services.cloudflare_service import CloudflareService
    config = get_dns_config()

    # Create Cloudflare service with database config
    service = CloudflareService()
    service.api_token = config['cloudflare_api_token']
    service.zone_id = config['cloudflare_zone_id']

    return service


def get_dns_service():
    """Get the configured DNS service (OVH or Cloudflare) from database"""
    config = get_dns_config()

    if config['dns_provider'].lower() == "cloudflare":
        return get_cloudflare_service()
    else:
        return get_ovh_service()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
async def root():
    """Root endpoint - redirects to documentation"""
    return {
        "message": "Docker Orchestrator API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health",
        "frontend": "Please access the frontend at http://localhost:8080"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    docker_ok = docker_service.health_check()
    npm_service = get_npm_service()
    npm_ok = npm_service.health_check()
    dns_service = get_dns_service()
    dns_ok = dns_service.health_check()

    return HealthResponse(
        status="healthy" if (docker_ok and npm_ok and dns_ok) else "degraded",
        docker=docker_ok,
        npm=npm_ok,
        ovh=dns_ok,
        docker_error=docker_service.last_error if not docker_ok else None,
        npm_error=npm_service.last_error if not npm_ok else None,
        ovh_error=dns_service.last_error if not dns_ok else None
    )


@app.get("/api/dns/records")
async def get_dns_records():
    """Get all DNS records from configured DNS provider"""
    try:
        all_records = []
        zone_name = ""

        # Get DNS config and determine provider
        dns_config = get_dns_config()

        if dns_config['dns_provider'].lower() == "cloudflare":
            # Get Cloudflare service with current DB config
            cloudflare_service = get_cloudflare_service()

            # Get records from Cloudflare
            records = cloudflare_service.get_records()
            zone_info = cloudflare_service._get_zone_info()
            zone_name = zone_info.get('name') if zone_info else dns_config['cloudflare_zone_id']

            for record in records:
                # Extract subdomain from full name
                full_name = record.get('name', '')
                if full_name.endswith(f".{zone_name}"):
                    subdomain = full_name[:-len(f".{zone_name}")]
                elif full_name == zone_name:
                    subdomain = "@"
                else:
                    subdomain = full_name

                all_records.append({
                    "id": record.get('id'),
                    "type": record.get('type'),
                    "subdomain": subdomain,
                    "target": record.get('content'),
                    "ttl": record.get('ttl'),
                    "zone": zone_name
                })

            # Also get CNAME records
            try:
                import requests
                response = requests.get(
                    f"{cloudflare_service.base_url}/zones/{cloudflare_service.zone_id}/dns_records",
                    headers=cloudflare_service._get_headers(),
                    params={'type': 'CNAME'},
                    timeout=10
                )
                if response.ok:
                    data = response.json()
                    if data.get('success'):
                        for record in data.get('result', []):
                            full_name = record.get('name', '')
                            if full_name.endswith(f".{zone_name}"):
                                subdomain = full_name[:-len(f".{zone_name}")]
                            elif full_name == zone_name:
                                subdomain = "@"
                            else:
                                subdomain = full_name

                            all_records.append({
                                "id": record.get('id'),
                                "type": record.get('type'),
                                "subdomain": subdomain,
                                "target": record.get('content'),
                                "ttl": record.get('ttl'),
                                "zone": zone_name
                            })
            except:
                pass

        else:
            # Get OVH service with current DB config
            ovh_service = get_ovh_service()
            zone_name = dns_config['ovh_zone_name']

            # Get A records
            a_record_ids = ovh_service.get_records()
            for record_id in a_record_ids:
                record = ovh_service.get_record_details(record_id)
                if record:
                    all_records.append({
                        "id": record_id,
                        "type": "A",
                        "subdomain": record.get("subDomain") or "@",
                        "target": record.get("target"),
                        "ttl": record.get("ttl"),
                        "zone": record.get("zone")
                    })

            # Get CNAME records
            try:
                cname_ids = ovh_service.client.get(
                    f'/domain/zone/{dns_config["ovh_zone_name"]}/record',
                    fieldType='CNAME'
                )
                for record_id in cname_ids:
                    record = ovh_service.get_record_details(record_id)
                    if record:
                        all_records.append({
                            "id": record_id,
                            "type": "CNAME",
                            "subdomain": record.get("subDomain") or "@",
                            "target": record.get("target"),
                            "ttl": record.get("ttl"),
                            "zone": record.get("zone")
                        })
            except:
                pass

        return {
            "success": True,
            "zone": zone_name,
            "count": len(all_records),
            "records": all_records
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "records": []
        }


@app.post("/api/dns-proxy", response_model=DNSProxyCreateResponse)
async def create_dns_proxy(request: DNSProxyCreateRequest):
    """
    Create DNS record + NPM proxy host (without Docker container)
    """
    errors = []
    dns_record_id = None
    npm_proxy_host_id = None

    # Get DNS service based on configured provider
    dns_service = get_dns_service()

    # Get DNS config and zone name based on provider
    dns_config = get_dns_config()
    if dns_config['dns_provider'].lower() == "cloudflare":
        cloudflare_service = get_cloudflare_service()
        zone_info = cloudflare_service._get_zone_info()
        zone_name = zone_info.get('name') if zone_info else dns_config['cloudflare_zone_id']
    else:
        zone_name = dns_config['ovh_zone_name']

    full_domain = f"{request.subdomain}.{zone_name}"

    try:
        # Step 1: Create DNS CNAME record (if requested)
        if request.create_dns:
            try:
                dns_record_id = dns_service.create_cname_record(
                    subdomain=request.subdomain,
                    target=request.cname_target,
                    ttl=request.ttl
                )
                if not dns_record_id:
                    raise Exception("DNS record creation returned no ID")
            except Exception as e:
                errors.append(f"DNS record creation failed: {str(e)}")
        else:
            # Skip DNS creation
            dns_record_id = None

        # Step 2: Create NPM proxy host
        try:
            npm_service = get_npm_service()
            npm_proxy_host_id = npm_service.create_proxy_host(
                domain_name=full_domain,
                forward_host=request.target_host,
                forward_port=request.target_port,
                enable_ssl=request.enable_ssl
            )
            if not npm_proxy_host_id:
                raise Exception("NPM proxy host creation returned no ID")
        except Exception as e:
            errors.append(f"NPM proxy host creation failed: {str(e)}")

        # Generate appropriate message
        if request.create_dns:
            success_message = "DNS + NPM Host created successfully"
            warning_message = "Created with warnings"
        else:
            success_message = "NPM Host created successfully (DNS skipped)"
            warning_message = "NPM Host created with warnings (DNS skipped)"

        return DNSProxyCreateResponse(
            success=len(errors) == 0,
            subdomain=request.subdomain,
            full_domain=full_domain,
            dns_record_id=dns_record_id,
            npm_proxy_host_id=npm_proxy_host_id,
            message=success_message if not errors else warning_message,
            errors=errors if errors else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/npm/hosts")
async def get_npm_hosts():
    """Get all NPM proxy hosts"""
    try:
        npm_service = get_npm_service()
        hosts = npm_service.get_proxy_hosts()
        return {
            "success": True,
            "count": len(hosts),
            "hosts": hosts
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "hosts": []
        }


@app.post("/api/services", response_model=ServiceCreateResponse)
async def create_service(
    request: ServiceCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new service with Docker container, NPM proxy, and OVH DNS
    """
    errors = []
    container_id = None
    network_name = None
    npm_proxy_host_id = None
    dns_record_id = None
    subnet = None

    try:
        # Check if service already exists
        existing = db.query(Service).filter(
            Service.service_name == request.service_name
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Service '{request.service_name}' already exists"
            )

        # Step 1: Allocate subnet
        subnet = subnet_manager.allocate_subnet(db, request.service_name)
        if not subnet:
            raise HTTPException(
                status_code=500,
                detail="No available subnets"
            )

        # Step 2: Create Docker network
        network_name = f"{request.service_name}-network"
        try:
            docker_service.create_network(network_name, subnet)
        except Exception as e:
            errors.append(f"Docker network creation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

        # Step 3: Create Docker container
        try:
            container = docker_service.create_container(
                name=request.service_name,
                image=request.docker_image,
                network=network_name,
                internal_port=request.internal_port,
                environment=request.environment_vars,
                volumes=request.volumes
            )
            container_id = container.id

            # Get container IP
            container_ip = docker_service.get_container_ip(container_id, network_name)
            if not container_ip:
                raise Exception("Could not retrieve container IP")

        except Exception as e:
            errors.append(f"Docker container creation failed: {str(e)}")
            # Cleanup network
            if network_name:
                docker_service.remove_network(network_name)
            raise HTTPException(status_code=500, detail=str(e))

        # Step 4: Create DNS record
        dns_config = get_dns_config()
        dns_service = get_dns_service()

        # Get zone name based on provider
        if dns_config['dns_provider'].lower() == "cloudflare":
            cloudflare_service = get_cloudflare_service()
            zone_info = cloudflare_service._get_zone_info()
            zone_name = zone_info.get('name') if zone_info else dns_config['cloudflare_zone_id']
        else:
            zone_name = dns_config['ovh_zone_name']

        subdomain = f"{request.service_name}.{zone_name}"
        try:
            dns_record_id = dns_service.create_a_record(
                subdomain=request.service_name,
                target_ip=settings.server_public_ip
            )
            if not dns_record_id:
                raise Exception("DNS record creation returned no ID")
        except Exception as e:
            errors.append(f"DNS record creation failed: {str(e)}")
            # Continue anyway, we can create DNS later

        # Step 5: Create NPM proxy host
        try:
            npm_service = get_npm_service()
            npm_proxy_host_id = npm_service.create_proxy_host(
                domain_name=subdomain,
                forward_host=container_ip,
                forward_port=request.internal_port,
                enable_ssl=request.enable_ssl
            )
            if not npm_proxy_host_id:
                raise Exception("NPM proxy host creation returned no ID")
        except Exception as e:
            errors.append(f"NPM proxy host creation failed: {str(e)}")
            # Continue anyway

        # Step 6: Save to database
        service = Service(
            service_name=request.service_name,
            subdomain=subdomain,
            docker_image=request.docker_image,
            container_id=container_id,
            network_name=network_name,
            subnet=subnet,
            internal_port=request.internal_port,
            npm_proxy_host_id=npm_proxy_host_id,
            dns_record_id=dns_record_id,
            status="active" if not errors else "partial"
        )
        db.add(service)
        db.commit()

        return ServiceCreateResponse(
            success=len(errors) == 0,
            service_name=request.service_name,
            subdomain=subdomain,
            container_id=container_id,
            network_name=network_name,
            npm_proxy_host_id=npm_proxy_host_id,
            dns_record_id=dns_record_id,
            message="Service created successfully" if not errors else "Service created with warnings",
            errors=errors if errors else None
        )

    except HTTPException:
        raise
    except Exception as e:
        # Cleanup on failure
        if container_id:
            docker_service.stop_and_remove_container(container_id)
        if network_name:
            docker_service.remove_network(network_name)
        if subnet:
            subnet_manager.release_subnet(db, subnet)

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services", response_model=List[ServiceInfo])
async def list_services(db: Session = Depends(get_db)):
    """List all services"""
    services = db.query(Service).all()
    return [
        ServiceInfo(
            id=s.id,
            service_name=s.service_name,
            subdomain=s.subdomain,
            docker_image=s.docker_image,
            container_id=s.container_id,
            network_name=s.network_name,
            subnet=s.subnet,
            internal_port=s.internal_port,
            npm_proxy_host_id=s.npm_proxy_host_id,
            dns_record_id=s.dns_record_id,
            created_at=s.created_at.isoformat(),
            status=s.status
        )
        for s in services
    ]


@app.delete("/api/services/{service_name}")
async def delete_service(service_name: str, db: Session = Depends(get_db)):
    """Delete a service and cleanup all resources"""
    service = db.query(Service).filter(
        Service.service_name == service_name
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    errors = []

    # Cleanup Docker container
    if service.container_id:
        if not docker_service.stop_and_remove_container(service.container_id):
            errors.append("Failed to remove Docker container")

    # Cleanup Docker network
    if service.network_name:
        if not docker_service.remove_network(service.network_name):
            errors.append("Failed to remove Docker network")

    # Cleanup NPM proxy host
    if service.npm_proxy_host_id:
        npm_service = get_npm_service()
        if not npm_service.delete_proxy_host(service.npm_proxy_host_id):
            errors.append("Failed to remove NPM proxy host")

    # Cleanup DNS record
    if service.dns_record_id:
        dns_service = get_dns_service()
        if not dns_service.delete_record(service.dns_record_id):
            errors.append("Failed to remove DNS record")

    # Release subnet
    if service.subnet:
        subnet_manager.release_subnet(db, service.subnet)

    # Delete from database
    db.delete(service)
    db.commit()

    return {
        "success": len(errors) == 0,
        "message": "Service deleted" if not errors else "Service deleted with warnings",
        "errors": errors if errors else None
    }


@app.delete("/api/dns/records/{record_id}")
async def delete_dns_record(record_id: str):
    """Delete a DNS record from configured DNS provider"""
    try:
        dns_service = get_dns_service()
        dns_config = get_dns_config()

        # For OVH, convert to int
        if dns_config['dns_provider'].lower() == "ovh":
            record_id = int(record_id)

        success = dns_service.delete_record(record_id)
        if success:
            return {
                "success": True,
                "message": f"DNS record {record_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete DNS record"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/npm/hosts/{proxy_host_id}")
async def delete_npm_host(proxy_host_id: int):
    """Delete an NPM proxy host"""
    try:
        npm_service = get_npm_service()
        success = npm_service.delete_proxy_host(proxy_host_id)
        if success:
            return {
                "success": True,
                "message": f"NPM proxy host {proxy_host_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete NPM proxy host"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/npm-config", response_model=NPMConfigResponse)
async def get_npm_config_endpoint():
    """Get current NPM configuration (password masked)"""
    config = get_npm_config()
    return NPMConfigResponse(
        npm_url=config['npm_url'],
        npm_email=config['npm_email'],
        npm_password_masked="*" * 12
    )


@app.put("/api/admin/npm-config", response_model=ConfigUpdateResponse)
async def update_npm_config(config: NPMConfigUpdateRequest):
    """Update NPM configuration in database"""
    db = SessionLocal()
    try:
        # Get or create NPM config
        npm_config = db.query(NPMConfig).first()
        if not npm_config:
            npm_config = NPMConfig()
            db.add(npm_config)

        # Update configuration
        npm_config.npm_url = config.npm_url
        npm_config.npm_email = config.npm_email

        # Only update password if new one provided
        if config.npm_password:
            npm_config.npm_password = config.npm_password

        db.commit()

        return ConfigUpdateResponse(
            success=True,
            message="NPM configuration updated successfully.",
            requires_restart=False
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")
    finally:
        db.close()


@app.get("/api/admin/dns-config", response_model=DNSConfigResponse)
async def get_dns_config_endpoint():
    """Get current DNS configuration (secrets masked)"""
    def mask_secret(value: str) -> str:
        if not value or len(value) == 0:
            return ""
        return "*" * 12

    config = get_dns_config()

    return DNSConfigResponse(
        dns_provider=config['dns_provider'],
        ovh_endpoint=config['ovh_endpoint'],
        ovh_application_key=config['ovh_application_key'],
        ovh_application_key_masked=mask_secret(config['ovh_application_key']),
        ovh_application_secret_masked=mask_secret(config['ovh_application_secret']),
        ovh_consumer_key_masked=mask_secret(config['ovh_consumer_key']),
        ovh_zone_name=config['ovh_zone_name'],
        cloudflare_api_token_masked=mask_secret(config['cloudflare_api_token']),
        cloudflare_zone_id=config['cloudflare_zone_id']
    )


@app.put("/api/admin/dns-config", response_model=ConfigUpdateResponse)
async def update_dns_config(config: DNSConfigUpdateRequest):
    """Update DNS configuration in database"""
    db = SessionLocal()
    try:
        # Get or create DNS config
        dns_config = db.query(DNSConfig).first()
        if not dns_config:
            dns_config = DNSConfig()
            db.add(dns_config)

        # Update DNS provider
        dns_config.dns_provider = config.dns_provider

        # Update OVH fields (only if provided)
        if config.ovh_endpoint is not None:
            dns_config.ovh_endpoint = config.ovh_endpoint
        if config.ovh_application_key is not None:
            dns_config.ovh_application_key = config.ovh_application_key
        if config.ovh_application_secret is not None:
            dns_config.ovh_application_secret = config.ovh_application_secret
        if config.ovh_consumer_key is not None:
            dns_config.ovh_consumer_key = config.ovh_consumer_key
        if config.ovh_zone_name is not None:
            dns_config.ovh_zone_name = config.ovh_zone_name

        # Update Cloudflare fields (only if provided)
        if config.cloudflare_api_token is not None:
            dns_config.cloudflare_api_token = config.cloudflare_api_token
        if config.cloudflare_zone_id is not None:
            dns_config.cloudflare_zone_id = config.cloudflare_zone_id

        db.commit()

        return ConfigUpdateResponse(
            success=True,
            message=f"DNS configuration updated successfully. Now using {config.dns_provider.upper()} provider.",
            requires_restart=False
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update DNS configuration: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
