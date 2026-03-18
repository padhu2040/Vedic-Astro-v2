import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

st.set_page_config(page_title="CRM / Saved Profiles", layout="wide")

# --- SECURITY GATEKEEPER & GLOBAL SYNC INIT ---
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("🔒 Please log in to view and manage your private cloud vault.")
    st.stop()

user_id = st.session_state.user.id

if "global_active_profile" not in st.session_state:
    st.session_state.global_active_profile = None

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

# --- FETCH CURRENT VAULT STATUS ---
response = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
records = response.data
current_profile_count = len(records)

# --- FREEMIUM / PLG SETTINGS ---
# Note: You can eventually link this to a Stripe database column!
PROFILE_LIMIT = 2
is_premium = st.session_state.get("is_premium", False) 

# --- UI CONFIG ---
st.title(":material/cloud_done: Private Profile Vault")
st.markdown("Your family and client profiles are securely encrypted and locked to your account.")
st.divider()

# --- ADD / UPDATE PROFILE ---
with st.expander(":material/person_add: Add or Edit Profile", expanded=True):
    
    # 💎 THE PAYWALL / VAULT TRACKER
    if not is_premium:
        color = "green" if current_profile_count < PROFILE_LIMIT else "red"
        st.markdown(f"<div style='font-size:13px; font-weight:bold; color:{color}; margin-bottom:10px;'>Vault Usage: {current_profile_count} / {PROFILE_LIMIT} Free Profiles Used</div>", unsafe_allow_html=True)
    
    st.info("💡 **How to Edit:** To update someone's details, just type their exact Name again and enter the new data. It will safely overwrite your old record.")
    
    with st.form("add_profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            p_name = st.text_input("Full Name")
            p_dob = st.date_input("Date of Birth", min_value=datetime(1950, 1, 1).date())
        with col2:
            p_tob = st.time_input("Time of Birth", step=60) 
            p_city = st.text_input("City of Birth")
            
        submitted = st.form_submit_button("Save to Private Vault", type="primary", use_container_width=True)
        
        if submitted:
            if p_name.strip() == "":
                st.error("Name cannot be empty!")
            else:
                with st.spinner("Securing data..."):
                    try:
                        clean_name = p_name.strip()
                        data = {
                            "user_id": user_id, 
                            "name": clean_name,
                            "dob": p_dob.strftime("%Y-%m-%d"),
                            "tob": p_tob.strftime("%H:%M:%S"),
                            "city": p_city.strip()
                        }
                        
                        # 1. Check if THIS user already has a profile with this exact name
                        existing = supabase.table("profiles").select("name").eq("user_id", user_id).eq("name", clean_name).execute()
                        
                        if existing.data:
                            # It's an EDIT - Always allow this!
                            supabase.table("profiles").update(data).eq("user_id", user_id).eq("name", clean_name).execute()
                            st.success(f"Profile for **{clean_name}** successfully updated!")
                            st.rerun()
                        else:
                            # It's a NEW addition - Hit the Paywall Check
                            if current_profile_count >= PROFILE_LIMIT and not is_premium:
                                st.error(f"💎 **Free Tier Limit Reached:** You can only save {PROFILE_LIMIT} profiles on the free plan.")
                                st.warning("Upgrade to Premium to unlock unlimited profiles for your clients and extended family.")
                                # st.link_button("Upgrade to Premium", "YOUR_STRIPE_LINK_HERE")
                            else:
                                supabase.table("profiles").insert(data).execute()
                                st.success(f"Profile for **{clean_name}** securely added to your vault!")
                                st.rerun() 
                                
                    except Exception as e:
                        st.error(f"Cloud Database Error: {e}")

# --- VIEW & MANAGE PROFILES ---
st.markdown("### :material/badge: Saved Cloud Profiles")

try:
    if records:
        df = pd.DataFrame(records)
        df = df.rename(columns={"name": "Name", "dob": "Date of Birth", "tob": "Time of Birth", "city": "City"})
        df = df[["Name", "Date of Birth", "Time of Birth", "City"]]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.write("")
        with st.expander(":material/delete: Delete a Profile"):
            del_name = st.selectbox("Select Profile to Remove", df['Name'].tolist())
            if st.button("Delete Permanently", type="secondary"):
                
                # Delete ONLY if the name AND user_id match
                supabase.table("profiles").delete().eq("user_id", user_id).eq("name", del_name).execute()
                
                # --- GLOBAL SYNC CLEANUP ---
                # If they deleted the person they were currently viewing, wipe the global memory to prevent crashes
                if st.session_state.global_active_profile == del_name:
                    st.session_state.global_active_profile = None
                
                st.success(f"Removed {del_name} from your secure vault.")
                st.rerun() 
    else:
        st.info("Your secure vault is currently empty. Add yourself above to get started!")

except Exception as e:
    st.error(f"Failed to fetch profiles from cloud: {e}")
