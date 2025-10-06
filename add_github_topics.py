#!/usr/bin/env python3
"""
Script to add required GitHub topics for HACS validation.
"""
import json
import requests
import os
import sys

def add_github_topics():
    """Add required topics to the GitHub repository."""
    
    # Repository details
    owner = "swavans"
    repo = "home-assistant-marstek-local-api"
    
    # Required topics for HACS
    topics = [
        "home-assistant",
        "hacs", 
        "integration",
        "marstek",
        "local-api",
        "battery",
        "solar",
        "energy-management"
    ]
    
    # GitHub API endpoint
    url = f"https://api.github.com/repos/{owner}/{repo}/topics"
    
    # You'll need to set this environment variable with your GitHub token
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        print("Please create a personal access token at: https://github.com/settings/tokens")
        print("Then run: export GITHUB_TOKEN=your_token_here")
        return False
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.mercy-preview+json",  # Required for topics API
        "Content-Type": "application/json"
    }
    
    data = {
        "names": topics
    }
    
    try:
        response = requests.put(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            print(f"✅ Successfully added topics: {', '.join(topics)}")
            return True
        else:
            print(f"❌ Failed to add topics. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Adding GitHub topics for HACS validation...")
    if add_github_topics():
        print("\n✅ Topics added successfully!")
        print("You can verify the topics at: https://github.com/swavans/home-assistant-marstek-local-api")
    else:
        print("\n❌ Failed to add topics. Please add them manually through GitHub web interface:")
        print("1. Go to https://github.com/swavans/home-assistant-marstek-local-api")
        print("2. Click the gear icon next to 'About'")
        print("3. Add these topics: home-assistant, hacs, integration, marstek, local-api, battery, solar, energy-management")
        sys.exit(1)