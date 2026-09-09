#!/usr/bin/env python3
"""
WordPress Setup Script for Parent Data Force
Sets up custom post types and theme configuration
"""

import requests
import json
import base64
from wp_config import WP_API_URL, WP_USERNAME, WP_APPLICATION_PASSWORD

class WordPressSetup:
    def __init__(self):
        self.api_url = WP_API_URL
        self.username = WP_USERNAME
        self.password = WP_APPLICATION_PASSWORD
        self.auth_header = self._create_auth_header()
    
    def _create_auth_header(self):
        """Create authentication header for WordPress REST API"""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded_credentials}"}
    
    def create_custom_post_types(self):
        """Instructions for creating custom post types"""
        cpt_instructions = """
Custom Post Types Needed:
1. Cases (/cases/)
2. Districts (/districts/)
3. Resources (/resources/)
4. Appearances (/appearances/)

These require a plugin like "Custom Post Type UI" to be installed and activated in WordPress.
After installing the plugin, you can register these CPTs through the WordPress admin interface.

Alternatively, add this code to your theme's functions.php:

function create_parentdataforce_post_types() {
    // Cases Post Type
    register_post_type('cases', array(
        'labels' => array(
            'name' => 'Cases',
            'singular_name' => 'Case'
        ),
        'public' => true,
        'has_archive' => true,
        'rewrite' => array('slug' => 'cases'),
        'supports' => array('title', 'editor', 'excerpt', 'thumbnail')
    ));
    
    // Districts Post Type
    register_post_type('districts', array(
        'labels' => array(
            'name' => 'Districts',
            'singular_name' => 'District'
        ),
        'public' => true,
        'has_archive' => true,
        'rewrite' => array('slug' => 'districts'),
        'supports' => array('title', 'editor', 'excerpt', 'thumbnail')
    ));
    
    // Resources Post Type
    register_post_type('resources', array(
        'labels' => array(
            'name' => 'Resources',
            'singular_name' => 'Resource'
        ),
        'public' => true,
        'has_archive' => true,
        'rewrite' => array('slug' => 'resources'),
        'supports' => array('title', 'editor', 'excerpt', 'thumbnail')
    ));
    
    // Appearances Post Type
    register_post_type('appearances', array(
        'labels' => array(
            'name' => 'Appearances',
            'singular_name' => 'Appearance'
        ),
        'public' => true,
        'has_archive' => true,
        'rewrite' => array('slug' => 'appearances'),
        'supports' => array('title', 'editor', 'excerpt', 'thumbnail')
    ));
}
add_action('init', 'create_parentdataforce_post_types');
"""
        print(cpt_instructions)
        return True
    
    def setup_theme_options(self):
        """Set up theme options and settings"""
        theme_settings = {
            "blogname": "Parent Data Force",
            "blogdescription": "Data-driven advocacy for families. Tracking complaints, records, outcomes, and systemic patterns across Massachusetts districts.",
            "admin_email": "admin@parentdataforce.com",
            "timezone_string": "America/New_York",
            "default_comment_status": "closed",
            "default_ping_status": "closed"
        }
        
        print("Theme settings to configure in WordPress:")
        for key, value in theme_settings.items():
            print(f"  {key}: {value}")
        
        return True
    
    def create_navigation_menus(self):
        """Create navigation menu structure"""
        menus = {
            "Primary Menu": [
                {"title": "Data", "url": "/data/"},
                {"title": "Districts", "url": "/districts/"},
                {"title": "Current Focus", "url": "/cases/"},
                {"title": "Articles", "url": "/articles/"},
                {"title": "Appearances", "url": "/appearances/"},
                {"title": "Resources", "url": "/resources/"},
                {"title": "About", "url": "/about/"},
                {"title": "Submit Data", "url": "/submit/"},
                {"title": "Donate", "url": "/donate/"}
            ],
            "Footer Menu": [
                {"title": "Articles", "url": "/articles/"},
                {"title": "Case Directory", "url": "/cases/"},
                {"title": "Districts", "url": "/districts/"},
                {"title": "Data Browser", "url": "/data/"},
                {"title": "Appearances", "url": "/appearances/"},
                {"title": "Updates", "url": "/updates/"},
                {"title": "Submit a Tip", "url": "/submit/"},
                {"title": "Request Help", "url": "/submit/#help"},
                {"title": "Upload Data", "url": "/submit/#upload"},
                {"title": "About Us", "url": "/about/"},
                {"title": "Privacy Policy", "url": "/about/#privacy"}
            ]
        }
        
        print("\nNavigation menus to create in WordPress:")
        for menu_name, items in menus.items():
            print(f"\n{menu_name}:")
            for item in items:
                print(f"  - {item['title']}: {item['url']}")
        
        return True
    
    def setup_branding_options(self):
        """Set up branding and color scheme options"""
        branding = {
            "colors": {
                "primary_background": "#0b0b0b",
                "secondary_background": "#161616",
                "accent_color": "#ff5a1f",
                "accent_glow": "#ffa366",
                "text_primary": "#f5f5f5",
                "text_secondary": "#a0a0a0",
                "text_muted": "#767676"
            },
            "typography": {
                "primary_font": "Inter",
                "monospace_font": "JetBrains Mono"
            }
        }
        
        print("\nBranding options for theme customization:")
        print(json.dumps(branding, indent=2))
        return True

def main():
    """Main setup function"""
    setup = WordPressSetup()
    
    print("Setting up WordPress for Parent Data Force...")
    print("=" * 50)
    
    # Create custom post types
    print("\n1. Custom Post Types:")
    setup.create_custom_post_types()
    
    # Set up theme options
    print("\n2. Theme Settings:")
    setup.setup_theme_options()
    
    # Create navigation menus
    print("\n3. Navigation Menus:")
    setup.create_navigation_menus()
    
    # Set up branding
    print("\n4. Branding Options:")
    setup.setup_branding_options()
    
    print("\n" + "=" * 50)
    print("WordPress setup instructions complete!")
    print("Please implement these settings in your WordPress installation.")

if __name__ == "__main__":
    main()