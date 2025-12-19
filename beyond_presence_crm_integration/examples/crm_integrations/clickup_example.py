"""
ClickUp CRM Integration Example
For use with Option 2 (LiveKit Agent)
"""

import os
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime


class ClickUpCRM:
    """ClickUp API client for CRM operations"""
    
    def __init__(self, api_token: str, list_id: str):
        self.api_token = api_token
        self.list_id = list_id
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json"
        }
    
    async def lookup_customer(self, phone: str) -> Dict[str, Any]:
        """Look up customer by phone number"""
        async with aiohttp.ClientSession() as session:
            # Search tasks by custom field (phone)
            url = f"{self.base_url}/list/{self.list_id}/task"
            params = {
                "custom_fields": [
                    {
                        "field_id": "phone_field_id",  # Replace with your field ID
                        "operator": "=",
                        "value": phone
                    }
                ]
            }
            
            async with session.get(url, headers=self.headers, params=params) as resp:
                if resp.status != 200:
                    return {"found": False, "error": await resp.text()}
                
                data = await resp.json()
                
                if data.get("tasks"):
                    task = data["tasks"][0]
                    
                    # Extract custom fields
                    custom_fields = {
                        field["name"]: field["value"]
                        for field in task.get("custom_fields", [])
                    }
                    
                    return {
                        "found": True,
                        "customer_id": task["id"],
                        "name": custom_fields.get("customer_name", ""),
                        "email": custom_fields.get("customer_email", ""),
                        "phone": custom_fields.get("customer_phone", ""),
                        "company": custom_fields.get("company_name", ""),
                        "status": task["status"]["status"],
                        "tags": [tag["name"] for tag in task.get("tags", [])],
                        "notes": task.get("description", ""),
                        "created_date": task["date_created"],
                        "last_updated": task["date_updated"],
                        "url": task["url"]
                    }
                
                return {"found": False}
    
    async def create_lead(
        self,
        name: str,
        email: str,
        phone: str,
        inquiry_type: str,
        details: str,
        sentiment: str = "neutral",
        priority: int = 2
    ) -> str:
        """Create a new lead in ClickUp"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/list/{self.list_id}/task"
            
            payload = {
                "name": f"Lead - {phone} - {name}",
                "description": details,
                "status": "to do",
                "priority": priority,
                "tags": [inquiry_type, sentiment],
                "custom_fields": [
                    {
                        "id": "customer_name_field_id",  # Replace with your field IDs
                        "value": name
                    },
                    {
                        "id": "customer_email_field_id",
                        "value": email
                    },
                    {
                        "id": "customer_phone_field_id",
                        "value": phone
                    },
                    {
                        "id": "inquiry_type_field_id",
                        "value": inquiry_type
                    },
                    {
                        "id": "sentiment_field_id",
                        "value": sentiment
                    },
                    {
                        "id": "lead_source_field_id",
                        "value": "Beyond Presence Avatar"
                    },
                    {
                        "id": "created_date_field_id",
                        "value": int(datetime.now().timestamp() * 1000)
                    }
                ]
            }
            
            async with session.post(url, headers=self.headers, json=payload) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to create lead: {await resp.text()}")
                
                data = await resp.json()
                return data["id"]
    
    async def update_customer_notes(
        self,
        customer_id: str,
        notes: str,
        append: bool = True
    ) -> bool:
        """Add or update notes on a customer record"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/task/{customer_id}"
            
            if append:
                # Get existing notes first
                async with session.get(url, headers=self.headers) as resp:
                    if resp.status == 200:
                        task = await resp.json()
                        existing_notes = task.get("description", "")
                        notes = f"{existing_notes}\n\n---\n{datetime.now().isoformat()}\n{notes}"
            
            payload = {
                "description": notes
            }
            
            async with session.put(url, headers=self.headers, json=payload) as resp:
                return resp.status == 200
    
    async def add_comment(
        self,
        customer_id: str,
        comment: str,
        notify_users: Optional[List[int]] = None
    ) -> str:
        """Add a comment to a customer task"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/task/{customer_id}/comment"
            
            payload = {
                "comment_text": comment,
                "notify_all": False
            }
            
            if notify_users:
                payload["assignee"] = notify_users
            
            async with session.post(url, headers=self.headers, json=payload) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to add comment: {await resp.text()}")
                
                data = await resp.json()
                return data["id"]
    
    async def update_status(
        self,
        customer_id: str,
        status: str
    ) -> bool:
        """Update customer/lead status"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/task/{customer_id}"
            
            payload = {
                "status": status
            }
            
            async with session.put(url, headers=self.headers, json=payload) as resp:
                return resp.status == 200
    
    async def assign_to_user(
        self,
        customer_id: str,
        user_id: int
    ) -> bool:
        """Assign customer/lead to a user"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/task/{customer_id}"
            
            payload = {
                "assignees": {
                    "add": [user_id]
                }
            }
            
            async with session.put(url, headers=self.headers, json=payload) as resp:
                return resp.status == 200
    
    async def get_custom_field_ids(self) -> Dict[str, str]:
        """Get all custom field IDs for the list (helper method)"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/list/{self.list_id}/field"
            
            async with session.get(url, headers=self.headers) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to get fields: {await resp.text()}")
                
                data = await resp.json()
                
                return {
                    field["name"]: field["id"]
                    for field in data.get("fields", [])
                }


# Example usage
async def example_usage():
    """Example of how to use the ClickUp CRM client"""
    
    # Initialize client
    crm = ClickUpCRM(
        api_token=os.getenv("CLICKUP_API_TOKEN"),
        list_id=os.getenv("CLICKUP_LIST_ID")
    )
    
    # Look up customer
    customer = await crm.lookup_customer("+1-510-555-0123")
    if customer["found"]:
        print(f"Found customer: {customer['name']}")
        print(f"Email: {customer['email']}")
        print(f"Status: {customer['status']}")
    
    # Create new lead
    lead_id = await crm.create_lead(
        name="John Doe",
        email="john@example.com",
        phone="+1-510-555-0123",
        inquiry_type="product_demo",
        details="Interested in enterprise plan. Wants to schedule a demo next week.",
        sentiment="positive",
        priority=3  # High priority
    )
    print(f"Created lead: {lead_id}")
    
    # Add notes
    await crm.update_customer_notes(
        customer_id=lead_id,
        notes="Called via Beyond Presence avatar. Very interested in AI features."
    )
    
    # Add comment
    await crm.add_comment(
        customer_id=lead_id,
        comment="Follow up scheduled for tomorrow at 2pm",
        notify_users=[12345]  # Notify sales rep
    )
    
    # Update status
    await crm.update_status(lead_id, "in progress")
    
    # Assign to sales rep
    await crm.assign_to_user(lead_id, user_id=12345)


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
