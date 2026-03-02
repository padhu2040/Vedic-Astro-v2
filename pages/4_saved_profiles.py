import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- SETUP SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("⚠️ Could not connect to Supabase. Check your Streamlit secrets.")
    st.stop()

# --- UI CONFIG ---
st.title(":material/cloud_done: Cloud Profile Vault")
st.markdown("Your family profiles are now securely synced to the cloud. They will never be deleted when the app updates.")
st.divider()

# --- ADD / UPDATE PROFILE ---
with st.expander(":material/person_add: Add or Edit Profile", expanded=True):
    st.info("💡 **How to Edit:** To update someone's details, just type their exact Name again and enter the new data. It will automatically overwrite their old record in the cloud!")
    
    with st.form("add_profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            p_name = st.text_input("Full Name")
            p_dob = st.date_input("Date of Birth", min_value=datetime(1950, 1, 1).date())
        with col2:
            p_tob = st.time_input("Time of Birth", step=60) 
            p_city = st.text_input("City of Birth")
            
        submitted = st.form_submit_button("Save to Cloud Vault", type="primary", use_container_width=True)
        
        if submitted:
            if p_name.strip() == "":
                st.error("Name cannot be empty!")
            else:
                try:
                    # Supabase 'upsert' acts as an Insert or Replace
                    data = {
                        "name": p_name.strip(),
                        "dob": p_dob.strftime("%Y-%m-%d"),
                        "tob": p_tob.strftime("%H:%M:%S"),
                        "city": p_city.strip()
                    }
                    supabase.table("profiles").upsert(data).execute()
                    
                    st.success(f"Profile for **{p_name}** successfully secured in the cloud!")
                    st.rerun() 
                except Exception as e:
                    st.error(f"Cloud Database Error: {e}")

# --- VIEW & MANAGE PROFILES ---
st.markdown("### :material/badge: Saved Cloud Profiles")

try:
    # Fetch all records from Supabase
    response = supabase.table("profiles").select("*").execute()
    records = response.data
    
    if records:
        # Convert to a beautiful Pandas DataFrame
        df = pd.DataFrame(records)
        df = df.rename(columns={
            "name": "Name", 
            "dob": "Date of Birth", 
            "tob": "Time of Birth", 
            "city": "City"
        })
        
        # Reorder columns just to be clean
        df = df[["Name", "Date of Birth", "Time of Birth", "City"]]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.write("")
        with st.expander(":material/delete: Delete a Profile"):
            del_name = st.selectbox("Select Profile to Remove", df['Name'].tolist())
            if st.button("Delete Permanently"):
                supabase.table("profiles").delete().eq("name", del_name).execute()
                st.success(f"Removed {del_name} from the cloud vault.")
                st.rerun() 
    else:
        st.info("Your cloud vault is currently empty. Add yourself above to get started!")

except Exception as e:
    st.error(f"Failed to fetch profiles from cloud: {e}")
