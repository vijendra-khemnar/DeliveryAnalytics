#!/usr/bin/env python3
"""
Perplexity API Setup Script for Delivery Analytics System

This script helps configure the Perplexity API key for enhanced AI features.
"""

import os
from pathlib import Path

def setup_perplexity_api():
    """Interactive setup for Perplexity API configuration"""
    
    print("🤖 Perplexity AI Integration Setup")
    print("=" * 50)
    print("\nThis script will help you configure Perplexity AI for enhanced")
    print("natural language processing in the delivery analytics system.")
    
    # Check if .env file exists
    env_file = Path('.env')
    
    if env_file.exists():
        print(f"\n✅ Found existing .env file")
        with open(env_file, 'r') as f:
            content = f.read()
            if 'PERPLEXITY_API_KEY=' in content:
                if 'your_perplexity_api_key_here' not in content:
                    print("🔧 Perplexity API key appears to be already configured")
                    choice = input("Would you like to update it? (y/N): ").strip().lower()
                    if choice != 'y':
                        return
    
    # Get API key from user
    print("\n📋 Please provide your Perplexity API key:")
    print("You can get one from: https://www.perplexity.ai/settings/api")
    
    api_key = input("\nEnter your Perplexity API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Setup cancelled.")
        return
    
    # Update .env file
    try:
        if env_file.exists():
            # Read existing content
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # Update or add API key
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('PERPLEXITY_API_KEY='):
                    lines[i] = f'PERPLEXITY_API_KEY={api_key}\n'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'\nPERPLEXITY_API_KEY={api_key}\n')
            
            # Write back
            with open(env_file, 'w') as f:
                f.writelines(lines)
        else:
            print("❌ .env file not found. Please run from the project directory.")
            return
        
        print("\n✅ Perplexity API key configured successfully!")
        print("\n🚀 Enhanced Features Available:")
        print("   • Advanced natural language query understanding")
        print("   • AI-generated contextual recommendations") 
        print("   • Executive summary generation")
        print("   • Improved entity extraction and intent classification")
        
        print("\n📋 Next Steps:")
        print("1. Install required dependencies: pip install -r requirements.txt")
        print("2. Run the system: python delivery_root_cause_analyzer.py")
        print("3. Try complex queries like:")
        print('   "Compare delivery performance between top cities during festival season"')
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        print("Please manually add this line to your .env file:")
        print(f"PERPLEXITY_API_KEY={api_key}")

def main():
    setup_perplexity_api()

if __name__ == "__main__":
    main()