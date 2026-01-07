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
