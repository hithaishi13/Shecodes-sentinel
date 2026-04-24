import streamlit as st
import pandas as pd
import os
from datetime import datetime
from location_helper import show_location_picker
from auth import logout

DONATIONS_FILE = "data/donations.csv"

@st.cache_data
def load_restaurant_data():
    """Load restaurant dataset"""
    try:
        df = pd.read_csv('bangalore_food_network (1).csv')
        return df
    except:
        return pd.DataFrame()

def init_donor_files():
    """Initialize donor database files"""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DONATIONS_FILE) or os.path.getsize(DONATIONS_FILE) == 0:
        df = pd.DataFrame(columns=[
            "donation_id", "restaurant_name", "food_name", "quantity_kg", 
            "expiry_hours", "latitude", "longitude", "address",
            "restaurant_contact", "area", "status", "accepted_by", "accepted_at", "posted_at"
        ])
        df.to_csv(DONATIONS_FILE, index=False)

def post_donation(restaurant_name, food_name, quantity, expiry_hours, lat, lon, address, restaurant_contact, donor_area):
    """Save donation to database"""
    
    donation_id = f"DON{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    new_donation = pd.DataFrame([{
        "donation_id": str(donation_id),
        "restaurant_name": str(restaurant_name),
        "food_name": str(food_name),
        "quantity_kg": float(quantity),
        "expiry_hours": int(expiry_hours),
        "latitude": float(lat),
        "longitude": float(lon),
        "address": str(address)[:300],
        "restaurant_contact": str(restaurant_contact),
        "area": str(donor_area),
        "status": "pending",
        "accepted_by": "",
        "accepted_at": "",
        "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    
    if os.path.exists(DONATIONS_FILE) and os.path.getsize(DONATIONS_FILE) > 0:
        existing = pd.read_csv(DONATIONS_FILE)
        updated = pd.concat([existing, new_donation], ignore_index=True)
    else:
        updated = new_donation
    
    updated.to_csv(DONATIONS_FILE, index=False)
    
    return donation_id, None  # No SMS notifications

def show_donor_dashboard():
    """Main restaurant dashboard"""
    
    st.title("🍕 Restaurant Donor Dashboard")
    st.markdown(f"### Welcome, {st.session_state['username']}!")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 Restaurant Info")
        st.write(f"**Name:** {st.session_state['username']}")
        st.write(f"**Email:** {st.session_state['email']}")
        st.write(f"**Contact:** {st.session_state['mobile']}")
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        
        if os.path.exists(DONATIONS_FILE) and os.path.getsize(DONATIONS_FILE) > 0:
            df = pd.read_csv(DONATIONS_FILE)
            restaurant_donations = df[df['restaurant_name'] == st.session_state['username']]
            total_donations = len(restaurant_donations)
            total_food = restaurant_donations['quantity_kg'].sum() if not restaurant_donations.empty else 0
            st.metric("Total Donations", total_donations)
            st.metric("Food Donated (kg)", f"{total_food:.0f}")
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    # Load data
    restaurant_data = load_restaurant_data()
    if not restaurant_data.empty and 'Area' in restaurant_data.columns:
        area_list = restaurant_data['Area'].unique().tolist()
    else:
        area_list = ['Koramangala', 'Indiranagar', 'HSR Layout', 'Whitefield', 'Marathahalli', 
                     'Jayanagar', 'JP Nagar', 'Electronic City', 'Rajajinagar', 'Malleshwaram']
    
    init_donor_files()
    
    # Create tabs
    tab1, tab2 = st.tabs(["📝 Post New Donation", "📋 My Donation History"])
    
    # ==================== TAB 1: POST NEW DONATION ====================
    with tab1:
        st.subheader("📝 Post New Food Donation")
        st.info("Fill the details below. The donation will appear in the NGO dashboard immediately!")
        
        with st.form("donation_form"):
            col1, col2 = st.columns(2)
            with col1:
                restaurant_name = st.text_input("Restaurant Name*", value=st.session_state['username'])
                food_name = st.text_input("Food Name*", placeholder="Example: French Fries, Vegetable Biryani")
            with col2:
                quantity = st.number_input("Quantity (kg)*", min_value=0.5, step=0.5, help="Total weight of food")
                expiry_hours = st.slider("Expires in (hours)*", 1, 24, 4, help="How long until food expires?")
            
            donor_area = st.selectbox("Select Your Area*", area_list)
            restaurant_contact = st.text_input("Restaurant Contact Number*", value=st.session_state['mobile'])
            
            st.caption("⏰ Food with shorter expiry (2-4 hours) will be marked as HIGH priority")
            
            submitted = st.form_submit_button("Next: Set Pickup Location →", type="primary")
            
            if submitted:
                if all([restaurant_name, food_name, quantity, donor_area, restaurant_contact]):
                    st.session_state['temp_donation'] = {
                        'restaurant_name': restaurant_name,
                        'food_name': food_name,
                        'quantity': quantity,
                        'expiry_hours': expiry_hours,
                        'donor_area': donor_area,
                        'restaurant_contact': restaurant_contact
                    }
                    st.session_state['show_location'] = True
                    st.rerun()
                else:
                    st.error("Please fill all fields")
        
        # Location picker
        if st.session_state.get('show_location', False):
            st.markdown("---")
            st.info(f"📍 Setting pickup location for: **{st.session_state['temp_donation']['food_name']}**")
            
            lat, lon, address = show_location_picker()
            
            if lat and lon:
                st.success("✅ Location set successfully!")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Post Donation", type="primary", use_container_width=True):
                        with st.spinner("Posting donation..."):
                            donation_id, _ = post_donation(
                                st.session_state['temp_donation']['restaurant_name'],
                                st.session_state['temp_donation']['food_name'],
                                st.session_state['temp_donation']['quantity'],
                                st.session_state['temp_donation']['expiry_hours'],
                                lat, lon, address,
                                st.session_state['temp_donation']['restaurant_contact'],
                                st.session_state['temp_donation']['donor_area']
                            )
                            
                            st.success(f"✅ Donation posted successfully!")
                            st.success(f"📦 Donation ID: {donation_id}")
                            
                            st.info("📢 NGOs can now see this donation in their dashboard!")
                            st.balloons()
                            
                            for key in ['temp_donation', 'show_location']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()
                
                with col2:
                    if st.button("❌ Cancel", use_container_width=True):
                        for key in ['temp_donation', 'show_location']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
    
    # ==================== TAB 2: DONATION HISTORY ====================
    with tab2:
        st.subheader("📋 Your Donation History")
        
        if os.path.exists(DONATIONS_FILE) and os.path.getsize(DONATIONS_FILE) > 0:
            df = pd.read_csv(DONATIONS_FILE)
            restaurant_donations = df[df['restaurant_name'] == st.session_state['username']]
            
            if len(restaurant_donations) > 0:
                # Summary stats
                total_food = restaurant_donations['quantity_kg'].sum()
                pending = len(restaurant_donations[restaurant_donations['status'] == 'pending'])
                accepted = len(restaurant_donations[restaurant_donations['status'] == 'accepted'])
                completed = len(restaurant_donations[restaurant_donations['status'] == 'completed'])
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Donations", len(restaurant_donations))
                col2.metric("Total Food (kg)", f"{total_food:.0f}")
                col3.metric("Pending", pending)
                col4.metric("Completed", completed)
                
                st.markdown("---")
                
                # Show each donation
                for _, donation in restaurant_donations.iterrows():
                    if donation['status'] == 'pending':
                        status_icon = "🟡"
                        status_text = "Waiting for NGO to accept"
                    elif donation['status'] == 'accepted':
                        status_icon = "🟢"
                        status_text = f"Accepted by {donation['accepted_by']}"
                    else:
                        status_icon = "✅"
                        status_text = "Completed - Food Collected"
                    
                    with st.expander(f"{status_icon} {donation['food_name']} - {donation['quantity_kg']} kg - {status_text}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Quantity", f"{donation['quantity_kg']} kg")
                            st.metric("Expires in", f"{donation['expiry_hours']} hours")
                        
                        with col2:
                            st.metric("Posted", donation['posted_at'][:16])
                            st.metric("Area", donation['area'])
                        
                        with col3:
                            st.metric("Status", donation['status'].upper())
                            if donation['status'] == 'accepted':
                                st.metric("Accepted By", donation['accepted_by'][:20])
                        
                        st.write(f"**📍 Pickup Location:**")
                        st.write(f"{donation['address'][:200]}")
                        st.write(f"**📞 Your Contact:** {donation['restaurant_contact']}")
                        
                        if donation['status'] == 'accepted':
                            st.success(f"✅ {donation['accepted_by']} has accepted your donation! They will arrive soon to collect the food.")
                        elif donation['status'] == 'pending':
                            st.info("⏳ Waiting for an NGO to accept... The donation is visible in the NGO dashboard.")
                        elif donation['status'] == 'completed':
                            st.success("🎉 Donation completed! Thank you for reducing food waste!")
            else:
                st.info("📭 No donations posted yet. Go to 'Post New Donation' tab to share food!")
        else:
            st.info("📭 No donations posted yet. Go to 'Post New Donation' tab to share food!")

def init():
    """Initialize donor dashboard"""
    init_donor_files()

if __name__ == "__main__":
    if "authenticated" not in st.session_state or st.session_state.get("role") != "donor":
        st.warning("Please login as Restaurant/Donor")
        st.stop()
    
    init()
    show_donor_dashboard()