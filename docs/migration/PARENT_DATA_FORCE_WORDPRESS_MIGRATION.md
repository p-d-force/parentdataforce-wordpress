# Parent Data Force WordPress Migration Documentation

## Project Overview

This document provides a complete guide for migrating the Parent Data Force static website to a dynamic WordPress platform. The migration preserves all existing content while adding powerful content management capabilities, improved maintainability, and enhanced functionality.

## Contents

1. [Migration Plan Summary](#migration-plan-summary)
2. [Technical Architecture](#technical-architecture)
3. [Implementation Files](#implementation-files)
4. [Installation Instructions](#installation-instructions)
5. [Content Migration Process](#content-migration-process)
6. [Theme Customization](#theme-customization)
7. [Testing and Validation](#testing-and-validation)
8. [Deployment](#deployment)

## Migration Plan Summary

The migration involves transforming a static HTML website into a fully functional WordPress site with:

- Custom theme implementing the dark/orange branding
- Custom post types for cases, districts, resources, and appearances
- REST API integration for content management
- Responsive design compatible with all devices
- Data visualization capabilities using Chart.js

## Technical Architecture

### WordPress Setup Requirements

- WordPress 5.0 or higher
- PHP 7.4 or higher
- MySQL 5.7 or higher
- HTTPS support (recommended)

### Custom Post Types

1. **Cases** - For tracking legal cases and investigations
2. **Districts** - For district profiles and analytics
3. **Resources** - For guides, documents, and educational materials
4. **Appearances** - For media appearances and public comments

### Theme Features

- Dark theme with orange accent colors (#0b0b0b background, #ff5a1f accents)
- Responsive design for mobile, tablet, and desktop
- Custom navigation menus
- Data visualization support
- SEO optimization
- Accessibility compliance

## Implementation Files

The following files have been created to facilitate the migration:

### Configuration Files
- `wp_config.py` - WordPress API configuration
- `docker-compose.yml` - Docker setup for local development

### Migration Scripts
- `migrate_parentdataforce.py` - Main content migration script
- `setup_wordpress.py` - WordPress setup helper
- `requirements.txt` - Python dependencies

### WordPress Theme Files
- `themes/parentdataforce/` - Complete custom theme directory
  - `style.css` - Theme styles and metadata
  - `functions.php` - Theme functionality and custom post types
  - `index.php` - Main template
  - `header.php` - Header template
  - `footer.php` - Footer template
  - `front-page.php` - Homepage template
  - `page.php` - Page template
  - `single.php` - Single post template
  - `archive.php` - Archive template
  - `template-parts/content.php` - Content template part
  - `screenshot.txt` - Theme screenshot placeholder
  - `readme.txt` - Theme documentation

### Documentation
- `parentdataforce_migration_plan.md` - Detailed migration plan
- `wordpress_setup_guide.md` - WordPress installation guide
- `PARENT_DATA_FORCE_WORDPRESS_MIGRATION.md` - This document

## Installation Instructions

### Option 1: Docker Development Environment (Recommended)

1. Install Docker Desktop
2. Navigate to the project directory
3. Run `docker-compose up -d`
4. Access WordPress at http://localhost:8080
5. Access phpMyAdmin at http://localhost:8081

### Option 2: Manual Installation

1. Install a local development environment (XAMPP, WAMP, MAMP)
2. Download and install WordPress
3. Create a database for WordPress
4. Run the WordPress installation wizard

### WordPress Configuration

1. Install required plugins:
   - Custom Post Type UI
   - Advanced Custom Fields
   - Application Passwords
   - WP REST API Controller (optional)

2. Activate the Parent Data Force theme:
   - Copy the `themes/parentdataforce` directory to `wp-content/themes/`
   - Activate the theme in WordPress Admin > Appearance > Themes

3. Register custom post types:
   - Using Custom Post Type UI plugin, or
   - Add the code from `functions.php` to your theme's functions.php

4. Create Application Password:
   - Go to Users > Profile
   - Generate an application password for API access
   - Update `wp_config.py` with the credentials

## Content Migration Process

### Prerequisites

1. WordPress installation with custom theme and post types
2. Application password for REST API access
3. Python 3.7+ with required packages

### Migration Steps

1. Update `wp_config.py` with your WordPress site URL and credentials
2. Run the migration script:
   ```bash
   pip install -r requirements.txt
   python migrate_parentdataforce.py
   ```

### Migration Script Functions

The migration script performs the following operations:

1. **Create Key Pages** - About, Cases, Districts, Resources, Submit Data, Donate, Appearances
2. **Create Homepage** - With hero section and featured content
3. **Migrate Articles** - Convert static articles to WordPress posts
4. **Upload Media** - Transfer images and other media assets
5. **Set Up Navigation** - Create menus and menu items

### Handling Migration Errors

If you encounter connection errors:
1. Verify WordPress is running and accessible
2. Check the URL in `wp_config.py`
3. Confirm Application Password is correct
4. Ensure REST API is enabled

## Theme Customization

### Color Scheme

The theme implements the Parent Data Force branding:

- Primary Background: #0b0b0b
- Secondary Background: #161616
- Accent Color: #ff5a1f
- Accent Glow: #ffa366
- Text Primary: #f5f5f5
- Text Secondary: #a0a0a0
- Text Muted: #767676

### Typography

- Primary Font: Inter (Google Fonts)
- Monospace Font: JetBrains Mono (Google Fonts)

### Customization Options

1. **Header Customization**
   - Site logo
   - Navigation menus
   - Social media links

2. **Homepage Sections**
   - Hero section
   - Featured articles
   - Quick links
   - Statistics

3. **Content Areas**
   - Articles grid
   - Resource cards
   - Case studies
   - District profiles

### Adding Custom Functionality

1. **Widgets** - Add to sidebar or footer areas
2. **Shortcodes** - Create custom content elements
3. **Custom Fields** - Add metadata to posts
4. **Data Visualizations** - Implement Chart.js charts

## Testing and Validation

### Pre-Migration Testing

1. Backup all static site files
2. Document all content types and structures
3. Identify all media assets
4. Catalog all internal and external links

### During Migration Testing

1. Verify content integrity after migration
2. Test all navigation links
3. Validate responsive design
4. Check data visualization functionality

### Post-Migration Testing

1. Test search functionality
2. Verify form submissions
3. Check social media integration
4. Validate SEO metadata
5. Performance testing

### Quality Assurance Checklist

- [ ] All content successfully migrated with preserved formatting
- [ ] Improved site performance and loading times
- [ ] Enhanced mobile responsiveness
- [ ] Maintained branding and visual identity
- [ ] Functional search and navigation
- [ ] Proper categorization of content types

## Deployment

### Production Deployment Steps

1. **Prepare Production Environment**
   - Set up hosting with WordPress support
   - Configure domain and SSL certificate
   - Create production database

2. **Deploy WordPress**
   - Install WordPress on production server
   - Configure wp-config.php with production settings
   - Install and activate required plugins

3. **Deploy Theme**
   - Upload custom theme to production
   - Activate theme in WordPress Admin

4. **Migrate Content**
   - Update wp_config.py with production credentials
   - Run migration script against production site
   - Verify all content is properly migrated

5. **Configure Settings**
   - Set up navigation menus
   - Configure permalinks
   - Set reading settings
   - Configure SEO settings

6. **Final Testing**
   - Test all pages and functionality
   - Verify cross-browser compatibility
   - Check mobile responsiveness
   - Validate performance metrics

### Maintenance Considerations

1. **Regular Updates**
   - WordPress core updates
   - Plugin updates
   - Theme updates
   - Security patches

2. **Backups**
   - Automated backup scheduling
   - Offsite backup storage
   - Regular restore testing

3. **Performance Monitoring**
   - Page load speed monitoring
   - Uptime monitoring
   - Traffic analytics

4. **Security**
   - Regular security audits
   - Malware scanning
   - User access management

## Troubleshooting Common Issues

### REST API Connection Errors

- Verify WordPress URL in wp_config.py
- Check that REST API is enabled
- Confirm Application Password is correct
- Ensure user has proper permissions

### Permission Issues

- Make sure the WordPress user has editor or administrator role
- Check that custom post types are registered correctly
- Verify Application Password has been generated

### Media Upload Failures

- Check upload folder permissions
- Increase PHP memory limit if needed
- Verify file size limits in PHP configuration

## Conclusion

This migration transforms the Parent Data Force static website into a powerful, manageable WordPress platform while preserving all existing content and branding. The new system provides:

- Enhanced content management capabilities
- Improved maintainability
- Better performance and SEO
- Mobile-responsive design
- Data visualization features
- Scalable architecture

With the provided files and documentation, the migration can be completed efficiently while maintaining the organization's distinctive brand identity and advocacy mission.