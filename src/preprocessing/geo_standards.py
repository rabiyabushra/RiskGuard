"""Geographic standardization module for RiskGuard.

Normalizes State and District naming variations across PAIMANA, Census,
RBI Power, Courts, and MoRTH Road datasets into canonical keys.
"""

import re

STATE_CANONICAL_MAP = {
    # Andhra Pradesh
    "andhra pradesh": "Andhra Pradesh",
    "andhra pradesh(*)": "Andhra Pradesh",
    # Arunachal Pradesh
    "arunachal pradesh": "Arunachal Pradesh",
    "arunachal pradesh $": "Arunachal Pradesh",
    # Assam
    "assam": "Assam",
    # Bihar
    "bihar": "Bihar",
    # Chhattisgarh
    "chhattisgarh": "Chhattisgarh",
    "chhatisgarh": "Chhattisgarh",
    # Goa
    "goa": "Goa",
    # Gujarat
    "gujarat": "Gujarat",
    # Haryana
    "haryana": "Haryana",
    # Himachal Pradesh
    "himachal pradesh": "Himachal Pradesh",
    # Jammu and Kashmir
    "jammu & kashmir": "Jammu & Kashmir",
    "jammu and kashmir": "Jammu & Kashmir",
    # Jharkhand
    "jharkhand": "Jharkhand",
    # Karnataka
    "karnataka": "Karnataka",
    # Kerala
    "kerala": "Kerala",
    # Madhya Pradesh
    "madhya pradesh": "Madhhya Pradesh",
    "madhya pradesh": "Madhya Pradesh",
    # Maharashtra
    "maharashtra": "Maharashtra",
    # Manipur
    "manipur": "Manipur",
    # Meghalaya
    "meghalaya": "Meghalaya",
    # Mizoram
    "mizoram": "Mizoram",
    # Nagaland
    "nagaland": "Nagaland",
    # Odisha
    "odisha": "Odisha",
    "orissa": "Odisha",
    # Punjab
    "punjab": "Punjab",
    # Rajasthan
    "rajasthan": "Rajasthan",
    # Sikkim
    "sikkim": "Sikkim",
    # Tamil Nadu
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    # Telangana
    "telangana": "Telangana",
    # Tripura
    "tripura": "Tripura",
    # Uttar Pradesh
    "uttar pradesh": "Uttar Pradesh",
    # Uttarakhand
    "uttarakhand": "Uttarakhand",
    "uttaranchal": "Uttarakhand",
    # West Bengal
    "west bengal": "West Bengal",
    # Union Territories
    "andaman & nicobar islands": "Andaman & Nicobar Islands",
    "andaman and nicobar islands": "Andaman & Nicobar Islands",
    "andaman and nicobar islands (ut)": "Andaman & Nicobar Islands",
    "chandigarh": "Chandigarh",
    "chandigarh (ut)": "Chandigarh",
    "dadra & nagar haveli": "Dadra & Nagar Haveli and Daman & Diu",
    "dadra and nagar haveli": "Dadra & Nagar Haveli and Daman & Diu",
    "daman & diu": "Dadra & Nagar Haveli and Daman & Diu",
    "daman and diu": "Dadra & Nagar Haveli and Daman & Diu",
    "dadra and nagar haveli and daman and diu": "Dadra & Nagar Haveli and Daman & Diu",
    "delhi": "Delhi",
    "nct of delhi": "Delhi",
    "delhi (ut)": "Delhi",
    "ladakh": "Ladakh",
    "lakshadweep": "Lakshadweep",
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
}

def standardize_state(raw_state: str) -> str:
    """Normalize a state string to its canonical title-cased representation."""
    if not raw_state or not isinstance(raw_state, str):
        return "Unknown"
    
    s = raw_state.strip()
    # Check if multi-state
    if "multi" in s.lower() or "," in s:
        return "Multi-States"
    
    # Strip footnotes (*), ($) and digits
    s_clean = re.sub(r'[\*\$\d\(\)]', '', s).strip().lower()
    s_clean = re.sub(r'\s+', ' ', s_clean)
    
    if s_clean in STATE_CANONICAL_MAP:
        return STATE_CANONICAL_MAP[s_clean]
    
    # Capitalize words as fallback
    return s_clean.title()

def standardize_district(raw_district: str) -> str:
    """Normalize a district string to lowercase stripped format."""
    if not raw_district or not isinstance(raw_district, str):
        return "unknown"
    d = raw_district.strip().lower()
    d = re.sub(r'[^a-z0-9\s]', '', d)
    d = re.sub(r'\s+', ' ', d).strip()
    return d
