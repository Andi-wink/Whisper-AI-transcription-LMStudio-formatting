"""
HubSpot CRM Integration
=======================
Client for HubSpot CRM operations - contacts, properties, etc.
"""

import aiohttp
import logging

logger = logging.getLogger("hubspot-integration")


class HubSpotClient:
    """Async HubSpot CRM client for contact operations with connection pooling."""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.hubapi.com/crm/v3/objects/contacts"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self._session: aiohttp.ClientSession | None = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a reusable session for connection pooling."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.headers)
        return self._session
    
    async def close(self):
        """Close the session when done."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def get_contact_by_email(self, email: str) -> dict | None:
        """Search for a contact by email."""
        url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
        payload = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email
                }]
            }],
            "properties": ["email", "firstname", "lastname", "city", "country", "zip", "address", "registration_plate", "policy_info"]
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["total"] > 0:
                        return data["results"][0]
                else:
                    logger.error(f"Error searching contact: {await response.text()}")
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error searching contact: {e}")
        return None

    async def update_contact_address(self, contact_id: str, address_data: dict) -> bool:
        """Update contact address fields."""
        url = f"{self.base_url}/{contact_id}"
        
        properties = {}
        if "city" in address_data:
            properties["city"] = address_data["city"]
        if "country" in address_data:
            properties["country"] = address_data["country"]
        if "postalCode" in address_data:
            properties["zip"] = address_data["postalCode"]
        if "streetAddress" in address_data:
            properties["address"] = address_data["streetAddress"]
            
        payload = {"properties": properties}
        
        try:
            session = await self._get_session()
            async with session.patch(url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Successfully updated contact {contact_id} address")
                    return True
                else:
                    logger.error(f"Error updating contact: {await response.text()}")
                    return False
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error updating contact: {e}")
            return False

    async def update_registration_plate(self, contact_id: str, plate_number: str, insured_vehicle: str = None) -> bool:
        """Update contact's vehicle registration plate and optionally the insured vehicle."""
        url = f"{self.base_url}/{contact_id}"
        properties = {
            "registration_plate": plate_number
        }
        if insured_vehicle:
            properties["insured_vehicle"] = insured_vehicle
        
        payload = {
            "properties": properties
        }
        
        try:
            session = await self._get_session()
            async with session.patch(url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Successfully updated registration plate for contact {contact_id}")
                    return True
                else:
                    logger.error(f"Error updating registration plate: {await response.text()}")
                    return False
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error updating registration plate: {e}")
            return False

    async def get_contact_policy_info(self, contact_id: str) -> dict | None:
        """Get contact's policy info from HubSpot."""
        url = f"{self.base_url}/{contact_id}"
        params = {"properties": "policy_info,firstname,lastname,email"}
        
        try:
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("properties", {})
                else:
                    logger.error(f"Error getting contact policy info: {await response.text()}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error getting contact policy info: {e}")
            return None

    async def create_ticket(
        self, 
        subject: str, 
        description: str, 
        priority: str = "MEDIUM",
        contact_id: str = None
    ) -> dict | None:
        """Create a support ticket in HubSpot.
        
        Args:
            subject: Ticket subject/title
            description: Ticket description/content
            priority: LOW, MEDIUM, or HIGH
            contact_id: Optional contact ID to associate ticket with
        """
        url = "https://api.hubapi.com/crm/v3/objects/tickets"
        
        payload = {
            "properties": {
                "subject": subject,
                "content": description,
                "hs_ticket_priority": priority.upper(),
                "hs_pipeline": "0",  # Default support pipeline
                "hs_pipeline_stage": "1"  # New stage
            }
        }
        
        # Associate with contact if provided
        if contact_id:
            payload["associations"] = [{
                "to": {"id": int(contact_id)},
                "types": [{
                    "associationCategory": "HUBSPOT_DEFINED",
                    "associationTypeId": 16  # Ticket to Contact
                }]
            }]
        
        try:
            session = await self._get_session()
            async with session.post(url, json=payload) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    logger.info(f"Successfully created ticket: {data.get('id')}")
                    return data
                else:
                    logger.error(f"Error creating ticket: {await response.text()}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error creating ticket: {e}")
            return None
