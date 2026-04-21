#!/usr/bin/env python3
# Check if "rice" is in "price of fish meal"
msg = "price of fish meal"
print(f"'rice' in '{msg}': {'rice' in msg}")
print(f"'rice' in '{msg.lower()}': {'rice' in msg.lower()}")

# Find where
idx = msg.lower().find('rice')
print(f"Found at index: {idx}")
print(f"Context: '{msg[idx-3:idx+5]}'")

# Same for other keywords
for kw in ["Corn", "Soybean meal", "Fish meal", "Wheat", "Barley", "Rice",
           "DDGS", "Canola meal", "Cottonseed meal", "Dicalcium phosphate",
           "Limestone", "Salt", "L-Lysine", "DL-Methionine", "Premix",
           "Alfalfa", "Corn silage", "Grass hay", "Molasses"]:
    if kw.lower() in msg.lower():
        print(f"  '{kw}' matches in '{msg}'")
