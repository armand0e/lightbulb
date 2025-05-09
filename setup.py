#!/usr/bin/env python3

import os
import sys

def create_config(path, token):
    """Create a config.py file with the provided token."""
    with open(path, 'w') as f:
        f.write(f'DISCORD_BOT_TOKEN="{token}"')
    print(f"Created config at {path}")

def main():
    print("Setting up Discord bot configurations...")
    
    # Prompt for Blackbulb token
    blackbulb_token = input("Enter the Discord token for Blackbulb: ").strip()
    
    # Prompt for Lightbulb token
    lightbulb_token = input("Enter the Discord token for Lightbulb: ").strip()
    
    # Create the config files
    create_config("blackbulb/config.py", blackbulb_token)
    create_config("lightbulb/config.py", lightbulb_token)
    
    print("\nSetup complete!")
    print("You can now run the bots using `docker compose up -d`")

if __name__ == "__main__":
    main()
