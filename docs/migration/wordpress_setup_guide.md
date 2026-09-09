# WordPress Installation and Setup Guide for Parent Data Force

## Prerequisites

Before installing WordPress, ensure you have the following:

1. A web server (Apache, Nginx, or IIS)
2. PHP version 7.4 or greater
3. MySQL version 5.7 or greater OR MariaDB version 10.2 or greater
4. HTTPS support (recommended)

## Installation Methods

### Option 1: Local Development Environment

For local development, you can use:

1. **XAMPP** (Windows/Mac/Linux)
2. **WAMP** (Windows)
3. **MAMP** (Mac)
4. **Local by Flywheel** (WordPress-specific)
5. **Docker** with WordPress image

### Option 2: Manual Installation

1. Download WordPress from [wordpress.org](https://wordpress.org/latest.zip)
2. Extract the files to your web server directory
3. Create a database for WordPress
4. Run the installation script by navigating to your site in a browser

## Step-by-Step Installation Using XAMPP (Windows)

1. **Download and Install XAMPP**
   - Visit https://www.apachefriends.org/index.html
   - Download the Windows version
   - Run the installer with default settings

2. **Start Apache and MySQL Services**
   - Open XAMPP Control Panel
   - Click "Start" for Apache and MySQL

3. **Download WordPress**
   - Go to https://wordpress.org/download/
   - Download the latest version
   - Extract to `C:\xampp\htdocs\parentdataforce`

4. **Create Database**
   - Open phpMyAdmin at http://localhost/phpmyadmin
   - Click "New" to create a database named `parentdataforce_wp`

5. **Configure WordPress**
   - Rename `wp-config-sample.php` to `wp-config.php`
   - Edit the file and set database details:
     ```php
     define('DB_NAME', 'parentdataforce_wp');
     define('DB_USER', 'root');
     define('DB_PASSWORD', '');
     define('DB_HOST', 'localhost');
     ```

6. **Run Installation**
   - Navigate to http://localhost/parentdataforce
   - Follow the installation wizard
   - Set site title to "Parent Data Force"
   - Create an admin user

## Essential Plugins to Install

After WordPress is installed, install these plugins:

1. **Custom Post Type UI** - For creating custom post types
2. **Advanced Custom Fields** - For custom fields
3. **WP REST API Controller** - For enhanced REST API control
4. **Application Passwords** - For REST API authentication
5. **WP Super Cache** - For performance optimization
6. **Yoast SEO** - For search engine optimization

## Configuring WordPress for Parent Data Force

### 1. Enable REST API
The REST API is enabled by default in WordPress 4.7+, but you can verify it's working by visiting:
`http://your-site.com/wp-json/wp/v2/posts`

### 2. Create Application Password
1. Go to Users > Profile
2. Scroll to "Application Passwords" section
3. Enter "ParentDataForce Migration" as the name
4. Click "Add New Application Password"
5. Save the generated password securely

### 3. Set Permalinks
1. Go to Settings > Permalinks
2. Select "Post name" structure
3. Save changes

### 4. Configure Reading Settings
1. Go to Settings > Reading
2. Set "Front page displays" to a static page
3. Create and select "Home" as front page
4. Create and select "Blog" as posts page

## Creating Custom Post Types

### Using Custom Post Type UI Plugin

1. Go to CPT UI > Add New
2. Register each custom post type:

#### Cases
- Slug: cases
- Plural: Cases
- Singular: Case
- Supports: title, editor, excerpt, thumbnail

#### Districts
- Slug: districts
- Plural: Districts
- Singular: District
- Supports: title, editor, excerpt, thumbnail

#### Resources
- Slug: resources
- Plural: Resources
- Singular: Resource
- Supports: title, editor, excerpt, thumbnail

#### Appearances
- Slug: appearances
- Plural: Appearances
- Singular: Appearance
- Supports: title, editor, excerpt, thumbnail

### Alternative: Code Registration

Add this to your theme's `functions.php`:

```php
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
        'supports' => array('title', 'editor', 'excerpt', 'thumbnail'),
        'show_in_rest' => true,
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
        'supports' => array('title', 'editor', 'excerpt', 'thumbnail'),
        'show_in_rest' => true,
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
        'supports' => array('title', 'editor', 'excerpt', 'thumbnail'),
        'show_in_rest' => true,
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
        'supports' => array('title', 'editor', 'excerpt', 'thumbnail'),
        'show_in_rest' => true,
    ));
}
add_action('init', 'create_parentdataforce_post_types');
```

## Theme Development

### Installing a Base Theme

1. Install a developer-friendly theme like "Underscores" (_s)
2. Go to Appearance > Themes > Add New
3. Search for "Underscores" and install

### Customizing for Parent Data Force Branding

Update the theme to match the dark/orange branding:

#### Color Scheme
- Primary Background: #0b0b0b
- Secondary Background: #161616
- Accent Color: #ff5a1f
- Accent Glow: #ffa366
- Text Primary: #f5f5f5
- Text Secondary: #a0a0a0
- Text Muted: #767676

#### Typography
- Primary Font: Inter
- Monospace Font: JetBrains Mono

### Adding Chart.js Support

1. Download Chart.js from https://www.chartjs.org/
2. Add to theme's js folder
3. Enqueue in functions.php:
```php
function parentdataforce_enqueue_scripts() {
    wp_enqueue_script('chart-js', get_template_directory_uri() . '/js/chart.min.js', array(), '4.4.0', true);
}
add_action('wp_enqueue_scripts', 'parentdataforce_enqueue_scripts');
```

## Running the Migration Script

Once WordPress is set up:

1. Update `wp_config.py` with your site URL and credentials
2. Run the migration script:
   ```bash
   python migrate_parentdataforce.py
   ```

## Post-Migration Tasks

### 1. Set Up Navigation Menus
1. Go to Appearance > Menus
2. Create "Primary Menu" and "Footer Menu"
3. Add the appropriate links as identified in the migration plan

### 2. Configure Homepage
1. Create a page named "Home"
2. Set it as the front page in Settings > Reading
3. Add widgets or content blocks as needed

### 3. Set Up Widgets
1. Go to Appearance > Widgets
2. Add subscribe form to footer
3. Add recent posts widget to sidebar (if applicable)

### 4. Configure SEO
1. Install and activate Yoast SEO
2. Configure titles and meta descriptions
3. Submit sitemap to Google Search Console

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

## Security Considerations

1. **Change Default Admin Username**
   - Don't use "admin" as username
   - Create a new administrator user and delete the default one

2. **Secure Application Passwords**
   - Store passwords securely
   - Rotate passwords periodically
   - Limit access to migration scripts

3. **Keep WordPress Updated**
   - Regularly update WordPress core
   - Update plugins and themes
   - Monitor security advisories

4. **Implement Additional Security**
   - Install a security plugin like Wordfence
   - Use strong passwords
   - Enable two-factor authentication

## Performance Optimization

1. **Caching**
   - Install WP Super Cache or W3 Total Cache
   - Configure caching rules appropriately

2. **Image Optimization**
   - Compress images before upload
   - Use WebP format when possible
   - Implement lazy loading

3. **Database Optimization**
   - Regularly clean up revisions and spam comments
   - Optimize database tables
   - Use a database optimization plugin

## Backup Strategy

1. **Regular Backups**
   - Schedule automatic backups
   - Store backups in multiple locations
   - Test backup restoration procedures

2. **Backup Components**
   - WordPress files
   - Database
   - Media uploads
   - Configuration files

3. **Backup Solutions**
   - UpdraftPlus
   - BackupBuddy
   - Manual database exports