#!/usr/bin/env python3
"""
Demonstration Script for Parent Data Force WordPress Manager Skill
Shows how to use the Oh My Pi skill capabilities
"""

import json
from wp import WPApiClient
from upload_theme import ThemeUploader
from migrate_parentdataforce import ContentMigration
from monitor_health import SiteHealthMonitor
from backup_restore import WordPressBackupRestore
import wp_config

def demo_theme_management():
    """Demonstrate theme management capabilities"""
    print("=== Theme Management Demo ===")
    
    # Initialize WordPress client
    wp_client = WPApiClient(
        base_url=wp_config.WP_URL,
        username=wp_config.WP_USERNAME,
        password=wp_config.WP_PASSWORD
    )
    
    # Initialize theme uploader
    theme_uploader = ThemeUploader(wp_client)
    
    # Validate theme structure
    print("Validating theme structure...")
    is_valid = theme_uploader.validate_theme_structure("./themes/parentdataforce")
    print(f"Theme validation result: {'PASS' if is_valid else 'FAIL'}")
    
    # In a real implementation, you would also demonstrate:
    # - Theme upload
    # - Theme activation
    # - Theme update
    # - Theme deletion
    
    print("Theme management demo completed.\n")

def demo_content_migration():
    """Demonstrate content migration capabilities"""
    print("=== Content Migration Demo ===")
    
    # Initialize WordPress client
    wp_client = WPApiClient(
        base_url=wp_config.WP_URL,
        username=wp_config.WP_USERNAME,
        password=wp_config.WP_PASSWORD
    )
    
    # Initialize content migration
    migration = ContentMigration(wp_client, wp_config.STATIC_SITE_PATH)
    
    # Generate content inventory (without actually migrating)
    print("Generating content inventory...")
    # This is just a demonstration - in practice, you would have static files
    print("Content inventory would be generated from static site files.")
    
    print("Content migration demo completed.\n")

def demo_rest_api_interactions():
    """Demonstrate REST API interaction capabilities"""
    print("=== REST API Interactions Demo ===")
    
    # Initialize WordPress client
    wp_client = WPApiClient(
        base_url=wp_config.WP_URL,
        username=wp_config.WP_USERNAME,
        password=wp_config.WP_PASSWORD
    )
    
    # Demonstrate getting posts
    print("Retrieving recent posts...")
    try:
        posts = wp_client.get_posts(per_page=5)
        print(f"Retrieved {len(posts)} posts")
        if posts:
            print(f"Latest post: {posts[0].get('title', {}).get('rendered', 'Untitled')}")
    except Exception as e:
        print(f"Error retrieving posts: {e}")
    
    # Demonstrate creating a draft post
    print("Creating a test draft post...")
    try:
        new_post = wp_client.create_post(
            title="Test Post from Oh My Pi Skill",
            content="This post was created using the Parent Data Force WordPress Manager skill for Oh My Pi.",
            status="draft"
        )
        print(f"Created draft post with ID: {new_post.get('id', 'Unknown')}")
    except Exception as e:
        print(f"Error creating post: {e}")
    
    print("REST API interactions demo completed.\n")

def demo_site_health_monitoring():
    """Demonstrate site health monitoring capabilities"""
    print("=== Site Health Monitoring Demo ===")
    
    # Initialize health monitor
    monitor = SiteHealthMonitor()
    
    # Run availability check
    print("Checking site availability...")
    availability = monitor.check_site_availability()
    print(f"Site status: {availability.get('status', 'Unknown')}")
    if availability.get('response_time'):
        print(f"Response time: {availability['response_time']} seconds")
    
    print("Site health monitoring demo completed.\n")

def demo_backup_restore():
    """Demonstrate backup and restore capabilities"""
    print("=== Backup and Restore Demo ===")
    
    # Initialize backup manager
    backup_manager = WordPressBackupRestore()
    
    # List existing backups
    print("Listing available backups...")
    backups = backup_manager.list_backups()
    print(f"Found {len(backups)} backups")
    for backup in backups[:3]:  # Show first 3
        print(f"  - {backup['name']} ({backup['date']})")
    
    print("Backup and restore demo completed.\n")

def main():
    """Main demonstration function"""
    print("Parent Data Force WordPress Manager Skill - Demo")
    print("=" * 50)
    print("This script demonstrates the capabilities of the Oh My Pi skill.")
    print()
    
    # Run all demos
    demo_theme_management()
    demo_content_migration()
    demo_rest_api_interactions()
    demo_site_health_monitoring()
    demo_backup_restore()
    
    print("All demonstrations completed successfully!")
    print("\nTo use the full capabilities of the Oh My Pi skill:")
    print("1. Load the parentdataforce-wordpress.agent file in Oh My Pi")
    print("2. Configure the WordPress connection settings")
    print("3. Use the defined actions to manage your WordPress site")

if __name__ == "__main__":
    main()