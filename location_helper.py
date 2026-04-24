import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

def search_any_location(search_term):
    """Search any location - works like Google Maps"""
    if not search_term:
        return None, None, None
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": search_term,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }
    headers = {"User-Agent": "FoodRedistributionApp/1.0"}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        results = response.json()
        
        if results:
            first = results[0]
            return float(first["lat"]), float(first["lon"]), first.get("display_name", "")
        return None, None, None
    except:
        return None, None, None

def get_address_from_coordinates(lat, lon):
    """Get address from coordinates"""
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "json"}
    headers = {"User-Agent": "FoodRedistributionApp/1.0"}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        return data.get("display_name", f"Lat: {lat:.4f}, Lon: {lon:.4f}")
    except:
        return f"Lat: {lat:.4f}, Lon: {lon:.4f}"

def show_location_picker():
    """Interactive location picker for restaurants"""
    
    st.subheader("📍 Set Your Restaurant Pickup Location")
    
    # Search box
    search_term = st.text_input(
        "🔍 Search your restaurant location:",
        placeholder="Example: MG Road, Bangalore or Koramangala",
        key="search_input"
    )
    
    # Initialize session state
    if 'map_center_lat' not in st.session_state:
        st.session_state.map_center_lat = 12.9716
        st.session_state.map_center_lon = 77.5946
        st.session_state.map_zoom = 12
    
    # Search button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔍 Search", key="search_btn", use_container_width=True):
            if search_term:
                with st.spinner("Searching..."):
                    lat, lon, address = search_any_location(search_term)
                    if lat:
                        st.session_state.map_center_lat = lat
                        st.session_state.map_center_lon = lon
                        st.session_state.map_zoom = 16
                        st.session_state['donor_lat'] = lat
                        st.session_state['donor_lon'] = lon
                        st.session_state['donor_address'] = address
                        st.success(f"✅ Found: {address[:100]}...")
                        st.rerun()
                    else:
                        st.error("Location not found. Try adding area name.")
    
    st.markdown("---")
    st.markdown("### 🗺️ Confirm Your Location")
    st.caption("📍 Click on map to adjust if needed")
    
    # Create map
    m = folium.Map(
        location=[st.session_state.map_center_lat, st.session_state.map_center_lon],
        zoom_start=st.session_state.map_zoom,
        tiles='OpenStreetMap'
    )
    
    # Add marker
    if 'donor_lat' in st.session_state:
        folium.Marker(
            [st.session_state['donor_lat'], st.session_state['donor_lon']],
            popup="📍 Restaurant Location",
            icon=folium.Icon(color="red", icon="cutlery", prefix="fa")
        ).add_to(m)
    
    # Display map
    map_data = st_folium(m, width=700, height=400, key="location_map")
    
    # Handle click
    if map_data and map_data.get("last_clicked"):
        clicked = map_data["last_clicked"]
        st.session_state['donor_lat'] = clicked["lat"]
        st.session_state['donor_lon'] = clicked["lng"]
        st.session_state['donor_address'] = get_address_from_coordinates(clicked["lat"], clicked["lng"])
        st.success("📍 Location updated!")
        st.rerun()
    
    # Show current location
    if 'donor_lat' in st.session_state:
        st.markdown("---")
        st.markdown("**📍 Selected Location:**")
        st.write(f"📌 {st.session_state.get('donor_address', 'Location selected')[:200]}")
        st.write(f"📐 Coordinates: {st.session_state['donor_lat']:.6f}, {st.session_state['donor_lon']:.6f}")
        
        return st.session_state['donor_lat'], st.session_state['donor_lon'], st.session_state.get('donor_address', '')
    
    return None, None, None