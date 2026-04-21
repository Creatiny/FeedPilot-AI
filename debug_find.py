#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from skills.price_lookup_skill.skill import PriceLookupSkill

skill = PriceLookupSkill()

# Debug _find_ingredient step by step
msg = "price of Fish meal"
msg_lower = msg.lower()

print(f"Message: {msg}")
print(f"Message lower: {msg_lower}")
print()

# Check keyword matching
for keyword in skill.INGREDIENT_KEYWORDS:
    if keyword.lower() in msg_lower:
        print(f"  KEYWORD MATCH: '{keyword}' found in '{msg_lower}'")
        break
else:
    print("  No keyword match found")

# Check regex pattern
import re
match = re.search(r'(?:price\s+(?:of\s+)?|(.+?)\s+price)', msg, re.IGNORECASE)
if match:
    print(f"  REGEX MATCH: group(0)='{match.group(0)}', group(1)='{match.group(1)}'")
    name = match.group(1) if match.group(1) else match.group(0)
    name = name.replace('price', '').replace('of', '').strip()
    print(f"  Extracted name: '{name}'")
else:
    print("  No regex match")

# Now test "price of Corn" which works
print()
msg2 = "price of Corn"
msg2_lower = msg2.lower()
print(f"Message: {msg2}")
for keyword in skill.INGREDIENT_KEYWORDS:
    if keyword.lower() in msg2_lower:
        print(f"  KEYWORD MATCH: '{keyword}' found in '{msg2_lower}'")
        break
else:
    print("  No keyword match found")
