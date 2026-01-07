import ipaddress
from typing import Optional, Set
from sqlalchemy.orm import Session
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import Subnet


class SubnetManager:
    """Manages subnet allocation for Docker networks"""

    def __init__(self, pool: str, subnet_size: int):
        """
        Initialize subnet manager

        Args:
            pool: CIDR notation of the subnet pool (e.g., "172.20.0.0/16")
            subnet_size: Size of subnets to allocate (e.g., 24 for /24)
        """
        self.pool = ipaddress.IPv4Network(pool)
        self.subnet_size = subnet_size

    def get_available_subnets(self, db: Session) -> Set[str]:
        """Get all used subnets from database"""
        used_subnets = db.query(Subnet.subnet).filter(Subnet.in_use == True).all()
        return {subnet[0] for subnet in used_subnets}

    def allocate_subnet(self, db: Session, service_name: str) -> Optional[str]:
        """
        Allocate a new subnet for a service

        Args:
            db: Database session
            service_name: Name of the service requesting the subnet

        Returns:
            Subnet in CIDR notation or None if no subnets available
        """
        used_subnets = self.get_available_subnets(db)

        # Generate all possible subnets from the pool
        for subnet in self.pool.subnets(new_prefix=self.subnet_size):
            subnet_str = str(subnet)
            if subnet_str not in used_subnets:
                # Allocate this subnet
                new_subnet = Subnet(
                    subnet=subnet_str,
                    service_name=service_name,
                    in_use=True
                )
                db.add(new_subnet)
                db.commit()
                return subnet_str

        return None

    def release_subnet(self, db: Session, subnet: str) -> bool:
        """
        Release a subnet back to the pool

        Args:
            db: Database session
            subnet: Subnet to release in CIDR notation

        Returns:
            True if released, False if not found
        """
        subnet_record = db.query(Subnet).filter(Subnet.subnet == subnet).first()
        if subnet_record:
            subnet_record.in_use = False
            db.commit()
            return True
        return False

    def get_gateway_ip(self, subnet: str) -> str:
        """Get the gateway IP for a subnet (first usable IP)"""
        network = ipaddress.IPv4Network(subnet)
        return str(list(network.hosts())[0])

    def get_container_ip(self, subnet: str) -> str:
        """Get the container IP for a subnet (second usable IP)"""
        network = ipaddress.IPv4Network(subnet)
        return str(list(network.hosts())[1])
