import os
import requests
import json
import re

LEMLIST_API_KEY = "8fad96626dca907a8b2bb5a3e7da45d2"
BASE_URL = "https://api.lemlist.com/api"

headers = {
    "Authorization": f"Basic {LEMLIST_API_KEY}",
    "Content-Type": "application/json"
}

def create_campaign(name):
    resp = requests.post(f"{BASE_URL}/campaigns", auth=("", LEMLIST_API_KEY), json={"name": name})
    if resp.status_code in [200, 201]:
        return resp.json().get("_id")
    else:
        print(f"Error creating campaign: {resp.text}")
        return None

def add_step_to_campaign(campaign_id, subject, body, day_delay):
    payload = {
        "type": "email",
        "delay": day_delay,
        "subject": subject,
        "html": body.replace('\n', '<br>')
    }
    resp = requests.post(f"{BASE_URL}/campaigns/{campaign_id}/steps", auth=("", LEMLIST_API_KEY), json=payload)
    if resp.status_code in [200, 201]:
        print(f"  -> Added step: {subject} (Day {day_delay})")
    else:
        print(f"  -> Error adding step: Status {resp.status_code} - {resp.text}")

def parse_markdown_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    emails = []
    # Splitting by "## Email x — "
    parts = re.split(r"## Email \d+ — Dag (\d+)[^\n]*", content)
    
    # parts[0] is the header text
    # then follows [day, body, day, body, ...]
    for i in range(1, len(parts), 2):
        day = int(parts[i])
        block = parts[i+1]
        
        # Extract the first Subject variant (Variant A)
        subj_match = re.search(r"- A: `([^`]+)`", block)
        subject = subj_match.group(1) if subj_match else "Follow-up"
        
        # Extract body
        body_match = re.search(r"\*\*Body:\*\*(.*?)(?=---|\Z)", block, re.DOTALL)
        body = body_match.group(1).strip() if body_match else ""
        
        emails.append({
            "day": day,
            "subject": subject,
            "body": body
        })
    return emails

if __name__ == "__main__":
    email_file = "/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/scripts/vacaturekanon/vacaturekanon/m5-email-sequences/sequence-meta-inbound.md"
    
    print("Parsing Markdown...")
    emails = parse_markdown_file(email_file)
    
    camp_id = create_campaign("VK-META-INBOUND")
    if not camp_id:
        # Check if campaign already exists
        resp = requests.get(f"{BASE_URL}/campaigns", auth=("", LEMLIST_API_KEY))
        if resp.status_code == 200:
            for c in resp.json():
                if c.get("name") == "VK-META-INBOUND":
                    camp_id = c.get("_id")
                    print(f"Campaign already exists. ID: {camp_id}")
                    break

    if camp_id:
        print(f"Adding {len(emails)} steps...")
        # Sort just in case
        emails.sort(key=lambda x: x["day"])
        
        # Lemlist API expects the delay to be relative to the previous step (in days or hours).
        # We need to calculate the relative day difference.
        prev_day = 0
        for i, email in enumerate(emails):
            # The FIRST email in Lemlist typically has delay 0. Subsequent emails have relative delay.
            # Day 0 relative = 0. Day 2 relative to Day 0 = 2. Day 5 relative to Day 2 = 3.
            relative_delay = email['day'] - prev_day
            if i == 0:
                relative_delay = 0 # first step is always day 0
            
            # Since relative_delay is given directly to "delay" field which usually is in days (or minutes).
            # The API doc says: "delay" between steps.
            add_step_to_campaign(camp_id, email['subject'], email['body'], relative_delay)
            prev_day = email['day']
            
    print("Done!")
