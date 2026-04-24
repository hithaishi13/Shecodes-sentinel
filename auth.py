import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import datetime

USERS_FILE = "data/users.csv"

def init_auth():
    """Initialize users database"""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
        df = pd.DataFrame(columns=[
            "user_id", "username", "email", "mobile", "password_hash", 
            "role", "registered_at"
        ])
        df.to_csv(USERS_FILE, index=False)

def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

def signup(username, email, mobile, password, role):
    """Register new restaurant"""
    init_auth()
    
    try:
        df = pd.read_csv(USERS_FILE)
    except:
        df = pd.DataFrame(columns=[
            "user_id", "username", "email", "mobile", "password_hash", 
            "role", "registered_at"
        ])
    
    # Check if user exists
    if not df.empty:
        if username in df['username'].values:
            return False, "Username already exists!"
        if email in df['email'].values:
            return False, "Email already registered!"
    
    # Create new user
    user_id = f"RES{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    new_user = pd.DataFrame([{
        "user_id": user_id,
        "username": username,
        "email": email,
        "mobile": mobile,
        "password_hash": hash_password(password),
        "role": role,
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    
    updated = pd.concat([df, new_user], ignore_index=True)
    updated.to_csv(USERS_FILE, index=False)
    
    return True, f"Registration successful! Your ID: {user_id}"

def login(username_or_email, password, role):
    """Authenticate restaurant"""
    try:
        df = pd.read_csv(USERS_FILE)
        if df.empty:
            return False, "", "", "", "No users found. Please sign up first!"
    except:
        return False, "", "", "", "System error. Please try again."
    
    # Find user
    user = df[
        ((df['username'] == username_or_email) | (df['email'] == username_or_email)) &
        (df['role'] == role)
    ]
    
    if user.empty:
        return False, "", "", "", "User not found!"
    
    user = user.iloc[0]
    
    if user['password_hash'] == hash_password(password):
        return True, user['user_id'], user['username'], user['email'], user['mobile']
    else:
        return False, "", "", "", "Wrong password!"

def show_auth_page():
    """Display authentication page for restaurants"""
    
    st.title("🍕 Restaurant Donor Portal")
    st.markdown("### Register or Login to Donate Food")
    st.markdown("---")
    
    init_auth()
    
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Sign Up"])
    
    with tab1:
        st.subheader("Welcome Back!")
        
        username_email = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        
        if st.button("🔓 Sign In", type="primary", use_container_width=True):
            if username_email and password:
                success, user_id, username, email, mobile = login(username_email, password, "donor")
                if success:
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = user_id
                    st.session_state["username"] = username
                    st.session_state["email"] = email
                    st.session_state["mobile"] = mobile
                    st.session_state["role"] = "donor"
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error(mobile)
            else:
                st.warning("Please enter username/email and password")
    
    with tab2:
        st.subheader("Create New Restaurant Account")
        
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Restaurant Name*")
            new_email = st.text_input("Email*")
        with col2:
            new_mobile = st.text_input("Contact Number*")
            new_password = st.text_input("Password*", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
        
        if st.button("📝 Sign Up", type="primary", use_container_width=True):
            if not all([new_username, new_email, new_mobile, new_password]):
                st.warning("Please fill all fields!")
            elif new_password != confirm_password:
                st.error("Passwords do not match!")
            elif len(new_mobile) != 10 or not new_mobile.isdigit():
                st.error("Please enter valid 10-digit mobile number!")
            else:
                success, message = signup(new_username, new_email, new_mobile, new_password, "donor")
                if success:
                    st.success(message)
                    st.info("Please go to Sign In tab to login")
                else:
                    st.error(message)

def logout():
    """Logout user"""
    for key in ["authenticated", "user_id", "username", "email", "mobile", "role"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()