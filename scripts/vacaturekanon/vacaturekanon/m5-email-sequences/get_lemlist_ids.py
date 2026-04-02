import requests

LEMLIST_API_KEY = "8fad96626dca907a8b2bb5a3e7da45d2"
BASE_URL = "https://api.lemlist.com/api"

def create_or_get_campaign(name):
    auth = ("", LEMLIST_API_KEY)
    # Check if exists
    resp = requests.get(f"{BASE_URL}/campaigns", auth=auth)
    if resp.status_code == 200:
        for c in resp.json():
            if c.get("name") == name:
                return c.get("_id")
                
    # Create if not exists
    resp = requests.post(f"{BASE_URL}/campaigns", auth=auth, json={"name": name})
    if resp.status_code in [200, 201]:
        return resp.json().get("_id")
    return None

if __name__ == "__main__":
    chaser_id = create_or_get_campaign("VK-INTAKE-CHASER")
    onboarding_id = create_or_get_campaign("VK-ONBOARDING")
    
    print(f"INTAKE_CHASER_ID={chaser_id}")
    print(f"ONBOARDING_ID={onboarding_id}")
