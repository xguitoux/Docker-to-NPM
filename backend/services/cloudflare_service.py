import requests
from typing import Optional, List, Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import settings


class CloudflareService:
    """Service for Cloudflare DNS API operations"""

    def __init__(self):
        self.api_token = settings.cloudflare_api_token
        self.zone_id = settings.cloudflare_zone_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.last_error: Optional[str] = None

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def create_a_record(
        self,
        subdomain: str,
        target_ip: str,
        ttl: int = 3600,
        proxied: bool = False
    ) -> Optional[str]:
        """
        Create an A record in Cloudflare DNS

        Args:
            subdomain: Subdomain name (without the main domain)
            target_ip: Target IP address
            ttl: Time to live in seconds (1 = automatic)
            proxied: Whether to proxy through Cloudflare

        Returns:
            Record ID or None if failed
        """
        try:
            # Get zone name first
            zone_info = self._get_zone_info()
            if not zone_info:
                return None

            zone_name = zone_info.get('name')
            full_name = f"{subdomain}.{zone_name}" if subdomain else zone_name

            payload = {
                "type": "A",
                "name": full_name,
                "content": target_ip,
                "ttl": ttl,
                "proxied": proxied
            }

            response = requests.post(
                f"{self.base_url}/zones/{self.zone_id}/dns_records",
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                return data['result'].get('id')
            else:
                print(f"Cloudflare API error: {data.get('errors')}")
                return None

        except Exception as e:
            print(f"Error creating DNS record: {e}")
            self.last_error = str(e)
            return None

    def create_cname_record(
        self,
        subdomain: str,
        target: str,
        ttl: int = 3600,
        proxied: bool = False
    ) -> Optional[str]:
        """
        Create a CNAME record in Cloudflare DNS

        Args:
            subdomain: Subdomain name (without the main domain)
            target: Target domain (e.g., "example.com" or "@" for the zone)
            ttl: Time to live in seconds (1 = automatic)
            proxied: Whether to proxy through Cloudflare

        Returns:
            Record ID or None if failed
        """
        try:
            # Get zone name first
            zone_info = self._get_zone_info()
            if not zone_info:
                return None

            zone_name = zone_info.get('name')
            full_name = f"{subdomain}.{zone_name}" if subdomain else zone_name

            # If target is "@", use the zone name
            if target == "@":
                target = zone_name

            # Cloudflare doesn't require trailing dot for CNAME
            target = target.rstrip('.')

            payload = {
                "type": "CNAME",
                "name": full_name,
                "content": target,
                "ttl": ttl,
                "proxied": proxied
            }

            response = requests.post(
                f"{self.base_url}/zones/{self.zone_id}/dns_records",
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                return data['result'].get('id')
            else:
                print(f"Cloudflare API error: {data.get('errors')}")
                return None

        except Exception as e:
            print(f"Error creating CNAME record: {e}")
            self.last_error = str(e)
            return None

    def _get_zone_info(self) -> Optional[Dict]:
        """Get zone information"""
        try:
            response = requests.get(
                f"{self.base_url}/zones/{self.zone_id}",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                return data['result']
            return None

        except Exception as e:
            print(f"Error getting zone info: {e}")
            return None

    def get_records(self, subdomain: Optional[str] = None) -> List[Dict]:
        """
        Get DNS records

        Args:
            subdomain: Filter by subdomain (optional)

        Returns:
            List of record dictionaries
        """
        try:
            params = {'type': 'A'}
            if subdomain:
                zone_info = self._get_zone_info()
                if zone_info:
                    zone_name = zone_info.get('name')
                    params['name'] = f"{subdomain}.{zone_name}"

            response = requests.get(
                f"{self.base_url}/zones/{self.zone_id}/dns_records",
                headers=self._get_headers(),
                params=params,
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                return data['result']
            return []

        except Exception as e:
            print(f"Error getting DNS records: {e}")
            return []

    def get_record_details(self, record_id: str) -> Optional[Dict]:
        """Get details of a specific DNS record"""
        try:
            response = requests.get(
                f"{self.base_url}/zones/{self.zone_id}/dns_records/{record_id}",
                headers=self._get_headers(),
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                return data['result']
            return None

        except Exception as e:
            print(f"Error getting record details: {e}")
            return None

    def delete_record(self, record_id: str) -> bool:
        """
        Delete a DNS record

        Args:
            record_id: ID of the record to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.base_url}/zones/{self.zone_id}/dns_records/{record_id}",
                headers=self._get_headers(),
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            return data.get('success', False)

        except Exception as e:
            print(f"Error deleting DNS record: {e}")
            self.last_error = str(e)
            return False

    def health_check(self) -> bool:
        """Check if Cloudflare API is accessible"""
        try:
            response = requests.get(
                f"{self.base_url}/zones/{self.zone_id}",
                headers=self._get_headers(),
                timeout=5
            )
            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                self.last_error = None
                return True
            else:
                self.last_error = f"Cloudflare API error: {data.get('errors')}"
                return False

        except Exception as e:
            self.last_error = f"Cloudflare API error: {str(e)}"
            return False
