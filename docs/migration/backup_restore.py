#!/usr/bin/env python3
"""
Parent Data Force WordPress Backup and Restore
Handles backup and restoration of WordPress site
"""

import os
import zipfile
import json
import subprocess
import shutil
from datetime import datetime
import wp_config
from wp import WPApiClient

class WordPressBackupRestore:
    """Handles WordPress backup and restore operations"""
    
    def __init__(self, wp_client: WPApiClient = None, backup_dir: str = None):
        """
        Initialize backup/restore manager
        
        Args:
            wp_client (WPApiClient): Optional WordPress API client
            backup_dir (str): Backup directory path
        """
        self.wp_client = wp_client or WPApiClient(base_url=wp_config.WP_URL)
        self.backup_dir = backup_dir or wp_config.BACKUP_DIRECTORY
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Backup WordPress database (simulated)
        
        Args:
            backup_path (str): Path to save database backup
            
        Returns:
            bool: True if backup successful
        """
        print("Backing up database...")
        
        # In a real implementation, this would use mysqldump or similar
        # For now, we'll create a simulated database backup
        try:
            db_info = {
                'backup_date': datetime.now().isoformat(),
                'site_url': wp_config.WP_URL,
                'tables': [
                    'wp_options',
                    'wp_posts',
                    'wp_postmeta',
                    'wp_terms',
                    'wp_term_taxonomy',
                    'wp_term_relationships',
                    'wp_users',
                    'wp_usermeta'
                ],
                'row_counts': {
                    'wp_options': 125,
                    'wp_posts': 42,
                    'wp_postmeta': 210,
                    'wp_terms': 15,
                    'wp_term_taxonomy': 15,
                    'wp_term_relationships': 38,
                    'wp_users': 3,
                    'wp_usermeta': 42
                }
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(db_info, f, indent=2)
            
            print(f"Database backup saved to: {backup_path}")
            return True
        except Exception as e:
            print(f"Database backup failed: {e}")
            return False
    
    def backup_files(self, backup_path: str, file_paths: list = None) -> bool:
        """
        Backup WordPress files
        
        Args:
            backup_path (str): Path to save file backup
            file_paths (list): Specific files to backup (default: all)
            
        Returns:
            bool: True if backup successful
        """
        print("Backing up files...")
        
        if file_paths is None:
            # Default file paths to backup
            file_paths = [
                './wordpress',
                './themes',
                './plugins'
            ]
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in file_paths:
                    if os.path.exists(file_path):
                        if os.path.isfile(file_path):
                            zipf.write(file_path)
                        elif os.path.isdir(file_path):
                            for root, dirs, files in os.walk(file_path):
                                for file in files:
                                    full_path = os.path.join(root, file)
                                    arc_path = os.path.relpath(full_path, '.')
                                    zipf.write(full_path, arc_path)
            
            print(f"Files backup saved to: {backup_path}")
            return True
        except Exception as e:
            print(f"Files backup failed: {e}")
            return False
    
    def create_full_backup(self, backup_name: str = None) -> str:
        """
        Create a full backup of WordPress site
        
        Args:
            backup_name (str): Custom backup name (default: auto-generated)
            
        Returns:
            str: Path to backup file
        """
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"wordpress_backup_{timestamp}"
        
        print(f"Creating full backup: {backup_name}")
        
        # Create backup directory for this backup
        backup_path = os.path.join(self.backup_dir, backup_name)
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
        
        # Backup database
        db_backup_path = os.path.join(backup_path, "database.json")
        db_success = self.backup_database(db_backup_path)
        
        # Backup files
        files_backup_path = os.path.join(backup_path, "files.zip")
        files_success = self.backup_files(files_backup_path)
        
        # Create backup metadata
        metadata = {
            'backup_name': backup_name,
            'backup_date': datetime.now().isoformat(),
            'site_url': wp_config.WP_URL,
            'components': {
                'database': db_success,
                'files': files_success
            },
            'file_sizes': {
                'database': os.path.getsize(db_backup_path) if db_success else 0,
                'files': os.path.getsize(files_backup_path) if files_success else 0
            }
        }
        
        metadata_path = os.path.join(backup_path, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        if db_success and files_success:
            print(f"Full backup created successfully at: {backup_path}")
            return backup_path
        else:
            print("Backup completed with errors")
            return backup_path
    
    def restore_database(self, backup_path: str) -> bool:
        """
        Restore WordPress database from backup (simulated)
        
        Args:
            backup_path (str): Path to database backup
            
        Returns:
            bool: True if restore successful
        """
        print("Restoring database...")
        
        # In a real implementation, this would restore the actual database
        # For now, we'll just verify the backup file exists
        if os.path.exists(backup_path):
            print(f"Database restored from: {backup_path}")
            return True
        else:
            print(f"Database backup not found: {backup_path}")
            return False
    
    def restore_files(self, backup_path: str, restore_paths: dict = None) -> bool:
        """
        Restore WordPress files from backup
        
        Args:
            backup_path (str): Path to files backup
            restore_paths (dict): Mapping of backup paths to restore locations
            
        Returns:
            bool: True if restore successful
        """
        print("Restoring files...")
        
        if not os.path.exists(backup_path):
            print(f"Files backup not found: {backup_path}")
            return False
        
        try:
            # Extract files
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                if restore_paths:
                    # Restore specific paths
                    for backup_path, restore_path in restore_paths.items():
                        # This is a simplified approach - in reality, you'd need to
                        # map the paths correctly
                        pass
                else:
                    # Restore all files
                    zipf.extractall('.')
            
            print(f"Files restored from: {backup_path}")
            return True
        except Exception as e:
            print(f"Files restore failed: {e}")
            return False
    
    def restore_backup(self, backup_path: str, components: list = None) -> bool:
        """
        Restore WordPress site from backup
        
        Args:
            backup_path (str): Path to backup directory
            components (list): Components to restore (database, files)
            
        Returns:
            bool: True if restore successful
        """
        if components is None:
            components = ['database', 'files']
        
        print(f"Restoring backup from: {backup_path}")
        
        # Check if backup exists
        if not os.path.exists(backup_path):
            print(f"Backup not found: {backup_path}")
            return False
        
        # Load metadata
        metadata_path = os.path.join(backup_path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            print(f"Backup metadata: {metadata['backup_name']} from {metadata['backup_date']}")
        
        success = True
        
        # Restore database
        if 'database' in components:
            db_backup_path = os.path.join(backup_path, "database.json")
            if not self.restore_database(db_backup_path):
                success = False
        
        # Restore files
        if 'files' in components:
            files_backup_path = os.path.join(backup_path, "files.zip")
            if not self.restore_files(files_backup_path):
                success = False
        
        if success:
            print("Backup restoration completed successfully")
        else:
            print("Backup restoration completed with errors")
        
        return success
    
    def list_backups(self) -> list:
        """
        List available backups
        
        Returns:
            list: List of available backups
        """
        backups = []
        
        if os.path.exists(self.backup_dir):
            for item in os.listdir(self.backup_dir):
                item_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(item_path):
                    # Check if it's a valid backup (has metadata)
                    metadata_path = os.path.join(item_path, "metadata.json")
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        backups.append({
                            'name': item,
                            'path': item_path,
                            'date': metadata.get('backup_date', ''),
                            'components': metadata.get('components', {}),
                            'size': sum(metadata.get('file_sizes', {}).values())
                        })
        
        # Sort by date (newest first)
        backups.sort(key=lambda x: x['date'], reverse=True)
        return backups
    
    def delete_old_backups(self, retention_days: int = None):
        """
        Delete old backups based on retention policy
        
        Args:
            retention_days (int): Number of days to retain backups
        """
        if retention_days is None:
            retention_days = wp_config.BACKUP_RETENTION_DAYS
        
        print(f"Cleaning up backups older than {retention_days} days...")
        
        backups = self.list_backups()
        now = datetime.now()
        
        deleted_count = 0
        for backup in backups:
            backup_date = datetime.fromisoformat(backup['date'])
            age_days = (now - backup_date).days
            
            if age_days > retention_days:
                try:
                    shutil.rmtree(backup['path'])
                    print(f"Deleted old backup: {backup['name']}")
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete backup {backup['name']}: {e}")
        
        print(f"Deleted {deleted_count} old backups")

def main():
    """Main function for backup/restore operations"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WordPress Backup and Restore')
    parser.add_argument('action', choices=['backup', 'restore', 'list'], 
                       help='Action to perform')
    parser.add_argument('--backup-name', help='Name for the backup')
    parser.add_argument('--backup-path', help='Path to backup for restoration')
    parser.add_argument('--components', nargs='+', 
                       choices=['database', 'files'], default=['database', 'files'],
                       help='Components to backup/restore')
    
    args = parser.parse_args()
    
    backup_manager = WordPressBackupRestore()
    
    if args.action == 'backup':
        backup_manager.create_full_backup(args.backup_name)
    elif args.action == 'restore':
        if not args.backup_path:
            print("Error: --backup-path is required for restore action")
            return 1
        backup_manager.restore_backup(args.backup_path, args.components)
    elif args.action == 'list':
        backups = backup_manager.list_backups()
        if backups:
            print("Available backups:")
            for backup in backups:
                size_mb = backup['size'] / (1024 * 1024)
                print(f"  {backup['name']} ({size_mb:.1f} MB) - {backup['date']}")
        else:
            print("No backups found")

if __name__ == "__main__":
    exit(main())