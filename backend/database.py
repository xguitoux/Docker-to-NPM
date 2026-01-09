from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class Service(Base):
    """Service model for tracking deployed services"""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, unique=True, index=True)
    subdomain = Column(String, unique=True)
    docker_image = Column(String)
    container_id = Column(String, unique=True)
    network_name = Column(String)
    subnet = Column(String)
    internal_port = Column(Integer)
    npm_proxy_host_id = Column(Integer)
    dns_record_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")


class Subnet(Base):
    """Subnet model for tracking subnet allocation"""
    __tablename__ = "subnets"

    id = Column(Integer, primary_key=True, index=True)
    subnet = Column(String, unique=True, index=True)
    service_name = Column(String)
    in_use = Column(Boolean, default=True)
    allocated_at = Column(DateTime, default=datetime.utcnow)


class NPMConfig(Base):
    """NPM configuration stored in database"""
    __tablename__ = "npm_config"

    id = Column(Integer, primary_key=True, index=True)
    npm_url = Column(String, nullable=False)
    npm_email = Column(String, nullable=False)
    npm_password = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DNSConfig(Base):
    """DNS configuration stored in database"""
    __tablename__ = "dns_config"

    id = Column(Integer, primary_key=True, index=True)
    dns_provider = Column(String, nullable=False, default="ovh")  # "ovh" or "cloudflare"

    # OVH fields
    ovh_endpoint = Column(String, default="ovh-eu")
    ovh_application_key = Column(String, default="")
    ovh_application_secret = Column(String, default="")
    ovh_consumer_key = Column(String, default="")
    ovh_zone_name = Column(String, default="")

    # Cloudflare fields
    cloudflare_api_token = Column(String, default="")
    cloudflare_zone_id = Column(String, default="")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

    # Initialize default configurations from .env if they don't exist
    db = SessionLocal()
    try:
        # Check if NPM config exists
        npm_config = db.query(NPMConfig).first()
        if not npm_config:
            # Create default NPM config from .env
            npm_config = NPMConfig(
                npm_url=settings.npm_url,
                npm_email=settings.npm_email,
                npm_password=settings.npm_password
            )
            db.add(npm_config)

        # Check if DNS config exists
        dns_config = db.query(DNSConfig).first()
        if not dns_config:
            # Create default DNS config from .env
            dns_config = DNSConfig(
                dns_provider=settings.dns_provider,
                ovh_endpoint=settings.ovh_endpoint,
                ovh_application_key=settings.ovh_application_key,
                ovh_application_secret=settings.ovh_application_secret,
                ovh_consumer_key=settings.ovh_consumer_key,
                ovh_zone_name=settings.ovh_zone_name,
                cloudflare_api_token=settings.cloudflare_api_token,
                cloudflare_zone_id=settings.cloudflare_zone_id
            )
            db.add(dns_config)

        db.commit()
    finally:
        db.close()


def get_npm_config():
    """Get NPM configuration from database"""
    db = SessionLocal()
    try:
        config = db.query(NPMConfig).first()
        if not config:
            # Fallback to settings if not in DB
            return {
                'npm_url': settings.npm_url,
                'npm_email': settings.npm_email,
                'npm_password': settings.npm_password
            }
        return {
            'npm_url': config.npm_url,
            'npm_email': config.npm_email,
            'npm_password': config.npm_password
        }
    finally:
        db.close()


def get_dns_config():
    """Get DNS configuration from database"""
    db = SessionLocal()
    try:
        config = db.query(DNSConfig).first()
        if not config:
            # Fallback to settings if not in DB
            return {
                'dns_provider': settings.dns_provider,
                'ovh_endpoint': settings.ovh_endpoint,
                'ovh_application_key': settings.ovh_application_key,
                'ovh_application_secret': settings.ovh_application_secret,
                'ovh_consumer_key': settings.ovh_consumer_key,
                'ovh_zone_name': settings.ovh_zone_name,
                'cloudflare_api_token': settings.cloudflare_api_token,
                'cloudflare_zone_id': settings.cloudflare_zone_id
            }
        return {
            'dns_provider': config.dns_provider,
            'ovh_endpoint': config.ovh_endpoint,
            'ovh_application_key': config.ovh_application_key,
            'ovh_application_secret': config.ovh_application_secret,
            'ovh_consumer_key': config.ovh_consumer_key,
            'ovh_zone_name': config.ovh_zone_name,
            'cloudflare_api_token': config.cloudflare_api_token,
            'cloudflare_zone_id': config.cloudflare_zone_id
        }
    finally:
        db.close()
