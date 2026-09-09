# Parent Data Force WordPress Migration - Implementation Instructions

## Overview

This document provides step-by-step instructions for implementing the WordPress migration of the Parent Data Force website using the files provided in this package.

## Prerequisites

Before starting the implementation, ensure you have:

1. Python 3.7 or higher installed
2. Docker Desktop (recommended) or a local WordPress development environment
3. Basic understanding of WordPress administration
4. Access to a WordPress hosting environment for production deployment

## Step 1: Set Up Development Environment

### Option A: Using Docker (Recommended)

1. Install Docker Desktop from https://www.docker.com/products/docker-desktop
2. Navigate to the project directory in your terminal
3. Run the following command to start the WordPress environment:
   ```
   docker-compose up -d
   ```
4. Access WordPress at http://localhost:8080
5. Complete the WordPress installation wizard
6. Access phpMyAdmin at http://localhost:8081 (optional, for database management)

### Option B: Manual Installation

1. Install a local development environment:
   - Windows: XAMPP (https://www.apachefriends.org/index.html)
   - Mac: MAMP (https://www.mamp.info/en/)
   - Linux: LAMP stack
2. Download WordPress from https://wordpress.org/latest.zip
3. Extract to your web server directory
4. Create a database for WordPress
5. Run the WordPress installation at http://localhost/your-wordpress-directory

## Step 2: Configure WordPress

### Install Required Plugins

1. Log in to WordPress Admin at http://localhost:8080/wp-admin (or your local URL)
2. Go to Plugins > Add New
3. Install and activate the following plugins:
   - Custom Post Type UI
   - Advanced Custom Fields
   - Application Passwords
   - WP REST API Controller (optional)

### Activate the Parent Data Force Theme

1. Copy the `themes/parentdataforce` directory to your WordPress installation's `wp-content/themes/` directory
2. Go to Appearance > Themes in WordPress Admin
3. Activate the "Parent Data Force" theme

### Register Custom Post Types

Option 1: Using Custom Post Type UI Plugin
1. Go to CPT UI > Add New
2. Register each custom post type as documented in `wordpress_setup_guide.md`

Option 2: Code Registration
1. Add the custom post type code from `themes/parentdataforce/functions.php` to your theme's functions.php file

### Create Application Password

1. Go to Users > Profile
2. Scroll to the "Application Passwords" section
3. Enter "ParentDataForce Migration" as the name
4. Click "Add New Application Password"
5. Save the generated password securely

## Step 3: Configure Migration Script

1. Open `wp_config.py` in a text editor
2. Update the following values:
   ```python
   WP_API_URL = "http://localhost:8080/wp-json/wp/v2"  # Your WordPress REST API URL
   WP_USERNAME = "your_admin_username"  # Your WordPress admin username
   WP_APPLICATION_PASSWORD = "your_generated_app_password"  # The password generated in Step 2
   ```
3. Save the file

## Step 4: Install Python Dependencies

1. Open a terminal/command prompt
2. Navigate to the project directory
3. Run:
   ```
   pip install -r requirements.txt
   ```

## Step 5: Run Content Migration

1. Ensure your WordPress development environment is running
2. In the terminal, run:
   ```
   python migrate_parentdataforce.py
   ```
3. The script will:
   - Create key pages (About, Cases, Districts, etc.)
   - Create the homepage
   - Migrate articles as WordPress posts
   - Set up basic navigation

Note: If you encounter connection errors, verify:
- WordPress is running and accessible
- The URL in `wp_config.py` is correct
- The Application Password is correct
- The user has proper permissions

## Step 6: Manual Configuration

### Set Up Navigation Menus

1. Go to Appearance > Menus in WordPress Admin
2. Create a "Primary Menu" with the following items:
   - Data (URL: /data/)
   - Districts (URL: /districts/)
   - Current Focus (URL: /cases/)
   - Articles (URL: /articles/)
   - Appearances (URL: /appearances/)
   - Resources (URL: /resources/)
   - About (URL: /about/)
   - Submit Data (URL: /submit/)
   - Donate (URL: /donate/)

3. Create a "Footer Menu" with appropriate links

### Configure Homepage

1. Go to Settings > Reading
2. Set "Front page displays" to "A static page"
3. Select "Home" as the front page
4. Optionally select a page for posts

### Customize Theme (Optional)

1. Go to Appearance > Customize
2. Adjust colors, typography, and other settings as needed
3. Add site logo and favicon

## Step 7: Test the Implementation

1. Visit the homepage and verify the design
2. Navigate through all pages
3. Check that articles are properly displayed
4. Verify mobile responsiveness
5. Test search functionality (may require additional configuration)

## Step 8: Production Deployment

### Prepare Production Environment

1. Set up hosting with WordPress support
2. Configure domain and SSL certificate
3. Create production database

### Deploy WordPress

1. Upload WordPress files to production server
2. Import the development database or run fresh installation
3. Update `wp-config.php` with production database settings

### Deploy Theme

1. Upload the `themes/parentdataforce` directory to production `wp-content/themes/`
2. Activate the theme in WordPress Admin

### Migrate Content to Production

Option 1: Re-run migration script
1. Update `wp_config.py` with production credentials
2. Run `python migrate_parentdataforce.py`

Option 2: Export/import content
1. In development WordPress, go to Tools > Export
2. Export all content
3. In production WordPress, go to Tools > Import
4. Install WordPress importer plugin if needed
5. Import the exported content

### Final Configuration

1. Set up navigation menus in production
2. Configure permalink settings
3. Set reading settings
4. Configure SEO settings if using an SEO plugin
5. Test all functionality

## Troubleshooting Common Issues

### Connection Errors During Migration

- Verify WordPress is running and accessible
- Check the URL in `wp_config.py`
- Confirm Application Password is correct
- Ensure user has proper permissions

### Missing Custom Post Types

- Verify Custom Post Type UI plugin is installed and activated
- Check that custom post types are registered correctly
- Ensure the theme's functions.php contains the CPT registration code

### Theme Not Appearing Correctly

- Verify all theme files are uploaded correctly
- Check that the theme is activated
- Clear any caching plugins
- Verify file permissions

### Performance Issues

- Install a caching plugin like WP Super Cache
- Optimize images before uploading
- Use a Content Delivery Network (CDN)
- Implement lazy loading for images

## Maintenance Recommendations

1. **Regular Updates**
   - Keep WordPress core updated
   - Update plugins and themes regularly
   - Monitor security advisories

2. **Backups**
   - Implement automated backup solution
   - Store backups in multiple locations
   - Regularly test backup restoration

3. **Security**
   - Use strong passwords
   - Implement two-factor authentication
   - Install a security plugin
   - Regularly scan for malware

4. **Performance Monitoring**
   - Monitor page load speeds
   - Use tools like Google PageSpeed Insights
   - Optimize database regularly

## Support and Further Development

For ongoing maintenance and enhancements:

1. Refer to the documentation files in this package
2. Consult WordPress developer resources
3. Consider hiring a WordPress developer for complex customizations
4. Join WordPress community forums for support

## Conclusion

Following these instructions will successfully migrate the Parent Data Force static website to a dynamic WordPress platform while preserving the organization's distinctive branding and content. The new system provides enhanced content management capabilities, improved maintainability, and better performance while maintaining the advocacy mission of the organization.