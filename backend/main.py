from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from config import settings
from database import get_db, init_db, Service
from models import (
    ServiceCreateRequest,
    ServiceCreateResponse,
    ServiceInfo,
    HealthResponse,
    DNSProxyCreateRequest,
    DNSProxyCreateResponse
)
from services import (
    DockerService,
    NPMService,
    OVHService,
    SubnetManager
)

# Initialize FastAPI app
app = FastAPI(
    title="Docker Orchestrator API",
    description="API for managing Docker containers with NPM and OVH DNS",
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

# Initialize services
docker_service = DockerService()
npm_service = NPMService()
ovh_service = OVHService()
subnet_manager = SubnetManager(settings.subnet_pool, settings.subnet_size)


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
    npm_ok = npm_service.health_check()
    ovh_ok = ovh_service.health_check()

    return HealthResponse(
        status="healthy" if (docker_ok and npm_ok and ovh_ok) else "degraded",
        docker=docker_ok,
        npm=npm_ok,
        ovh=ovh_ok,
        docker_error=docker_service.last_error if not docker_ok else None,
        npm_error=npm_service.last_error if not npm_ok else None,
        ovh_error=ovh_service.last_error if not ovh_ok else None
    )


@app.get("/api/dns/records")
async def get_dns_records():
    """Get all DNS records from OVH"""
    try:
        # Get all record types
        all_records = []

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
                f'/domain/zone/{settings.ovh_zone_name}/record',
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
            "zone": settings.ovh_zone_name,
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
    full_domain = f"{request.subdomain}.{settings.ovh_zone_name}"

    try:
        # Step 1: Create OVH DNS CNAME record (if requested)
        if request.create_dns:
            try:
                dns_record_id = ovh_service.create_cname_record(
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

        # Step 4: Create OVH DNS record
        subdomain = f"{request.service_name}.{settings.ovh_zone_name}"
        try:
            dns_record_id = ovh_service.create_a_record(
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
        if not npm_service.delete_proxy_host(service.npm_proxy_host_id):
            errors.append("Failed to remove NPM proxy host")

    # Cleanup OVH DNS record
    if service.dns_record_id:
        if not ovh_service.delete_record(service.dns_record_id):
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
