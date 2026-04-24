import streamlit as st
import pandas as pd
import os
from route_optimizer import show_optimized_route_map
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

DONATIONS_FILE = "data/donations.csv"

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def load_donations():
    """Load all donations from CSV"""
    try:
        if os.path.exists(DONATIONS_FILE) and os.path.getsize(DONATIONS_FILE) > 0:
            df = pd.read_csv(DONATIONS_FILE)
            return df.to_dict('records')
        return []
    except:
        return []

def save_donations(donations):
    """Save all donations to CSV"""
    df = pd.DataFrame(donations)
    # Ensure all string columns are properly formatted
    if 'donation_id' in df.columns:
        df['donation_id'] = df['donation_id'].astype(str)
    if 'restaurant_name' in df.columns:
        df['restaurant_name'] = df['restaurant_name'].astype(str)
    if 'food_name' in df.columns:
        df['food_name'] = df['food_name'].astype(str)
    if 'address' in df.columns:
        df['address'] = df['address'].astype(str)
    if 'restaurant_contact' in df.columns:
        df['restaurant_contact'] = df['restaurant_contact'].astype(str)
    if 'area' in df.columns:
        df['area'] = df['area'].astype(str)
    if 'status' in df.columns:
        df['status'] = df['status'].astype(str)
    if 'accepted_by' in df.columns:
        df['accepted_by'] = df['accepted_by'].astype(str)
    if 'accepted_at' in df.columns:
        df['accepted_at'] = df['accepted_at'].astype(str)
    if 'posted_at' in df.columns:
        df['posted_at'] = df['posted_at'].astype(str)
    df.to_csv(DONATIONS_FILE, index=False)

def get_pending_donations():
    """Get only pending donations"""
    all_donations = load_donations()
    return [d for d in all_donations if d.get('status') == 'pending']

def get_all_ngos():
    """Get all NGOs with their details"""
    return [
        {'name': 'Feeding India - Koramangala', 'phone': '9353239332', 'lat': 12.9352, 'lon': 77.6245},
        {'name': 'Robin Hood Army - Koramangala', 'phone': '3591869024', 'lat': 12.9355, 'lon': 77.6248},
        {'name': 'Akshaya Patra - Koramangala', 'phone': '9845905314', 'lat': 12.9360, 'lon': 77.6252},
        {'name': 'Goonj - Koramangala', 'phone': '9844195520', 'lat': 12.9345, 'lon': 77.6240},
        {'name': 'Hasiru Dala - Koramangala', 'phone': '9353239332', 'lat': 12.9358, 'lon': 77.6255},
    ]

def get_max_allowed_distance(expiry_hours):
    if expiry_hours <= 2:
        return 3.0
    elif expiry_hours <= 4:
        return 5.0
    elif expiry_hours <= 6:
        return 8.0
    else:
        return 12.0

def get_nearby_ngos_for_donation(restaurant_lat, restaurant_lon, all_ngos, expiry_hours):
    """Find NGOs within smart distance"""
    max_distance = get_max_allowed_distance(expiry_hours)
    ngos_with_distance = []
    
    for ngo in all_ngos:
        dist = haversine(restaurant_lat, restaurant_lon, ngo['lat'], ngo['lon'])
        if dist <= max_distance:
            ngos_with_distance.append({
                'name': ngo['name'],
                'phone': ngo['phone'],
                'lat': ngo['lat'],
                'lon': ngo['lon'],
                'distance_km': dist
            })
    
    return sorted(ngos_with_distance, key=lambda x: x['distance_km']), max_distance

def accept_donation(donation_id, ngo_name, ngo_phone, ngo_lat, ngo_lon, restaurant_lat, restaurant_lon):
    """Accept a donation - removes from list for all NGOs"""
    all_donations = load_donations()
    
    for donation in all_donations:
        if donation.get('donation_id') == donation_id and donation.get('status') == 'pending':
            donation['status'] = 'accepted'
            donation['accepted_by'] = ngo_name
            donation['accepted_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_donations(all_donations)
            
            road_dist = haversine(ngo_lat, ngo_lon, restaurant_lat, restaurant_lon)
            
            st.session_state['accepted_donation'] = {
                'id': donation_id,
                'restaurant_name': donation['restaurant_name'],
                'food_name': donation['food_name'],
                'restaurant_lat': float(donation['latitude']),
                'restaurant_lon': float(donation['longitude']),
                'restaurant_address': donation['address'],
                'quantity': donation['quantity_kg'],
                'expiry': donation['expiry_hours'],
                'restaurant_contact': donation['restaurant_contact'],
                'ngo_name': ngo_name,
                'ngo_phone': ngo_phone,
                'ngo_lat': ngo_lat,
                'ngo_lon': ngo_lon,
                'distance': road_dist
            }
            
            return True, f"✅ {ngo_name} accepted the donation!"
    
    return False, "Donation already taken!"

def complete_donation(donation_id):
    """Mark donation as completed"""
    all_donations = load_donations()
    
    for donation in all_donations:
        if donation.get('donation_id') == donation_id:
            donation['status'] = 'completed'
            save_donations(all_donations)
            return True
    return False

def get_urgency_message(expiry_hours):
    if expiry_hours <= 2:
        return "🔴 CRITICAL - Food expires in 2 hours! Only NGOs within 3 km"
    elif expiry_hours <= 4:
        return "🟡 HIGH - Food expires in 4 hours. NGOs within 5 km"
    elif expiry_hours <= 6:
        return "🟠 MEDIUM - Food expires in 6 hours. NGOs within 8 km"
    else:
        return "🟢 NORMAL - NGOs within 12 km"

def show_donation_list():
    """Show the list of available donations with NGOs"""
    
    pending_donations = get_pending_donations()
    all_ngos = get_all_ngos()
    
    if not pending_donations:
        st.info("📭 No food donations available at the moment.")
        return
    
    for donation in pending_donations:
        st.markdown("---")
        st.markdown(f"## 🍽️ {donation['food_name']}")
        
        expiry_hours = int(donation['expiry_hours'])
        
        if expiry_hours <= 2:
            st.error("🔴 CRITICAL - Food expires in 2 hours!")
        elif expiry_hours <= 4:
            st.warning("🟡 HIGH URGENCY - Food expires in 4 hours")
        elif expiry_hours <= 6:
            st.info("🟠 MEDIUM URGENCY - Food expires in 6 hours")
        else:
            st.info("🟢 Normal urgency")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            **Restaurant:** {donation['restaurant_name']}  
            **Quantity:** {donation['quantity_kg']} kg  
            **Expires in:** {donation['expiry_hours']} hours
            """)
        
        with col2:
            st.markdown(f"""
            **📍 Pickup Location:**  
            {donation['address'][:100]}  
            **📞 Restaurant Contact:** {donation['restaurant_contact']}
            """)
        
        st.markdown("---")
        
        restaurant_lat = float(donation['latitude'])
        restaurant_lon = float(donation['longitude'])
        
        nearby_ngos, max_distance = get_nearby_ngos_for_donation(
            restaurant_lat, restaurant_lon, all_ngos, expiry_hours
        )
        
        st.info(get_urgency_message(expiry_hours))
        
        if not nearby_ngos:
            st.warning(f"⚠️ No NGOs found within {max_distance} km")
            continue
        
        st.subheader(f"📢 NGOs Within {max_distance} km")
        
        for ngo in nearby_ngos:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            with col1:
                st.markdown(f"**🏢 {ngo['name']}**")
            with col2:
                st.markdown(f"📞 {ngo['phone']}")
            with col3:
                st.markdown(f"🚗 {ngo['distance_km']:.1f} km away")
            with col4:
                if st.button(f"✅ Accept", key=f"accept_{donation['donation_id']}_{ngo['name'].replace(' ', '_')}", use_container_width=True):
                    success, message = accept_donation(
                        donation['donation_id'],
                        ngo['name'],
                        ngo['phone'],
                        ngo['lat'],
                        ngo['lon'],
                        restaurant_lat,
                        restaurant_lon
                    )
                    
                    if success:
                        st.success(message)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)
            
            st.markdown("---")

def show_route_for_accepted_donation():
    """Show route for accepted donation"""
    
    if st.session_state.get('accepted_donation') is None:
        return
    
    donation = st.session_state['accepted_donation']
    
    st.markdown("## 🗺️ Your Route to Collect Food")
    st.markdown(f"### 🍽️ {donation['food_name']} from {donation['restaurant_name']}")
    st.info(f"**Claimed by:** {donation['ngo_name']}")
    st.caption(f"🚗 Driving distance: {donation['distance']:.1f} km")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"📦 **Quantity:** {donation['quantity']} kg")
    with col2:
        if donation['expiry'] <= 2:
            st.error(f"⏰ **Expires in:** {donation['expiry']} hours - URGENT!")
        else:
            st.warning(f"⏰ **Expires in:** {donation['expiry']} hours")
    with col3:
        st.success(f"📞 **Restaurant Contact:** {donation['restaurant_contact']}")
    
    show_optimized_route_map(
        donation['ngo_lat'],
        donation['ngo_lon'],
        donation['restaurant_lat'],
        donation['restaurant_lon'],
        donation['restaurant_name']
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Mark as Collected", use_container_width=True, type="primary"):
            if complete_donation(donation['id']):
                st.success("🎉 Donation marked as collected! Food waste reduced!")
                st.balloons()
                st.session_state['accepted_donation'] = None
                st.rerun()
            else:
                st.error("Error completing donation")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            all_donations = load_donations()
            for donation_item in all_donations:
                if donation_item.get('donation_id') == donation['id']:
                    donation_item['status'] = 'pending'
                    donation_item['accepted_by'] = ''
                    donation_item['accepted_at'] = ''
                    save_donations(all_donations)
                    break
            st.info("Acceptance cancelled. Donation is available again.")
            st.session_state['accepted_donation'] = None
            st.rerun()

def show_stats():
    """Show statistics"""
    all_donations = load_donations()
    
    if all_donations:
        total = len(all_donations)
        completed = len([d for d in all_donations if d.get('status') == 'completed'])
        pending = len([d for d in all_donations if d.get('status') == 'pending'])
        accepted = len([d for d in all_donations if d.get('status') == 'accepted'])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Donations", total)
        col2.metric("Completed", completed)
        col3.metric("Available", pending)
        col4.metric("In Progress", accepted)
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Donations", "0")
        col2.metric("Completed", "0")
        col3.metric("Available", "0")
        col4.metric("In Progress", "0")

def show_public_ngo_dashboard():
    """Main NGO dashboard"""
    
    if 'accepted_donation' not in st.session_state:
        st.session_state['accepted_donation'] = None
    
    st.title("🏢 NGO Food Collection Dashboard")
    st.markdown("### First Come, First Serve!")
    st.markdown("---")
    
    st.info("""
    📢 **Smart Distance Filter:**
    - **0-2 hours** → NGOs within 3 km
    - **2-4 hours** → NGOs within 5 km
    - **4-6 hours** → NGOs within 8 km
    - **6+ hours** → NGOs within 12 km
    
    Click Accept next to your NGO name to claim a donation.
    """)
    
    st.markdown("---")
    
    if st.session_state['accepted_donation'] is None:
        show_donation_list()
    else:
        show_route_for_accepted_donation()
    
    if st.session_state['accepted_donation'] is None:
        st.markdown("---")
        st.subheader("📊 Impact Statistics")
        show_stats()

if __name__ == "__main__":
    show_public_ngo_dashboard()