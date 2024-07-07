import json
import openai

with open("pathPatterns/equipment_property_pairs.json", encoding='utf-8') as f:
    data = json.load(f)

# Choose random pattern from data

# Get LLM to generate several humanised sentences for the pattern
