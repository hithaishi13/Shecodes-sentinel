import os
import pandas as pd

# Create data folder
os.makedirs("data", exist_ok=True)

# Create empty donations file
donations_df = pd.DataFrame(columns=[
    "donation_id", "restaurant_name", "food_name", "quantity_kg", 
    "expiry_hours", "latitude", "longitude", "address",
    "restaurant_contact", "area", "status", "posted_at"
])
donations_df.to_csv("data/donations.csv", index=False)

# Create empty users file
users_df = pd.DataFrame(columns=[
    "user_id", "username", "email", "mobile", "password_hash", 
    "role", "registered_at"
])
users_df.to_csv("data/users.csv", index=False)

print("✅ Setup complete! Folders and files created.")
print("📁 Created: data/donations.csv")
print("📁 Created: data/users.csv")
print("\n🚀 Run: python -m streamlit run app.py")