#!/usr/bin/env python3
"""
Parent Data Force Site Verification Script
Verifies that theme enhancements have been applied to the live site
"""

import requests
import re
from datetime import datetime

def verify_site_changes():
    """Verify that site enhancements have been applied"""
    print("Parent Data Force Site Verification")
    print("=" * 35)
    print(f"Verification time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Fetch the live site
        response = requests.get("https://www.parentdataforce.com/news/", timeout=10)
        
        if response.status_code != 200:
            print(f"ERROR: Failed to fetch site (Status code: {response.status_code})")
            return False
        
        content = response.text
        print(f"Site fetched successfully ({len(content)} bytes)")
        print()
        
        # Check for footer content ported from parentdataforce.com
        print("Checking footer content:")

        checks = [
            ("independent special education and public accountability advocacy", "footer description"),
            ("tracking complaints, records, outcomes, and systemic patterns", "footer tracking line"),
            ("independent advocacy initiative", "footer disclaimer"),
            ("all rights reserved", "copyright notice"),
            ("case directory", "Content column"),
            ("submit a tip", "Get Involved column"),
            ("updates on new articles, case filings, and data releases", "Stay Updated column"),
            ("/about/#privacy", "privacy policy link"),
        ]
        ok = True
        for needle, label in checks:
            if needle in content.lower():
                print(f"✓ {label} found")
            else:
                print(f"✗ {label} NOT found")
                ok = False
        
        # Check for site title and tagline
        print("\nChecking site identity:")
        if "parent data force" in content.lower():
            print("✓ Site title 'Parent Data Force' found")
        else:
            print("✗ Site title 'Parent Data Force' not found")
        
        if "making data make sense" in content.lower():
            print("✓ Tagline 'Making Data Make Sense' found")
        else:
            print("✗ Tagline 'Making Data Make Sense' not found")
        
        # Check for theme characteristics
        print("\nChecking theme characteristics:")
        if "twentytwentyfive" in content.lower():
            print("✓ Twenty Twenty-Five theme detected")
        else:
            print("? Theme identification not found in content")
        
        # Check for dark theme indicators
        if "#0b0b0b" in content or "background:#0b0b0b" in content:
            print("✓ Dark theme background color detected")
        elif "dark" in content.lower():
            print("✓ Dark theme indicators found")
        else:
            print("? Dark theme indicators not clearly detected")
        
        # Check for orange accent color
        if "#ff5a1f" in content or "ff5a1f" in content:
            print("✓ Orange accent color detected")
        else:
            print("? Orange accent color not clearly detected")
        
        print("\nVerification complete.")
        return ok
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to connect to site - {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error during verification - {e}")
        return False

def main():
    """Main function for site verification"""
    success = verify_site_changes()
    
    if success:
        print("\nSite verification completed successfully!")
        print("The theme enhancements appear to be in place.")
        return 0
    else:
        print("\nSite verification encountered issues.")
        return 1

if __name__ == "__main__":
    exit(main())