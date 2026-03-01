import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- UI CONFIG ---
st.title(":material/group: Family Profile Vault")
st.markdown("Save your family and friends here once. In the next phase, we will link these directly to the astrological engines so you never have to type them again.")
st.divider()

# --- DATABASE SETUP ---
# This automatically creates a tiny, secure local file called 'astro_profiles.db'
conn = sqlite3.connect('astro_profiles.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS profiles
    (name TEXT PRIMARY KEY, dob TEXT, tob TEXT, city TEXT)
''')
conn.commit()

# --- ADD NEW PROFILE ---
with st.expander(":material/person_add: Add New Profile", expanded=True):
    with st.form("add_profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            p_name = st.text_input("Full Name")
            p_dob = st.date_input("Date of Birth", min_value=datetime(1950, 1, 1).date())
        with col2:
            p_tob = st.time_input("Time of Birth")
            p_city = st.text_input("City of Birth")
            
        submitted = st.form_submit_button("Save to Vault", type="primary", use_container_width=True)
        
        if submitted:
            if p_name.strip() == "":
                st.error("Name cannot be empty!")
            else:
                try:
                    # Insert or Replace allows you to update someone's details if you type their name again
                    c.execute("INSERT OR REPLACE INTO profiles VALUES (?, ?, ?, ?)", 
                              (p_name, p_dob.strftime("%Y-%m-%d"), p_tob.strftime("%H:%M:%S"), p_city))
                    conn.commit()
                    st.success(f"Profile for **{p_name}** securely saved to vault!")
                except Exception as e:
                    st.error(f"Database Error: {e}")

# --- VIEW & MANAGE PROFILES ---
st.markdown("### :material/badge: Saved Profiles")

# Read the database into a beautiful Pandas Dataframe
df = pd.read_sql_query("SELECT name as Name, dob as 'Date of Birth', tob as 'Time of Birth', city as City FROM profiles", conn)

if not df.empty:
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.write("")
    with st.expander(":material/delete: Delete a Profile"):
        del_name = st.selectbox("Select Profile to Remove", df['Name'].tolist())
        if st.button("Delete Permanently"):
            c.execute("DELETE FROM profiles WHERE name=?", (del_name,))
            conn.commit()
            st.success(f"Removed {del_name} from the vault.")
            st.rerun() # Refreshes the page to update the table
else:
    st.info("Your vault is currently empty. Add yourself above to get started!")

conn.close()
