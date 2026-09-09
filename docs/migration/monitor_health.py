#!/usr/bin/env python3
"""
Parent Data Force WordPress Site Health Monitoring
Monitors WordPress site performance and health
"""

import requests
import time
import json
from datetime import datetime
import wp_config
from wp import WPApiClient

class SiteHealthMonitor:
    """Monitors WordPress site health and performance"""
    
    def __init__(self, wp_client: WPApiClient = None):
        """
        Initialize health monitor
        
        Args:
            wp_client (WPApiClient): Optional WordPress API client
        """
        self.wp_client = wp_client or WPApiClient(base_url=wp_config.WP_URL)
        self.health_log = []
    
    def check_site_availability(self) -> dict:
        """
        Check if the site is accessible
        
        Returns:
            dict: Availability check results
        """
        start_time = time.time()
        result = {
            'timestamp': datetime.now().isoformat(),
            'check': 'availability',
            'status': 'unknown',
            'response_time': None,
            'status_code': None,
            'error': None
        }
        
        try:
            response = requests.get(wp_config.WP_URL, timeout=30)
            response_time = time.time() - start_time
            
            result['status_code'] = response.status_code
            result['response_time'] = round(response_time, 3)
            
            if response.status_code == 200:
                result['status'] = 'healthy'
            else:
                result['status'] = 'unhealthy'
                
        except requests.RequestException as e:
            result['status'] = 'unreachable'
            result['error'] = str(e)
        
        self.health_log.append(result)
        return result
    
    def check_api_endpoints(self) -> dict:
        """
        Check WordPress REST API endpoints
        
        Returns:
            dict: API endpoint check results
        """
        endpoints = [
            'posts',
            'pages',
            'media',
            'users'
        ]
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'check': 'api_endpoints',
            'endpoints': {}
        }
        
        for endpoint in endpoints:
            start_time = time.time()
            endpoint_result = {
                'status': 'unknown',
                'response_time': None,
                'status_code': None,
                'error': None
            }
            
            try:
                response = requests.get(
                    f"{wp_config.WP_API_BASE}/{endpoint}",
                    timeout=30
                )
                response_time = time.time() - start_time
                
                endpoint_result['status_code'] = response.status_code
                endpoint_result['response_time'] = round(response_time, 3)
                
                if response.status_code == 200:
                    endpoint_result['status'] = 'healthy'
                else:
                    endpoint_result['status'] = 'unhealthy'
                    
            except requests.RequestException as e:
                endpoint_result['status'] = 'unreachable'
                endpoint_result['error'] = str(e)
            
            results['endpoints'][endpoint] = endpoint_result
        
        self.health_log.append(results)
        return results
    
    def check_disk_space(self) -> dict:
        """
        Check disk space (simulated)
        
        Returns:
            dict: Disk space check results
        """
        # In a real implementation, this would check actual disk space
        # For now, we'll simulate a healthy disk space check
        result = {
            'timestamp': datetime.now().isoformat(),
            'check': 'disk_space',
            'status': 'healthy',
            'total_space': '100GB',
            'used_space': '25GB',
            'free_space': '75GB',
            'usage_percentage': 25
        }
        
        self.health_log.append(result)
        return result
    
    def check_database_connection(self) -> dict:
        """
        Check database connection (simulated)
        
        Returns:
            dict: Database connection check results
        """
        # In a real implementation, this would check actual database connection
        # For now, we'll simulate a healthy database connection
        result = {
            'timestamp': datetime.now().isoformat(),
            'check': 'database_connection',
            'status': 'healthy',
            'connection_time': 0.005,
            'error': None
        }
        
        self.health_log.append(result)
        return result
    
    def run_full_health_check(self) -> dict:
        """
        Run a complete health check
        
        Returns:
            dict: Full health check results
        """
        print("Running full health check...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Run all checks
        results['checks']['availability'] = self.check_site_availability()
        results['checks']['api_endpoints'] = self.check_api_endpoints()
        results['checks']['disk_space'] = self.check_disk_space()
        results['checks']['database_connection'] = self.check_database_connection()
        
        # Determine overall status
        unhealthy_checks = []
        for check_name, check_result in results['checks'].items():
            if isinstance(check_result, dict) and check_result.get('status') != 'healthy':
                unhealthy_checks.append(check_name)
            elif isinstance(check_result, dict) and 'endpoints' in check_result:
                for endpoint, endpoint_result in check_result['endpoints'].items():
                    if endpoint_result.get('status') != 'healthy':
                        unhealthy_checks.append(f"{check_name}.{endpoint}")
        
        if not unhealthy_checks:
            results['overall_status'] = 'healthy'
        elif len(unhealthy_checks) <= 2:
            results['overall_status'] = 'degraded'
        else:
            results['overall_status'] = 'unhealthy'
        
        results['unhealthy_checks'] = unhealthy_checks
        
        print(f"Health check complete. Overall status: {results['overall_status']}")
        if unhealthy_checks:
            print(f"Unhealthy checks: {', '.join(unhealthy_checks)}")
        
        return results
    
    def save_health_report(self, results: dict, output_path: str = "health_report.json"):
        """
        Save health report to JSON file
        
        Args:
            results (dict): Health check results
            output_path (str): Output file path
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Health report saved to: {output_path}")

def main():
    """Main function for site health monitoring"""
    monitor = SiteHealthMonitor()
    
    # Run health check
    results = monitor.run_full_health_check()
    
    # Save report
    monitor.save_health_report(results)
    
    # Print summary
    print("\n" + "="*50)
    print("SITE HEALTH SUMMARY")
    print("="*50)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Check Time: {results['timestamp']}")
    
    unhealthy_count = len(results.get('unhealthy_checks', []))
    if unhealthy_count > 0:
        print(f"\nIssues Found: {unhealthy_count}")
        for check in results['unhealthy_checks']:
            print(f"  - {check}")
    else:
        print("\nNo issues found. Site is healthy!")

if __name__ == "__main__":
    main()