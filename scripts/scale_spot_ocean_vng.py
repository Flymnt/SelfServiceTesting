#!/usr/bin/env python3
"""Scale Spot Ocean VNG Capacity
Calls the Spot.io Ocean AWS API to update Virtual Node Group (Launch Spec) capacity.

This script is called by the GitHub Actions workflow to scale VNG capacity.

API Reference:
https://spec.dev.spot.io/#tag/Ocean-AWS/operation/OceanAWSLaunchSpecUpdate

Endpoint: PUT /ocean/aws/k8s/launchSpec/{launchSpecId}
Payload: Updates resourceLimits.minInstanceCount and resourceLimits.maxInstanceCount

Environment Variables:
    SPOT_TOKEN: Bearer token for Spot.io API authentication
    SPOT_ACCOUNT_ID: Spot.io account ID (e.g., act-123abc)
    VNG_ID: Launch Spec ID (VNG ID) to scale (e.g., ols-a1b2c3d4)
    MIN_CAPACITY: New minimum number of instances
    MAX_CAPACITY: Maximum number of instances
    REASON: Reason for the scaling operation
    TRIGGERED_BY: Email of user who triggered the action
"""

import os
import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional


class SpotOceanScaler:
    """Handle Spot Ocean VNG scaling operations"""
    
    def __init__(self, token: str, account_id: str):
        self.token = token
        self.account_id = account_id
        self.base_url = "https://api.spotinst.io"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
    
    def get_launch_spec_details(self, vng_id: str) -> Dict[str, Any]:
        """
        Fetch current Launch Spec (VNG) configuration from Spot.io
        
        Args:
            vng_id: Launch Spec ID (Virtual Node Group ID)
            
        Returns:
            Launch Spec configuration object
        """
        endpoint = f"/ocean/aws/k8s/launchSpec/{vng_id}"
        params = {"accountId": self.account_id}
        
        print(f"📋 Fetching Launch Spec details for {vng_id}...")
        response = requests.get(
            self.base_url + endpoint,
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        
        launch_spec_data = response.json()
        if "response" in launch_spec_data:
            return launch_spec_data["response"]["items"][0]
        return launch_spec_data
    
    def scale_vng(
        self,
        cluster_id: str,
        vng_id: str,
        min_capacity: int,
        max_capacity: int,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        Update Virtual Node Group resource limits in Spot Ocean.
        
        Uses the OceanAWSLaunchSpecUpdate endpoint to update the Launch Spec
        (VNG) resource limits (minInstanceCount and maxInstanceCount).
        
        Args:
            cluster_id: Ocean cluster ID (for reference/logging)
            vng_id: Launch Spec ID to scale
            min_capacity: New minimum number of instances
            max_capacity: New maximum number of instances
            reason: Optional reason for scaling
            
        Returns:
            API response with update status
        """
        
        # First, fetch current Launch Spec configuration
        try:
            current_launch_spec = self.get_launch_spec_details(vng_id)
        except Exception as e:
            print(f"⚠️  Warning: Could not fetch current Launch Spec config: {str(e)}")
            current_launch_spec = {}
        
        # Build update payload with only resourceLimits (API rejects other fields)
        update_payload = {
            "launchSpec": {
                "resourceLimits": {
                    "minInstanceCount": min_capacity,
                    "maxInstanceCount": max_capacity,
                }
            }
        }
        
        # Make API call to update Launch Spec
        endpoint = f"/ocean/aws/k8s/launchSpec/{vng_id}"
        params = {"accountId": self.account_id}
        
        print(f"\n🔄 Scaling Launch Spec (VNG) {vng_id}:")
        print(f"   Min Instances: {min_capacity}")
        print(f"   Max Instances: {max_capacity}")
        if reason:
            print(f"   Reason: {reason}")
        
        response = requests.put(
            self.base_url + endpoint,
            headers=self.headers,
            params=params,
            json=update_payload
        )
        
        if response.status_code not in [200, 201]:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()
        
        result = response.json()
        print(f"\n✓ Launch Spec (VNG) scaling update submitted successfully!")
        print(json.dumps(result, indent=2))
        
        return result
    
    def validate_scaling_parameters(
        self,
        min_capacity: int,
        max_capacity: int
    ) -> bool:
        """
        Validate that scaling parameters are logically consistent
        
        Returns:
            True if valid, raises exception if invalid
        """
        if min_capacity < 1:
            raise ValueError(f"min_capacity must be >= 1, got {min_capacity}")
        
        if max_capacity < min_capacity:
            raise ValueError(
                f"max_capacity ({max_capacity}) must be >= "
                f"min_capacity ({min_capacity})"
            )
        
        return True


def main():
    """Main entry point"""
    
    # Load environment variables
    spot_token = os.getenv("SPOT_TOKEN")
    spot_account_id = os.getenv("SPOT_ACCOUNT_ID")
    vng_id = os.getenv("VNG_ID")
    min_capacity_str = os.getenv("MIN_CAPACITY")
    max_capacity_str = os.getenv("MAX_CAPACITY")
    reason = os.getenv("REASON", "")
    triggered_by = os.getenv("TRIGGERED_BY", "GitHub Actions")
    
    # Validate environment
    missing_vars = []
    if not spot_token:
        missing_vars.append("SPOT_TOKEN")
    if not spot_account_id:
        missing_vars.append("SPOT_ACCOUNT_ID")
    if not vng_id:
        missing_vars.append("VNG_ID")
    if not min_capacity_str:
        missing_vars.append("MIN_CAPACITY")
    if not max_capacity_str:
        missing_vars.append("MAX_CAPACITY")
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    try:
        # Parse capacity values
        min_capacity = int(min_capacity_str)
        max_capacity = int(max_capacity_str)
    except ValueError as e:
        print(f"❌ Error parsing capacity values: {str(e)}")
        sys.exit(1)
    
    try:
        # Initialize scaler
        scaler = SpotOceanScaler(spot_token, spot_account_id)
        
        # Validate parameters
        print("✓ Validating scaling parameters...")
        scaler.validate_scaling_parameters(
            min_capacity,
            max_capacity
        )
        
        # Execute scaling
        result = scaler.scale_vng(
            cluster_id="",
            vng_id=vng_id,
            min_capacity=min_capacity,
            max_capacity=max_capacity,
            reason=reason
        )
        
        print("\n" + "="*60)
        print("✓ Scaling operation completed successfully!")
        print("="*60)
        print(f"\nScaling Summary:")
        print(f"  Launch Spec (VNG): {vng_id}")
        print(f"  Min Instances: {min_capacity}, Max Instances: {max_capacity}")
        print(f"  Triggered by: {triggered_by}")
        print(f"  Timestamp: {datetime.utcnow().isoformat()}Z")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error during scaling operation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
