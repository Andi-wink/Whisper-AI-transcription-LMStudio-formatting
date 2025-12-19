"""
HubSpot Client
==============
Client for HubSpot CRM API operations.
"""

import os
import logging
import aiohttp

logger = logging.getLogger("hubspot-client")


class HubSpotClient:
    """Client for HubSpot CRM API operations."""
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.getenv("HUBSPOT_ACCESS_TOKEN")
        self.base_url = "https://api.hubapi.com/crm/v3/objects"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def get_contact_by_email(self, email: str):
        """Search for a contact by email."""
        url = f"{self.base_url}/contacts/search"
        payload = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email
                }]
            }],
            "properties": ["email", "firstname", "lastname", "city", "country", "zip", "address", "policy_info", "vehicle_registration"]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["total"] > 0:
                        return data["results"][0]
                else:
                    logger.error(f"Error searching contact: {await response.text()}")
        return None

    async def update_contact_address(self, contact_id: str, address_data: dict) -> bool:
        """Update contact address fields."""
        url = f"{self.base_url}/contacts/{contact_id}"
        
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
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=self.headers, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Successfully updated contact address {contact_id}")
                    return True
                else:
                    logger.error(f"Error updating contact: {await response.text()}")
                    return False

    async def update_registration_plate(self, contact_id: str, plate_number: str) -> bool:
        """Update contact vehicle registration plate."""
        url = f"{self.base_url}/contacts/{contact_id}"
        payload = {"properties": {"vehicle_registration": plate_number}}
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=self.headers, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Successfully updated registration plate for {contact_id}")
                    return True
                else:
                    logger.error(f"Error updating registration plate: {await response.text()}")
                    return False

    async def get_contact_policy_info(self, contact_id: str) -> dict:
        """Retrieve contact policy info."""
        url = f"{self.base_url}/contacts/{contact_id}?properties=policy_info,vehicle_registration,firstname,lastname"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("properties", {})
                else:
                    logger.error(f"Error getting policy info: {await response.text()}")
                    return None

    async def create_ticket(self, subject: str, description: str, priority: str = "MEDIUM", contact_id: str = None) -> dict:
        """Create a support ticket in HubSpot."""
        url = f"{self.base_url}/tickets"
        
        # Map priority to HubSpot values
        priority_map = {"LOW": "LOW", "MEDIUM": "MEDIUM", "HIGH": "HIGH"}
        hs_priority = priority_map.get(priority.upper(), "MEDIUM")
        
        payload = {
            "properties": {
                "subject": subject,
                "content": description,
                "hs_pipeline": "0",
                "hs_pipeline_stage": "1",
                "hs_ticket_priority": hs_priority
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status == 201:
                    ticket = await response.json()
                    logger.info(f"Created ticket: {ticket.get('id')}")
                    
                    # Associate with contact if provided
                    if contact_id:
                        await self._associate_ticket_to_contact(ticket["id"], contact_id)
                    
                    return ticket
                else:
                    logger.error(f"Error creating ticket: {await response.text()}")
                    return None

    async def _associate_ticket_to_contact(self, ticket_id: str, contact_id: str) -> bool:
        """Associate a ticket with a contact."""
        url = f"{self.base_url}/tickets/{ticket_id}/associations/contacts/{contact_id}/16"
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=self.headers) as response:
                if response.status == 200:
                    logger.info(f"Associated ticket {ticket_id} with contact {contact_id}")
                    return True
                else:
                    logger.error(f"Error associating ticket: {await response.text()}")
                    return False
