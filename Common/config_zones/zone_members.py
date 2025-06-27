import streamlit as st

# Sample data
member_aliases = {
    "1": {"name": "alias1"},
    "2": {"name": "alias2"},
    "3": {"name": "alias3"},
}
free_aliases = {
    "5": {"name": "alias5"},
    "4": {"name": "alias4"},
    "9": {"name": "alias9"},
    "8": {"name": "alias8"},
}

def Alias2ZoneLink(callback_logging):
    selected_zone = {"2": {"name": "zone2"}}
    selected_zone_name = selected_zone["2"]["name"]
    st.write("#### Manage Selected Zone, its members")
    
    col1, col2 = st.columns(2)
    
    # Left Column - Member Aliases
    with col1:
        st.write("##### Add aliases")
        q1, q2 = st.columns(2, vertical_alignment='bottom')
        with q1:
            member_alias_dict = {v["name"]: k for k, v in member_aliases.items()}
            aliases_for_remove = st.multiselect(
                "Select aliases to Remove",
                options=list(member_aliases.values()),
                format_func=lambda x: x["name"]
            )
        
        with q2:
            if st.button("Remove", key="Remove"):
                if aliases_for_remove:
                    for alias in aliases_for_remove:
                        alias_id = member_alias_dict[alias["name"]]
                        free_aliases[alias_id] = member_aliases.pop(alias_id)
                        st.toast(f"Alias {alias['name']} removed from {selected_zone_name}")
                        #st.write(f"Removing alias id {alias_id} from zone={selected_zone_name}")
                        callback_logging(f"Removing alias id {alias_id} from zone={selected_zone_name}")
                else:
                    st.toast("No aliases selected for removal.", icon="⚠️")
                    
        st.write("##### Updated Zone Members")
        st.table([{"ID": k, "Name": v["name"]} for k, v in member_aliases.items()])

    # Right Column - Free Aliases
    with col2:
        st.write("##### Remove aliases")
        q3, q4 = st.columns(2, vertical_alignment='bottom')
        with q3:
            free_alias_dict = {v["name"]: k for k, v in free_aliases.items()}
            aliases_for_add = st.multiselect(
                "Select aliases to Add",
                options=list(free_aliases.values()),
                format_func=lambda x: x["name"]
            )
        with q4:
            if st.button("Add", key="add"):
                if aliases_for_add:
                    for alias in aliases_for_add:
                        alias_id = free_alias_dict[alias["name"]]
                        member_aliases[alias_id] = free_aliases.pop(alias_id)
                        st.toast(f"Alias {alias['name']} added to {selected_zone_name}")
                        #st.write(f"Alias {alias['name']} added to Zone {selected_zone_name}")
                        callback_logging(f"Alias {alias['name']} added to Zone {selected_zone_name}")
                else:
                    st.toast("No aliases selected for addition.", icon="⚠️")
                    
        st.write("##### Updated Free Members")
        st.table([{"ID": k, "Name": v["name"]} for k, v in free_aliases.items()])

if __name__ == "__main__":
    Alias2ZoneLink(st.write)