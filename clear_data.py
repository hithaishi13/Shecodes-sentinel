import os

# Delete old donations file
if os.path.exists("data/donations.csv"):
    os.remove("data/donations.csv")
    print("✅ Old donations cleared!")
else:
    print("No file to delete")

# Create fresh donations file
import pandas as pd
os.makedirs("data", exist_ok=True)
df = pd.DataFrame(columns=[
    "donation_id", "restaurant_name", "food_name", "quantity_kg", 
    "expiry_hours", "latitude", "longitude", "address",
    "restaurant_contact", "area", "status", "accepted_by", "accepted_at", "posted_at"
])
df.to_csv("data/donations.csv", index=False)
print("✅ New donations file created!")