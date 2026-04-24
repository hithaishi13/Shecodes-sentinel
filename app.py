import streamlit as st
from auth import show_auth_page
from donor_dashboard import show_donor_dashboard
from public_ngo_dashboard import show_public_ngo_dashboard

def main():
    st.set_page_config(page_title="Food Redistribution System", page_icon="🍽️", layout="wide")
    
    # Custom CSS
    st.markdown("""
        <style>
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .stButton > button:hover {
            background-color: #45a049;
        }
        .css-1kyxreq {
            background-color: #f0f2f6;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.sidebar.title("🍽️ Food Redistribution")
    st.sidebar.markdown("### From Waste to Worth")
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.radio(
        "Select Page",
        ["🏢 NGO Dashboard (Public)", "🍕 Restaurant Donor Login"],
        help="NGOs don't need to login - just view and accept donations!"
    )
    
    if page == "🍕 Restaurant Donor Login":
        if "authenticated" not in st.session_state:
            st.session_state["authenticated"] = False
        
        if not st.session_state["authenticated"]:
            show_auth_page()
        else:
            if st.session_state["role"] == "donor":
                show_donor_dashboard()
            else:
                st.warning("Invalid role")
    else:
        # NGO Dashboard - No login required!
        show_public_ngo_dashboard()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Impact")
    st.sidebar.metric("Food Waste Reduced", "500+ kg", "Monthly")
    st.sidebar.metric("Active Restaurants", "100+", "Across Bangalore")
    st.sidebar.metric("NGOs Partnered", "15+", "Ready to collect")

if __name__ == "__main__":
    main()