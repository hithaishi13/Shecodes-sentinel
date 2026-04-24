import pandas as pd
import os
from datetime import datetime

NOTIFICATION_LOG = "data/notifications_log.csv"

def init_notification_log():
    """Initialize notification log file"""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(NOTIFICATION_LOG) or os.path.getsize(NOTIFICATION_LOG) == 0:
        df = pd.DataFrame(columns=[
            "notification_id", "donation_id", "ngo_name", "ngo_phone", 
            "restaurant_name", "food_name", "quantity_kg", "notified_at"
        ])
        df.to_csv(NOTIFICATION_LOG, index=False)

def log_notification(donation_id, ngo_name, ngo_phone, restaurant_name, food_name, quantity):
    """Log notification sent to NGO"""
    init_notification_log()
    
    df = pd.read_csv(NOTIFICATION_LOG)
    
    new_log = pd.DataFrame([{
        "notification_id": f"NOT{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "donation_id": donation_id,
        "ngo_name": ngo_name,
        "ngo_phone": ngo_phone,
        "restaurant_name": restaurant_name,
        "food_name": food_name,
        "quantity_kg": quantity,
        "notified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    
    updated = pd.concat([df, new_log], ignore_index=True)
    updated.to_csv(NOTIFICATION_LOG, index=False)

def get_notification_history():
    """Get all notification history"""
    if os.path.exists(NOTIFICATION_LOG) and os.path.getsize(NOTIFICATION_LOG) > 0:
        return pd.read_csv(NOTIFICATION_LOG)
    return pd.DataFrame()