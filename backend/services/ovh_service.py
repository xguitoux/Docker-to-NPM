import ovh
from typing import Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import settings


class OVHService:
    """Service for OVH DNS API operations"""

    def __init__(self):
        self.client = ovh.Client(
            endpoint=settings.ovh_endpoint,
            application_key=settings.ovh_application_key,
            application_secret=settings.ovh_application_secret,
            consumer_key=settings.ovh_consumer_key
        )
        self.zone_name = settings.ovh_zone_name
        self.last_error: Optional[str] = None

    def create_a_record(
        self,
        subdomain: str,
        target_ip: str,
        ttl: int = 3600
    ) -> Optional[int]:
        """
        Create an A record in OVH DNS

        Args:
            subdomain: Subdomain name (without the main domain)
            target_ip: Target IP address
            ttl: Time to live in seconds

        Returns:
            Record ID or None if failed
        """
        try:
            # Create the DNS record
            result = self.client.post(
                f'/domain/zone/{self.zone_name}/record',
                fieldType='A',
                subDomain=subdomain,
                target=target_ip,
                ttl=ttl
            )

            # Refresh the zone to apply changes
            self.client.post(f'/domain/zone/{self.zone_name}/refresh')

            return result.get('id')

        except Exception as e:
            print(f"Error creating DNS record: {e}")
            return None

    def create_cname_record(
        self,
        subdomain: str,
        target: str,
        ttl: int = 3600
    ) -> Optional[int]:
        """
        Create a CNAME record in OVH DNS

        Args:
            subdomain: Subdomain name (without the main domain)
            target: Target domain (e.g., "guitou.eu" or "@" for the zone)
            ttl: Time to live in seconds

        Returns:
            Record ID or None if failed
        """
        try:
            # If target is "@", use the zone name
            if target == "@":
                target = f"{self.zone_name}."
            # Ensure target ends with a dot for CNAME
            elif not target.endswith('.'):
                target = f"{target}."

            # Create the CNAME record
            result = self.client.post(
                f'/domain/zone/{self.zone_name}/record',
                fieldType='CNAME',
                subDomain=subdomain,
                target=target,
                ttl=ttl
            )

            # Refresh the zone to apply changes
            self.client.post(f'/domain/zone/{self.zone_name}/refresh')

            return result.get('id')

        except Exception as e:
            print(f"Error creating CNAME record: {e}")
            return None

    def get_records(self, subdomain: Optional[str] = None) -> list:
        """
        Get DNS records

        Args:
            subdomain: Filter by subdomain (optional)

        Returns:
            List of record IDs
        """
        try:
            params = {'fieldType': 'A'}
            if subdomain:
                params['subDomain'] = subdomain

            record_ids = self.client.get(
                f'/domain/zone/{self.zone_name}/record',
                **params
            )
            return record_ids

        except Exception as e:
            print(f"Error getting DNS records: {e}")
            return []

    def get_record_details(self, record_id: int) -> Optional[dict]:
        """Get details of a specific DNS record"""
        try:
            return self.client.get(
                f'/domain/zone/{self.zone_name}/record/{record_id}'
            )
        except Exception as e:
            print(f"Error getting record details: {e}")
            return None

    def delete_record(self, record_id: int) -> bool:
        """
        Delete a DNS record

        Args:
            record_id: ID of the record to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete(
                f'/domain/zone/{self.zone_name}/record/{record_id}'
            )

            # Refresh the zone to apply changes
            self.client.post(f'/domain/zone/{self.zone_name}/refresh')

            return True

        except Exception as e:
            print(f"Error deleting DNS record: {e}")
            return False

    def health_check(self) -> bool:
        """Check if OVH API is accessible"""
        try:
            self.client.get('/me')
            self.last_error = None
            return True
        except Exception as e:
            self.last_error = f"OVH API error: {str(e)}"
            return False
