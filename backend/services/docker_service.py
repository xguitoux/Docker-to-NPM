import docker
from docker.types import IPAMConfig, IPAMPool
from typing import Optional, Dict, List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import settings


class DockerService:
    """Service for Docker operations"""

    def __init__(self):
        self.client = docker.DockerClient(base_url=settings.docker_host)
        self.last_error: Optional[str] = None

    def create_network(self, network_name: str, subnet: str) -> docker.models.networks.Network:
        """
        Create a Docker network with a specific subnet

        Args:
            network_name: Name of the network
            subnet: Subnet in CIDR notation

        Returns:
            Docker network object
        """
        ipam_pool = IPAMPool(subnet=subnet)
        ipam_config = IPAMConfig(pool_configs=[ipam_pool])

        network = self.client.networks.create(
            name=network_name,
            driver="bridge",
            ipam=ipam_config
        )
        return network

    def create_container(
        self,
        name: str,
        image: str,
        network: str,
        internal_port: int,
        environment: Optional[Dict[str, str]] = None,
        volumes: Optional[List[str]] = None
    ) -> docker.models.containers.Container:
        """
        Create and start a Docker container

        Args:
            name: Container name
            image: Docker image
            network: Network name to connect to
            internal_port: Internal port of the application
            environment: Environment variables
            volumes: Volume mounts

        Returns:
            Docker container object
        """
        # Pull image if not present
        try:
            self.client.images.get(image)
        except docker.errors.ImageNotFound:
            print(f"Pulling image {image}...")
            self.client.images.pull(image)

        # Prepare volumes
        volume_dict = {}
        if volumes:
            for vol in volumes:
                parts = vol.split(":")
                if len(parts) == 2:
                    volume_dict[parts[0]] = {"bind": parts[1], "mode": "rw"}

        # Create container
        container = self.client.containers.run(
            image=image,
            name=name,
            detach=True,
            network=network,
            environment=environment or {},
            volumes=volume_dict if volume_dict else None,
            restart_policy={"Name": "unless-stopped"}
        )

        return container

    def get_container_ip(self, container_id: str, network_name: str) -> Optional[str]:
        """Get the IP address of a container on a specific network"""
        try:
            container = self.client.containers.get(container_id)
            networks = container.attrs['NetworkSettings']['Networks']
            if network_name in networks:
                return networks[network_name]['IPAddress']
        except Exception as e:
            print(f"Error getting container IP: {e}")
        return None

    def stop_and_remove_container(self, container_id: str) -> bool:
        """Stop and remove a container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            return True
        except Exception as e:
            print(f"Error removing container: {e}")
            return False

    def remove_network(self, network_name: str) -> bool:
        """Remove a Docker network"""
        try:
            network = self.client.networks.get(network_name)
            network.remove()
            return True
        except Exception as e:
            print(f"Error removing network: {e}")
            return False

    def health_check(self) -> bool:
        """Check if Docker is accessible"""
        try:
            self.client.ping()
            self.last_error = None
            return True
        except Exception as e:
            self.last_error = f"Docker error: {str(e)}"
            return False
