#!/usr/bin/env python3
"""
Parent Data Force Migration Script
Migrates static site content to WordPress using the REST API
"""

import requests
import json
import os
from bs4 import BeautifulSoup
import base64
from wp_config import WP_API_URL, WP_USERNAME, WP_APPLICATION_PASSWORD

class WordPressMigrator:
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
    
    def create_post(self, title, content, post_type="posts", status="publish", meta=None):
        """Create a post/page via WordPress REST API"""
        url = f"{self.api_url}/{post_type}"
        data = {
            "title": title,
            "content": content,
            "status": status
        }
        
        if meta:
            data.update(meta)
            
        try:
            response = requests.post(url, headers=self.auth_header, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating post '{title}': {e}")
            return None
    
    def create_page(self, title, content, status="publish"):
        """Create a page via WordPress REST API"""
        return self.create_post(title, content, "pages", status)
    
    def upload_media(self, file_path, title=""):
        """Upload media file to WordPress"""
        url = f"{self.api_url}/media"
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
            
        with open(file_path, 'rb') as f:
            media_content = f.read()
            
        headers = self.auth_header.copy()
        headers['Content-Type'] = 'image/png'  # Adjust based on file type
        headers['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        
        files = {'file': (os.path.basename(file_path), media_content)}
        data = {'title': title} if title else {}
        
        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error uploading media '{file_path}': {e}")
            return None
    
    def create_menu(self, name, items):
        """Create a navigation menu"""
        # This would require a plugin like WP REST API Menus
        # For now, we'll just print the menu structure
        print(f"Menu '{name}' would contain:")
        for item in items:
            print(f"  - {item}")
        return True
    
    def extract_articles_from_html(self, html_content):
        """Extract articles from the static site HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []
        
        # Find all article cards
        article_cards = soup.find_all('article', class_='article-card')
        
        for card in article_cards:
            try:
                # Extract title
                title_link = card.find('h3', class_='article-card-title').find('a')
                title = title_link.get_text().strip()
                link = title_link.get('href')
                
                # Extract category and date
                meta_div = card.find('div', class_='article-card-meta')
                category = meta_div.find('span', class_='article-category').get_text().strip()
                date = meta_div.find('span', class_='article-date').get_text().strip()
                
                # Extract excerpt
                excerpt = card.find('p', class_='article-card-excerpt').get_text().strip()
                
                # Extract read time
                footer = card.find('div', class_='article-card-footer')
                read_time = footer.find('span', class_='article-read-time').get_text().strip()
                
                article_data = {
                    'title': title,
                    'link': link,
                    'category': category,
                    'date': date,
                    'excerpt': excerpt,
                    'read_time': read_time
                }
                
                articles.append(article_data)
            except AttributeError as e:
                print(f"Error parsing article card: {e}")
                continue
                
        return articles
    
    def migrate_articles(self, html_content):
        """Migrate articles from static site to WordPress posts"""
        articles = self.extract_articles_from_html(html_content)
        migrated_articles = []
        
        for article in articles:
            # Create post content with excerpt and metadata
            content = f"<p>{article['excerpt']}</p>\n"
            content += f"<p><em>Category: {article['category']} | "
            content += f"Published: {article['date']} | "
            content += f"Read Time: {article['read_time']}</em></p>"
            
            # For a full migration, you would fetch the complete article content
            # from the article's URL and include it here
            
            post_data = {
                'title': article['title'],
                'content': content,
                'status': 'publish',
                'categories': [article['category']]
            }
            
            result = self.create_post(
                article['title'], 
                content, 
                "posts", 
                "publish"
            )
            
            if result:
                migrated_articles.append(result)
                print(f"Migrated article: {article['title']}")
            else:
                print(f"Failed to migrate article: {article['title']}")
                
        return migrated_articles
    
    def create_homepage(self, html_content):
        """Create the homepage with hero section and featured content"""
        # Parse the homepage content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract hero section content
        hero_section = soup.find('section', class_='hero')
        hero_title = hero_section.find('h1', class_='hero-title').get_text().strip()
        hero_subtitle = hero_section.find('p', class_='hero-subtitle').get_text().strip()
        
        # Create homepage content
        homepage_content = f"""
<h1>{hero_title}</h1>
<p>{hero_subtitle}</p>

<h2>Latest Articles</h2>
<p>Check out our latest data-driven reporting on special education, public records, and systemic accountability across Massachusetts.</p>

<h2>What We Track</h2>
<p>Every investigation, public records request, state determination, and systemic pattern — organized and accessible.</p>

<h2>District Coverage</h2>
<p>Each district profiled with case activity, restraint data, and demographic context.</p>
"""
        
        # Create the homepage
        result = self.create_page("Home", homepage_content)
        if result:
            print("Homepage created successfully")
            return result
        else:
            print("Failed to create homepage")
            return None
    
    def create_key_pages(self):
        """Create key static pages"""
        pages = [
            {
                "title": "About",
                "content": "<h1>About Parent Data Force</h1><p>Independent special education and public accountability advocacy.</p>"
            },
            {
                "title": "Cases",
                "content": "<h1>Case Directory</h1><p>Active investigations, public records requests, appeals, and state determinations.</p>"
            },
            {
                "title": "Districts",
                "content": "<h1>District Profiles</h1><p>Per-district pages aggregating cases, data summaries, and advocacy activity.</p>"
            },
            {
                "title": "Resources",
                "content": "<h1>Resource Library</h1><p>Guides, templates, and educational materials for advocacy.</p>"
            },
            {
                "title": "Submit Data",
                "content": "<h1>Submit Information</h1><p>Share tips, documents, or concerns with our team.</p>"
            },
            {
                "title": "Donate",
                "content": "<h1>Support Our Work</h1><p>Help us continue our advocacy efforts with a donation.</p>"
            },
            {
                "title": "Appearances",
                "content": "<h1>Media & Appearances</h1><p>Public comments, school committee testimony, and press coverage.</p>"
            }
        ]
        
        created_pages = []
        for page in pages:
            result = self.create_page(page["title"], page["content"])
            if result:
                created_pages.append(result)
                print(f"Created page: {page['title']}")
            else:
                print(f"Failed to create page: {page['title']}")
                
        return created_pages

def main():
    """Main migration function"""
    migrator = WordPressMigrator()
    
    # Read the static site HTML
    try:
        with open('site_source.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("Error: site_source.html not found")
        return
    
    print("Starting Parent Data Force migration to WordPress...")
    
    # Create key pages
    print("\n1. Creating key pages...")
    migrator.create_key_pages()
    
    # Create homepage
    print("\n2. Creating homepage...")
    migrator.create_homepage(html_content)
    
    # Migrate articles
    print("\n3. Migrating articles...")
    migrator.migrate_articles(html_content)
    
    print("\nMigration completed!")

if __name__ == "__main__":
    main()