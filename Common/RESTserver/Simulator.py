import re
from datetime import datetime

_zones = {}

def create_zone(zone_name):
    # Check if zone name is alphanumeric (with hyphens and underscores allowed)
    if not re.match(r'^[a-zA-Z0-9-_]+$', zone_name):
        raise ValueError("Zone name must contain only alphanumeric characters, hyphens, and underscores")
    
    # Check if zone already exists
    if zone_name in _zones:
        raise ValueError(f"Zone '{zone_name}' already exists")
    
    # Create the zone
    zone_info = {
        "id": 1,
        "name": zone_name,
        "status": "active"
    }
    
    _zones[zone_name] = zone_info
    return zone_info

def delete_zone(zone_name):
    if zone_name not in _zones:
        raise ValueError(f"Zone '{zone_name}' not found")
    
    # Delete the zone
    zone_info = _zones.pop(zone_name)
    
    return {
        "deleted": True,
        "zone_id": zone_info["id"],
        "zone_name": zone_name
    }

def get_all_zones():
    return list(_zones.values())

def get_zone(zone_name):
    return _zones.get(zone_name)

