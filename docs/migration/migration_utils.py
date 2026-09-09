#!/usr/bin/env python3
"""
Utility functions for Parent Data Force WordPress Migration
"""

import os
import json
import requests
from bs4 import BeautifulSoup

def parse_static_site_content(html_file_path):
    """
    Parse the static site HTML and extract structured content data
    """
    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"HTML file not found: {html_file_path}")
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract site metadata
    site_data = {
        'title': soup.find('title').get_text().strip() if soup.find('title') else 'Parent Data Force',
        'description': '',
        'navigation': [],
        'articles': [],
        'districts': [],
        'pages': []
    }
    
    # Extract meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        site_data['description'] = meta_desc.get('content', '')
    
    # Extract navigation items
    nav_items = soup.select('.nav-menu a')
    for item in nav_items:
        site_data['navigation'].append({
            'text': item.get_text().strip(),
            'href': item.get('href', '#')
        })
    
    # Extract articles
    article_cards = soup.find_all('article', class_='article-card')
    for card in article_cards:
        try:
            title_link = card.find('h3', class_='article-card-title').find('a')
            title = title_link.get_text().strip()
            link = title_link.get('href')
            
            meta_div = card.find('div', class_='article-card-meta')
            category = meta_div.find('span', class_='article-category').get_text().strip()
            date = meta_div.find('span', class_='article-date').get_text().strip()
            
            excerpt = card.find('p', class_='article-card-excerpt').get_text().strip()
            
            footer = card.find('div', class_='article-card-footer')
            read_time = footer.find('span', class_='article-read-time').get_text().strip()
            
            site_data['articles'].append({
                'title': title,
                'link': link,
                'category': category,
                'date': date,
                'excerpt': excerpt,
                'read_time': read_time
            })
        except AttributeError:
            continue
    
    # Extract districts
    district_links = soup.select('.resources-grid a[href*="/districts/"]')
    for link in district_links:
        title = link.find('h3').get_text().strip() if link.find('h3') else link.get_text().strip()
        url = link.get('href')
        site_data['districts'].append({
            'name': title,
            'url': url
        })
    
    return site_data

def generate_migration_report(site_data, output_file='migration_report.json'):
    """
    Generate a JSON report of the parsed site data
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(site_data, f, indent=2, ensure_ascii=False)
    
    print(f"Migration report generated: {output_file}")
    return output_file

def validate_wordpress_connection(api_url, username, password):
    """
    Validate connection to WordPress REST API
    """
    from base64 import b64encode
    
    credentials = f"{username}:{password}"
    encoded_credentials = b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    
    try:
        response = requests.get(f"{api_url}/users/me", headers=headers)
        response.raise_for_status()
        return True, "Connection successful"
    except requests.exceptions.RequestException as e:
        return False, f"Connection failed: {str(e)}"

def create_wordpress_content_structure():
    """
    Return the recommended WordPress content structure
    """
    return {
        "post_types": [
            {
                "name": "cases",
                "label": "Cases",
                "supports": ["title", "editor", "excerpt", "thumbnail"]
            },
            {
                "name": "districts",
                "label": "Districts",
                "supports": ["title", "editor", "excerpt", "thumbnail"]
            },
            {
                "name": "resources",
                "label": "Resources",
                "supports": ["title", "editor", "excerpt", "thumbnail"]
            },
            {
                "name": "appearances",
                "label": "Appearances",
                "supports": ["title", "editor", "excerpt", "thumbnail"]
            }
        ],
        "taxonomies": [
            {
                "name": "article_categories",
                "post_types": ["post"]
            }
        ],
        "menus": [
            {
                "name": "Primary Menu",
                "locations": ["primary"]
            },
            {
                "name": "Footer Menu",
                "locations": ["footer"]
            }
        ]
    }

def main():
    """
    Main utility function demonstration
    """
    print("Parent Data Force Migration Utilities")
    print("=" * 40)
    
    # Parse site content
    try:
        site_data = parse_static_site_content('site_source.html')
        print(f"Parsed {len(site_data['articles'])} articles")
        print(f"Parsed {len(site_data['districts'])} districts")
        print(f"Parsed {len(site_data['navigation'])} navigation items")
        
        # Generate report
        report_file = generate_migration_report(site_data)
        print(f"Report saved to: {report_file}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure 'site_source.html' is in the current directory")
    
    # Show content structure
    print("\nRecommended WordPress Content Structure:")
    structure = create_wordpress_content_structure()
    print(json.dumps(structure, indent=2))

if __name__ == "__main__":
    main()