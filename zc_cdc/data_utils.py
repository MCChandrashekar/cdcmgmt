#zc_cdc/data_utils.py
import json
from datetime import datetime

# ---- ZONE DATA ----
def load_zones():
    """Load zones data from JSON file."""
    try:
        with open("../CDCMgmt/data/zones_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"active_zones": {}, "inactive_zones": {}}
    except json.JSONDecodeError:
        return {"active_zones": {}, "inactive_zones": {}}

def save_zones(data):
    """Save zones data to JSON file."""
    with open("../CDCMgmt/data/zones_data.json", "w") as file:
        json.dump(data, file, indent=4)


# ---- ALIAS DATA ----
def load_alias():
    """Load alias data from JSON file."""
    try:
        with open("../CDCMgmt/data/alias_data.json", "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"member_aliases": {}, "free_aliases": {}}

def save_alias(alias_data):
    """Save alias data to JSON file."""
    with open("../CDCMgmt/data/alias_data.json", "w") as file:
        json.dump(alias_data, file, indent=4)


# ---- ZONE GROUP DATA ----
def load_zonegroup():
    """Load zone group data from JSON file."""
    try:
        with open("../CDCMgmt/data/zonegroup_data.json", "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"zone_groups": {}}

def save_zonegroup(zonegroup_data):
    """Save zone group data to JSON file."""
    with open("../CDCMgmt/data/zonegroup_data.json", "w") as file:
        json.dump(zonegroup_data, file, indent=4)


# ---- REGISTERED NODES DATA ----
def load_registered_nodes():
    try:
        with open('../CDCMgmt/data/nodes.json', 'r') as f:
            data = json.load(f)
        return data.get('nodes', [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_registered_nodes(nodes_data):
    with open('../CDCMgmt/data/nodes.json', 'w') as f:
        json.dump({'nodes': nodes_data}, f, indent=4)


def sync_zone_config_from_data_files():
    try:
        with open("../CDCMgmt/data/zonegroup_data.json", "r") as f:
            zonegroups = json.load(f)
        with open("../CDCMgmt/data/zones_data.json", "r") as f:
            zones = json.load(f)
        with open("../CDCMgmt/data/alias_data.json", "r") as f:
            aliases = json.load(f)
    except Exception as e:
        print(f"Error reading data files: {e}")
        return

    zone_config = {
        "active": [],
        "inactive": [],
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    for group in zonegroups:
        group_id = group["ZoneGrpId"]
        group_name = group["ZoneGrpName"]

        group_zones = [z for z in zones if z["ZoneGrpId"] == group_id]

        zone_members = []
        for zone in group_zones:
            zone_id = zone["ZoneId"]
            zone_aliases = [a for a in aliases if a["ZoneId"] == zone_id]

            zone_entry = {
                "ZoneId": zone_id,
                "ZoneName": zone["ZoneName"],
                "aliasCount": len(zone_aliases),
                "AliasMembers": zone_aliases
            }
            zone_members.append(zone_entry)

        group_entry = {
            "ZoneGrpId": group_id,
            "ZoneGrpName": group_name,
            "zoneCount": len(zone_members),
            "ZoneMembers": zone_members
        }

        if group_name == "Ungrouped":
            zone_config["inactive"].append(group_entry)
        else:
            zone_config["active"].append(group_entry)

    with open("../CDCMgmt/data/zone_config.json", "w") as f:
        json.dump(zone_config, f, indent=2)
