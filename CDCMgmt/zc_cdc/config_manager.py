import json
import time
from .activate_zone import load_data as load_zones
from .zonegroup import load_zonegroup

ZONE_CONFIG_PATH = "../CDCMgmt/data/zone_config.json"

def update_zone_config():
    """Centralized function to update the shared config file"""
    config = {
        "active": [],
        "inactive": [],
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    zonegroup_data = load_zonegroup()
    zones_data = load_zones()

    # Group zones by their group
    zones_by_group = {}
    for group_id, group in zonegroup_data["zone_groups"].items():
        zones_by_group[group_id] = {
            "ZoneGrpId": int(group_id),
            "ZoneGrpName": group["name"],
            "zoneCount": len(group["zones"]),
            "ZoneMembers": []
        }
        for zone_id in group["zones"]:
            zone = zones_data["active_zones"].get(zone_id) or zones_data["inactive_zones"].get(zone_id)
            if zone:
                alias_members = []
                for alias_id, alias in zone.get("aliases", {}).items():
                    alias_members.append({
                        "AliasId": int(alias_id),
                        "AliasName": alias["name"],
                        "Type": alias["type"],
                        "IPAddress": alias.get("ip", ""),
                        "NQN": alias.get("nqn", "")
                    })
                
                zones_by_group[group_id]["ZoneMembers"].append({
                    "ZoneId": int(zone_id),
                    "ZoneName": zone["name"],
                    "aliasCount": len(alias_members),
                    "AliasMembers": alias_members
                })
        
        # Add to active or inactive list
        if group.get("active", False):
            config["active"].append(zones_by_group[group_id])
        else:
            config["inactive"].append(zones_by_group[group_id])

    # Add ungrouped zones to inactive
    all_grouped_zones = set()
    for group in zonegroup_data["zone_groups"].values():
        all_grouped_zones.update(group["zones"])
    
    ungrouped_zones = []
    for zone_id, zone in zones_data["inactive_zones"].items():
        if zone_id not in all_grouped_zones:
            alias_members = []
            for alias_id, alias in zone.get("aliases", {}).items():
                alias_members.append({
                    "AliasId": int(alias_id),
                    "AliasName": alias["name"],
                    "Type": alias["type"],
                    "IPAddress": alias.get("ip", ""),
                    "NQN": alias.get("nqn", "")
                })
            
            ungrouped_zones.append({
                "ZoneId": int(zone_id),
                "ZoneName": zone["name"],
                "aliasCount": len(alias_members),
                "AliasMembers": alias_members
            })
    
    if ungrouped_zones:
        config["inactive"].append({
            "ZoneGrpId": 0,
            "ZoneGrpName": "Ungrouped",
            "zoneCount": len(ungrouped_zones),
            "ZoneMembers": ungrouped_zones
        })

    with open(ZONE_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

# def update_zone_config():
#     """Centralized function to update the shared config file"""
#     config = {
#         "active": [],
#         "inactive": [],
#         "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
#     }
    
#     zonegroup_data = load_zonegroup()
#     zones_data = load_zones()

#     for group_id, group in zonegroup_data["zone_groups"].items():
#         group_entry = {
#             "ZoneGrpId": int(group_id),
#             "ZoneGrpName": group["name"],
#             "zones": []
#         }
#         for zone_id in group["zones"]:
#             zone = zones_data["active_zones"].get(zone_id) or zones_data["inactive_zones"].get(zone_id)
#             if zone:
#                 group_entry["zones"].append({
#                     "ZoneId": int(zone_id),
#                     "ZoneName": zone["name"],
#                     "aliases": list(zone.get("aliases", {}).values())
#                 })
        
#         config["active" if group.get("active") else "inactive"].append(group_entry)

#     with open(ZONE_CONFIG_PATH, "w") as f:
#         json.dump(config, f, indent=2)