import requests
from typing import Optional, Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import settings


class NPMService:
    """Service for Nginx Proxy Manager API operations"""

    def __init__(self):
        self.base_url = settings.npm_url.rstrip('/')
        self.email = settings.npm_email
        self.password = settings.npm_password
        self.token: Optional[str] = None
        self.last_error: Optional[str] = None

    def authenticate(self) -> bool:
        """Authenticate with NPM and get access token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/tokens",
                json={
                    "identity": self.email,
                    "secret": self.password
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get("token")
            self.last_error = None
            return self.token is not None
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            self.last_error = f"Auth failed - {error_msg}"
            print(f"NPM authentication error: {self.last_error}")
            return False
        except Exception as e:
            self.last_error = f"Auth error: {str(e)}"
            print(f"NPM authentication error: {self.last_error}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        if not self.token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def create_proxy_host(
        self,
        domain_name: str,
        forward_host: str,
        forward_port: int,
        enable_ssl: bool = True
    ) -> Optional[int]:
        """
        Create a proxy host in NPM

        Args:
            domain_name: Full domain name (e.g., app.example.com)
            forward_host: IP address of the container
            forward_port: Port of the container
            enable_ssl: Whether to enable SSL with Let's Encrypt

        Returns:
            Proxy host ID or None if failed
        """
        try:
            payload = {
                "domain_names": [domain_name],
                "forward_host": forward_host,
                "forward_port": forward_port,
                "forward_scheme": "http",
                "access_list_id": 0,
                "certificate_id": 0,
                "ssl_forced": False,
                "caching_enabled": False,
                "block_exploits": True,
                "advanced_config": "",
                "meta": {
                    "letsencrypt_agree": False,
                    "dns_challenge": False
                },
                "allow_websocket_upgrade": True,
                "http2_support": True,
                "hsts_enabled": False,
                "hsts_subdomains": False
            }

            # If SSL is enabled, configure Let's Encrypt
            if enable_ssl:
                payload["ssl_forced"] = True
                payload["meta"]["letsencrypt_agree"] = True
                payload["meta"]["letsencrypt_email"] = self.email
                payload["certificate_id"] = "new"

            response = requests.post(
                f"{self.base_url}/api/nginx/proxy-hosts",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("id")

        except Exception as e:
            print(f"Error creating proxy host: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return None

    def get_proxy_hosts(self) -> list:
        """Get all proxy hosts"""
        try:
            response = requests.get(
                f"{self.base_url}/api/nginx/proxy-hosts",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting proxy hosts: {e}")
            return []

    def delete_proxy_host(self, proxy_host_id: int) -> bool:
        """Delete a proxy host"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/nginx/proxy-hosts/{proxy_host_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error deleting proxy host: {e}")
            return False

    def health_check(self) -> bool:
        """Check if NPM is accessible and can authenticate"""
        try:
            # First check if NPM is responding
            response = requests.get(f"{self.base_url}/api/schema", timeout=5)
            if response.status_code != 200:
                self.last_error = f"NPM not responding (status {response.status_code})"
                return False

            # Then try to authenticate
            return self.authenticate()
        except requests.exceptions.Timeout:
            self.last_error = f"Connection timeout to {self.base_url}"
            return False
        except requests.exceptions.ConnectionError:
            self.last_error = f"Cannot connect to {self.base_url}"
            return False
        except Exception as e:
            self.last_error = f"Error: {str(e)}"
            return False
