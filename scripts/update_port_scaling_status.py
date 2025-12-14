#!/usr/bin/env python3
"""
Update Port.io with Scaling Result
After the Spot.io scaling operation completes, update Port.io with the result
so users can see the action status in the Port.io dashboard.

This script runs as the final step in the GitHub Actions workflow to report
back the scaling operation outcome to Port.io.

Environment Variables:
    PORT_CLIENT_ID: Port.io client ID for authentication
    PORT_CLIENT_SECRET: Port.io client secret
    CLUSTER_ID: Ocean Cluster ID (to identify which entity to update)
    SCALING_STATUS: Status from GitHub Actions job (success/failure)
"""

import os
import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional


class PortStatusReporter:
    """Report scaling operation status back to Port.io"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.port.io/v1"
        self.access_token = None
    
    def authenticate(self) -> str:
        """Get access token from Port.io"""
        auth_url = f"{self.base_url}/auth/access_token"
        payload = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
        }
        
        response = requests.post(auth_url, json=payload)
        response.raise_for_status()
        
        self.access_token = response.json()["accessToken"]
        print(f"✓ Authenticated with Port.io")
        return self.access_token
    
    def update_entity_status(
        self,
        blueprint_id: str,
        entity_identifier: str,
        scaling_status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update entity with scaling operation status
        
        Args:
            blueprint_id: Port.io blueprint ID
            entity_identifier: Entity ID to update
            scaling_status: Status from workflow (success/failure)
            details: Optional additional details
            
        Returns:
            API response
        """
        
        if not self.access_token:
            self.authenticate()
        
        # Map GitHub Actions status to Port status
        is_successful = scaling_status.lower() == "success"
        port_status = "COMPLETED" if is_successful else "FAILED"
        
        # Build update payload
        entity_update = {
            "properties": {
                "last_scaling_status": port_status,
                "last_scaling_time": datetime.utcnow().isoformat() + "Z",
                "scaling_job_link": os.getenv("GITHUB_SERVER_URL", "https://github.com") + "/" +
                                   os.getenv("GITHUB_REPOSITORY", "") + "/actions/runs/" +
                                   os.getenv("GITHUB_RUN_ID", ""),
            }
        }
        
        if details:
            entity_update["properties"].update(details)
        
        # Send update to Port.io
        url = f"{self.base_url}/blueprints/{blueprint_id}/entities/{entity_identifier}"
        params = {"upsert": "true"}
        headers = {
            "Authorization": self.access_token,
            "Content-Type": "application/json",
        }
        
        print(f"\n📤 Updating Port.io entity {entity_identifier}")
        print(f"   Status: {port_status}")
        
        response = requests.patch(url, json=entity_update, headers=headers, params=params)
        
        if response.status_code not in [200, 201]:
            print(f"⚠️  Warning: Could not update Port.io: {response.status_code}")
            print(f"   Response: {response.text}")
            # Don't fail - this is a secondary action
            return {}
        
        result = response.json()
        print(f"✓ Port.io entity updated successfully!")
        return result


def main():
    """Main entry point"""
    
    # Load environment
    port_client_id = os.getenv("PORT_CLIENT_ID")
    port_client_secret = os.getenv("PORT_CLIENT_SECRET")
    cluster_id = os.getenv("CLUSTER_ID")
    scaling_status = os.getenv("SCALING_STATUS", "unknown")
    blueprint_id = os.getenv("BLUEPRINT_ID", "spot_ocean_cluster")
    
    # Validate environment
    missing_vars = []
    if not port_client_id:
        missing_vars.append("PORT_CLIENT_ID")
    if not port_client_secret:
        missing_vars.append("PORT_CLIENT_SECRET")
    if not cluster_id:
        missing_vars.append("CLUSTER_ID")
    
    if missing_vars:
        print(f"⚠️  Skipping Port.io update - missing: {', '.join(missing_vars)}")
        sys.exit(0)  # Don't fail - this is secondary
    
    try:
        reporter = PortStatusReporter(port_client_id, port_client_secret)
        
        # Build entity identifier (use cluster_id-heartbeat to match the entity created by heartbeat script)
        entity_identifier = f"{cluster_id}-heartbeat"
        
        # Update Port.io
        reporter.update_entity_status(
            blueprint_id=blueprint_id,
            entity_identifier=entity_identifier,
            scaling_status=scaling_status,
            details={
                "workflow_run_id": os.getenv("GITHUB_RUN_ID", ""),
                "workflow_name": os.getenv("GITHUB_WORKFLOW", ""),
                "workflow_actor": os.getenv("GITHUB_ACTOR", ""),
            }
        )
        
        print("\n" + "="*60)
        print("✓ Port.io status update completed!")
        print("="*60)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n⚠️  Error updating Port.io: {str(e)}")
        # Don't fail the workflow - this is a secondary action
        import traceback
        traceback.print_exc()
        sys.exit(0)


if __name__ == "__main__":
    main()
