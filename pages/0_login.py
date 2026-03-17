import streamlit as st
from supabase import create_client

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = init_connection()

st.title("Zodiac Engine: Executive Access")
st.markdown("<div style='color:#7f8c8d; margin-top:-15px; margin-bottom: 20px;'>Secure authentication for personalized astrological intelligence.</div>", unsafe_allow_html=True)
st.divider()

if not supabase:
    st.error("Database connection failed. Please check your secrets.")
    st.stop()

# --- LOGIN UI ---
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### 🔐 Secure Login")
    
    with st.form("login_form"):
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit_login = st.form_submit_button("Log In", use_container_width=True)
        with col_btn2:
            submit_signup = st.form_submit_button("Create Account", use_container_width=True)

    # --- AUTHENTICATION LOGIC ---
    if submit_login:
        if email and password:
            with st.spinner("Authenticating..."):
                try:
                    # Attempt to log in via Supabase Auth
                    auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = auth_response.user
                    st.success("Login successful! Redirecting...")
                    st.rerun() # This instantly forces app.py to rebuild the sidebar!
                except Exception as e:
                    st.error(f"Login failed: {e}")
        else:
            st.warning("Please enter both email and password.")

    if submit_signup:
        if email and password:
            with st.spinner("Provisioning account..."):
                try:
                    # Create a new user in Supabase Auth
                    auth_response = supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Account created successfully! You can now log in.")
                except Exception as e:
                    st.error(f"Sign up failed: {e}")
        else:
            st.warning("Please enter an email and password to sign up.")
