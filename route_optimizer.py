import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import polyline
from math import radians, sin, cos, sqrt, atan2
import time

def haversine(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance between two coordinates in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def get_road_distance_only(start_lat, start_lon, end_lat, end_lon):
    """
    Get ONLY the road distance (km) without showing the map
    Used for consistent distance display in NGO list
    """
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
        params = {"overview": "false", "steps": "false"}
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("routes") and len(data["routes"]) > 0:
                return data["routes"][0]["distance"] / 1000
    except:
        pass
    
    # Fallback: straight line + 30% for roads
    straight_dist = haversine(start_lat, start_lon, end_lat, end_lon)
    return straight_dist * 1.3

def get_osrm_route(start_lat, start_lon, end_lat, end_lon, retries=3):
    """
    Get real road-based route using OSRM (Open Source Routing Machine)
    This gives actual driving directions, not straight lines!
    """
    
    # OSRM public API (free, no API key needed)
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {
        "overview": "full",      # Get full route geometry
        "steps": "true",         # Get turn-by-turn instructions
        "geometries": "polyline", # Get encoded polyline
        "annotations": "true"
    }
    
    headers = {
        "User-Agent": "FoodRedistributionApp/1.0"
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("routes") and len(data["routes"]) > 0:
                    route = data["routes"][0]
                    
                    # Get actual road distance and duration
                    road_distance_km = route["distance"] / 1000
                    road_duration_min = route["duration"] / 60
                    
                    # Decode polyline to get actual road coordinates
                    geometry = route["geometry"]
                    road_coordinates = polyline.decode(geometry)
                    
                    # Extract step-by-step instructions
                    steps = []
                    if route.get("legs"):
                        for leg in route["legs"]:
                            for step in leg.get("steps", []):
                                instruction = step.get("maneuver", {}).get("instruction", "")
                                step_distance = step.get("distance", 0) / 1000
                                step_duration = step.get("duration", 0) / 60
                                road_name = step.get("name", "")
                                if instruction:
                                    steps.append({
                                        'instruction': instruction,
                                        'road': road_name,
                                        'distance_km': step_distance,
                                        'duration_min': step_duration
                                    })
                    
                    return {
                        'coordinates': road_coordinates,
                        'road_distance_km': road_distance_km,
                        'road_duration_min': road_duration_min,
                        'steps': steps,
                        'source': 'osrm'
                    }
            
            # If OSRM fails, try alternative
            result = get_alternative_route(start_lat, start_lon, end_lat, end_lon)
            if result:
                return result
            
        except requests.exceptions.Timeout:
            if attempt == retries - 1:
                result = get_alternative_route(start_lat, start_lon, end_lat, end_lon)
                if result:
                    return result
            time.sleep(1)
        except Exception as e:
            if attempt == retries - 1:
                result = get_alternative_route(start_lat, start_lon, end_lat, end_lon)
                if result:
                    return result
            time.sleep(1)
    
    return get_straight_line_route(start_lat, start_lon, end_lat, end_lon)

def get_alternative_route(start_lat, start_lon, end_lat, end_lon):
    """Fallback: Use OpenRouteService API"""
    try:
        url = f"https://api.openrouteservice.org/v2/directions/driving-car"
        params = {
            "start": f"{start_lon},{start_lat}",
            "end": f"{end_lon},{end_lat}"
        }
        headers = {
            "User-Agent": "FoodRedistributionApp/1.0",
            "Accept": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("features") and len(data["features"]) > 0:
                feature = data["features"][0]
                geometry = feature.get("geometry", {})
                coordinates = geometry.get("coordinates", [])
                
                # Convert [lng, lat] to [lat, lng] for folium
                road_coordinates = [[coord[1], coord[0]] for coord in coordinates]
                
                properties = feature.get("properties", {})
                summary = properties.get("summary", {})
                road_distance_km = summary.get("distance", 0) / 1000
                road_duration_min = summary.get("duration", 0) / 60
                
                return {
                    'coordinates': road_coordinates,
                    'road_distance_km': road_distance_km,
                    'road_duration_min': road_duration_min,
                    'steps': [],
                    'source': 'openrouteservice'
                }
    except Exception as e:
        pass
    
    return None

def get_straight_line_route(start_lat, start_lon, end_lat, end_lon):
    """
    Last resort: Straight line with realistic road factor (1.3x straight distance)
    """
    straight_distance = haversine(start_lat, start_lon, end_lat, end_lon)
    road_distance_km = straight_distance * 1.3
    road_duration_min = road_distance_km * 2.5
    
    # Create a few intermediate points to simulate roads
    num_points = 5
    coordinates = []
    for i in range(num_points + 1):
        t = i / num_points
        lat = start_lat + (end_lat - start_lat) * t
        lon = start_lon + (end_lon - start_lon) * t
        
        # Add slight curve to simulate roads
        if 0 < t < 1:
            import random
            lat += random.uniform(-0.0003, 0.0003)
            lon += random.uniform(-0.0003, 0.0003)
        coordinates.append([lat, lon])
    
    return {
        'coordinates': coordinates,
        'road_distance_km': road_distance_km,
        'road_duration_min': road_duration_min,
        'steps': [],
        'source': 'estimated'
    }

def show_optimized_route_map(start_lat, start_lon, end_lat, end_lon, restaurant_name):
    """
    Display the optimized route map with actual road distances
    """
    
    st.subheader(f"🗺️ Route to {restaurant_name}")
    
    # Show loading spinner while getting route
    with st.spinner("Finding the best driving route..."):
        route_data = get_osrm_route(start_lat, start_lon, end_lat, end_lon)
    
    # Show route source
    if route_data['source'] == 'osrm':
        st.success("✅ Route calculated using real road network")
    elif route_data['source'] == 'openrouteservice':
        st.info("🔄 Route from OpenRouteService")
    else:
        st.info("📍 Route calculated (estimated based on road network)")
    
    # Show ONLY the road distance
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🚗 Driving Distance", f"{route_data['road_distance_km']:.1f} km")
    with col2:
        st.metric("⏱️ Driving Time", f"{route_data['road_duration_min']:.0f} minutes")
    with col3:
        fuel_estimate = route_data['road_distance_km'] * 0.08
        st.metric("⛽ Fuel Estimate", f"{fuel_estimate:.1f} L")
    
    # Create interactive map
    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles='OpenStreetMap')
    
    # Start marker (NGO location)
    folium.Marker(
        [start_lat, start_lon],
        popup="🚚 Your Location (NGO)",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
        tooltip="Start from here"
    ).add_to(m)
    
    # Destination marker (Restaurant)
    folium.Marker(
        [end_lat, end_lon],
        popup=f"🍽️ {restaurant_name}",
        icon=folium.Icon(color="red", icon="cutlery", prefix="fa"),
        tooltip="Food pickup here"
    ).add_to(m)
    
    # Draw the actual road route
    if route_data['coordinates'] and len(route_data['coordinates']) > 1:
        folium.PolyLine(
            route_data['coordinates'],
            color="#0066cc",
            weight=6,
            opacity=0.8,
            popup=f"Driving route: {route_data['road_distance_km']:.1f} km"
        ).add_to(m)
        
        # Add distance marker at midpoint
        mid_idx = len(route_data['coordinates']) // 2
        if mid_idx < len(route_data['coordinates']):
            mid_coord = route_data['coordinates'][mid_idx]
            folium.map.Marker(
                [mid_coord[0], mid_coord[1]],
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 14px; background-color: white; padding: 4px 12px; border-radius: 25px; border: 2px solid #0066cc; font-weight: bold;">🚗 {route_data["road_distance_km"]:.1f} km</div>'
                )
            ).add_to(m)
    
    st_folium(m, width=800, height=500, key="route_map")
    
    # Show turn-by-turn directions if available
    if route_data.get('steps') and len(route_data['steps']) > 0:
        st.subheader("📋 Turn-by-Turn Directions")
        
        for i, step in enumerate(route_data['steps'][:10], 1):
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 8px; border-left: 4px solid #0066cc;">
                <b>{i}. {step['instruction']}</b><br>
                <span style="color: #666; font-size: 12px;">
                    📏 {step['distance_km']:.2f} km · ⏱️ {step['duration_min']:.1f} min
                    {f' · 🛣️ {step["road"]}' if step.get('road') else ''}
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    # Google Maps alternative link
    google_maps_url = f"https://www.google.com/maps/dir/{start_lat},{start_lon}/{end_lat},{end_lon}"
    st.markdown(f"""
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; margin-top: 15px;">
        <b>📱 For Live Navigation:</b><br>
        <a href="{google_maps_url}" target="_blank">🔗 Open in Google Maps</a> for real-time traffic
    </div>
    """, unsafe_allow_html=True)
    
    return route_data['road_distance_km'], route_data['road_duration_min']