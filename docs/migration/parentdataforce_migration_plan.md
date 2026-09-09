# Parent Data Force Migration Plan: Static Site to WordPress

## Overview
This document outlines the comprehensive plan to migrate the Parent Data Force static website to a dynamic WordPress platform using the REST API. The migration will preserve all content while enhancing functionality, maintainability, and scalability.

## Site Structure Analysis

### Key Pages to Create
1. **Homepage** - Main landing page with hero section, featured articles, quick links
2. **About** - Organization information and mission
3. **Articles** - Blog section for published articles
4. **Cases** - Case directory and current focus areas
5. **Districts** - District profiles and coverage
6. **Resources** - Resource library and materials
7. **Submit Data** - Form for submitting tips/data
8. **Donate** - Donation page
9. **Appearances** - Media appearances and public comments
10. **Search** - Search functionality

### Navigation Structure
- Primary Navigation: Data, Districts, Current Focus, Articles, Appearances, Resources, About, Submit Data, Donate
- Social Links: Facebook
- Utility: Search

### Content Types Identified
1. **Articles** - Will become WordPress Posts
2. **Cases** - Custom Post Type
3. **Districts** - Custom Post Type
4. **Resources** - Custom Post Type or Pages
5. **Appearances** - Custom Post Type

### Branding Elements
- Color Scheme: Dark theme (#0b0b0b) with orange accents (#ff5a1f)
- Typography: Inter (primary), JetBrains Mono (monospace)
- Visual Elements: Charts, data visualizations, statistics

## Migration Phases

### Phase 1: Environment Setup
1. Install WordPress locally or on server
2. Configure WordPress REST API
3. Install required plugins:
   - Custom Post Type UI
   - Advanced Custom Fields
   - WP REST API Controller (if needed)
4. Set up authentication for REST API access

### Phase 2: Theme Development
1. Create custom theme based on dark/orange branding
2. Implement responsive design
3. Add chart.js support for data visualizations
4. Create templates for custom post types

### Phase 3: Content Migration
1. Create homepage with hero section and featured content
2. Migrate articles as WordPress posts
3. Create custom post types for cases, districts, resources
4. Set up navigation menus
5. Import media assets

### Phase 4: Functionality Implementation
1. Implement search functionality
2. Create forms for data submission
3. Set up newsletter subscription
4. Add social sharing features

### Phase 5: Testing and Deployment
1. Test all migrated content
2. Verify navigation and links
3. Check responsive design
4. Deploy to production environment

## Technical Implementation Details

### REST API Endpoints to Use
- `wp-json/wp/v2/posts` - For articles
- `wp-json/wp/v2/pages` - For static pages
- `wp-json/wp/v2/media` - For image uploads
- `wp-json/wp/v2/users` - For author information
- Custom endpoints for cases, districts, resources

### Authentication Method
- Application Passwords (recommended for API access)
- OAuth 1.0a (alternative option)

### Data Mapping
| Static Site Element | WordPress Equivalent | Notes |
|---------------------|----------------------|-------|
| Articles | Posts | Preserve metadata, categories |
| Cases | Custom Post Type | Create "cases" CPT |
| Districts | Custom Post Type | Create "districts" CPT |
| Resources | Custom Post Type or Pages | Determine based on content |
| Appearances | Custom Post Type | Create "appearances" CPT |

## Implementation Steps

### Step 1: WordPress Installation
1. Download and install WordPress
2. Activate REST API (enabled by default in WordPress 4.7+)
3. Install required plugins
4. Configure permalink structure

### Step 2: Theme Development
1. Create child theme or custom theme
2. Implement dark/orange color scheme
3. Add responsive navigation
4. Create template files for all content types

### Step 3: Custom Post Types
1. Register "cases" custom post type
2. Register "districts" custom post type
3. Register "resources" custom post type
4. Register "appearances" custom post type

### Step 4: Content Migration Script
1. Parse static HTML files
2. Extract content and metadata
3. Create corresponding WordPress entities via REST API
4. Upload media files
5. Set featured images

### Step 5: Menu Creation
1. Create primary navigation menu
2. Assign menu locations
3. Add social media links
4. Configure footer navigation

### Step 6: Homepage Development
1. Create custom homepage template
2. Implement hero section
3. Add featured articles section
4. Include quick links and statistics
5. Add data visualization components

## Specific Content Migration Tasks

### Homepage
- Hero section with tagline "MAKING DATA MAKE SENSE"
- Featured articles section
- Quick links to key sections
- District coverage statistics
- Data visualization charts

### Articles
- Title, content, excerpt
- Publication date
- Categories: Guide, Data Analysis, Methodology, Case Update, Policy
- Read time metadata
- Featured images

### Cases
- Case titles and descriptions
- District associations
- Status information
- Timeline data
- Document attachments

### Districts
- District names and locations
- Case counts and activity
- Demographic information
- Profile pages

### Resources
- Resource titles and descriptions
- Categories
- Download links
- Related content

## Quality Assurance Checklist

### Pre-Migration
- [ ] Backup all static site files
- [ ] Document all content types and structures
- [ ] Identify all media assets
- [ ] Catalog all internal and external links

### During Migration
- [ ] Verify content integrity after migration
- [ ] Test all navigation links
- [ ] Validate responsive design
- [ ] Check data visualization functionality

### Post-Migration
- [ ] Test search functionality
- [ ] Verify form submissions
- [ ] Check social media integration
- [ ] Validate SEO metadata
- [ ] Performance testing

## Timeline Estimate

### Week 1: Environment Setup and Theme Development
- WordPress installation
- Theme development
- Custom post type registration

### Week 2: Content Migration
- Article migration
- Cases, districts, resources migration
- Media asset upload

### Week 3: Functionality Implementation
- Homepage development
- Navigation setup
- Forms and search implementation

### Week 4: Testing and Deployment
- Quality assurance testing
- Performance optimization
- Production deployment

## Success Metrics
- All content successfully migrated with preserved formatting
- Improved site performance and loading times
- Enhanced mobile responsiveness
- Maintained branding and visual identity
- Functional search and navigation
- Proper categorization of content types