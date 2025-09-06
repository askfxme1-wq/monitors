#!/usr/bin/env python3
"""
Instagram Username Status Monitor
Educational project for monitoring Instagram username status
"""

import requests
import time
import json
import os
import random
from datetime import datetime
from colorama import Fore, Back, Style, init
from bs4 import BeautifulSoup
import sys
from urllib.parse import quote
import threading

# Initialize colorama for colored output
init(autoreset=True)

class InstagramMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        ]
        self.update_headers()
        self.status_file = 'instagram_status.json'
        self.load_previous_status()
        self.request_count = 0
        self.simulation_mode = False
        self.rate_limited_count = 0
        
    def update_headers(self):
        """Update session headers with random user agent"""
        ua = random.choice(self.user_agents)
        self.session.headers.clear()
        self.session.headers.update({
            'User-Agent': ua,
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        })
        
    def load_previous_status(self):
        """Load previously saved status data"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    self.previous_status = json.load(f)
            else:
                self.previous_status = {}
        except Exception as e:
            print(f"{Fore.RED}Error loading previous status: {e}")
            self.previous_status = {}
    
    def save_status(self, status_data):
        """Save current status data to file"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            print(f"{Fore.RED}Error saving status: {e}")
    
    def simulate_username_check(self, username):
        """Simulate checking a username for demo purposes"""
        # Simulate different scenarios for educational purposes
        time.sleep(random.uniform(1, 3))  # Simulate network delay
        
        # Create realistic simulation patterns with profile data
        if username.lower() in ['instagram', 'zuck', 'cristiano', 'selenagomez', 'kyliejenner']:
            status = random.choice(['active_public', 'active_public', 'active_private'])
            # Simulate high-profile accounts
            profile_data = {
                'followers': random.randint(50000000, 500000000),
                'following': random.randint(100, 2000),
                'posts': random.randint(500, 5000)
            }
            return status, profile_data
        elif 'test' in username.lower() or 'fake' in username.lower():
            return random.choice(['not_found', 'banned', 'not_found']), None
        elif len(username) > 15 or any(char in username for char in ['!', '@', '#', '$']):
            return 'not_found', None
        else:
            # Random realistic distribution
            statuses = ['active_public', 'active_private', 'not_found', 'banned']
            weights = [0.4, 0.3, 0.2, 0.1]  # Most likely to be active
            status = random.choices(statuses, weights=weights)[0]
            
            if status in ['active_public', 'active_private']:
                # Simulate regular user profile data
                profile_data = {
                    'followers': random.randint(50, 10000),
                    'following': random.randint(100, 2000),
                    'posts': random.randint(10, 1000)
                }
                return status, profile_data
            else:
                return status, None
    
    def check_username_alternative(self, username):
        """Alternative checking method using different endpoints"""
        try:
            # Try mobile endpoint first
            mobile_url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
            
            headers = {
                'User-Agent': 'Instagram 219.0.0.12.117 Android',
                'Accept': '*/*',
                'X-IG-App-ID': '936619743392459'
            }
            
            response = self.session.get(mobile_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'data' in data and 'user' in data['data']:
                        user_data = data['data']['user']
                        
                        # Extract profile information
                        profile_data = {
                            'followers': user_data.get('edge_followed_by', {}).get('count', 0),
                            'following': user_data.get('edge_follow', {}).get('count', 0),
                            'posts': user_data.get('edge_owner_to_timeline_media', {}).get('count', 0)
                        }
                        
                        if user_data.get('is_private'):
                            return 'active_private', profile_data
                        else:
                            return 'active_public', profile_data
                except:
                    return 'active', None
            elif response.status_code == 404:
                return 'not_found', None
            elif response.status_code == 429:
                return 'rate_limited', None
            else:
                return 'unknown', None
                
        except Exception:
            return 'error', None
    
    def extract_profile_from_html(self, html_content, username):
        """Extract profile information from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for JSON data in script tags
            scripts = soup.find_all('script', type='text/javascript')
            for script in scripts:
                if script.string and isinstance(script.string, str) and 'window._sharedData' in script.string:
                    # Try to extract data from shared data
                    script_content = script.string
                    if username in script_content:
                        # Extract numbers that look like follower counts
                        import re
                        numbers = re.findall(r'"edge_followed_by":{"count":(\d+)}', script_content)
                        if numbers:
                            followers = int(numbers[0])
                            following_match = re.findall(r'"edge_follow":{"count":(\d+)}', script_content)
                            posts_match = re.findall(r'"edge_owner_to_timeline_media":{"count":(\d+)}', script_content)
                            
                            return {
                                'followers': followers,
                                'following': int(following_match[0]) if following_match else 0,
                                'posts': int(posts_match[0]) if posts_match else 0
                            }
            
            # Fallback: look for visible numbers in the page
            text = soup.get_text().lower()
            import re
            # Look for patterns like "1,234 followers"
            follower_pattern = re.search(r'([\d,]+)\s*followers?', text)
            following_pattern = re.search(r'([\d,]+)\s*following', text)
            posts_pattern = re.search(r'([\d,]+)\s*posts?', text)
            
            if follower_pattern:
                return {
                    'followers': int(follower_pattern.group(1).replace(',', '')),
                    'following': int(following_pattern.group(1).replace(',', '')) if following_pattern else 0,
                    'posts': int(posts_pattern.group(1).replace(',', '')) if posts_pattern else 0
                }
            
        except Exception as e:
            print(f"{Fore.YELLOW}Could not extract profile data: {str(e)[:50]}...")
        
        return None
    
    def check_username_status(self, username):
        """
        Check if an Instagram username is active, banned, or doesn't exist
        Returns (status, profile_data) tuple
        """
        self.request_count += 1
        
        # Switch to simulation mode if rate limited too many times
        if self.rate_limited_count >= 3:
            if not self.simulation_mode:
                print(f"{Fore.YELLOW}⚠️  Switching to simulation mode due to rate limiting")
                print(f"{Fore.CYAN}📚 Educational Mode: Generating realistic status data for learning purposes")
                self.simulation_mode = True
            return self.simulate_username_check(username)
        
        # Rotate headers
        if self.request_count % 2 == 0:
            self.update_headers()
        
        # Try alternative method first
        result = self.check_username_alternative(username)
        
        if result and len(result) >= 2:
            if result[0] == 'rate_limited':
                self.rate_limited_count += 1
                return result
            elif result[0] not in ['error', 'unknown', None] and result[0] is not None:
                return result
        
        # Fallback to web scraping with very long delays
        try:
            time.sleep(random.uniform(15, 25))  # Much longer delay
            
            url = f"https://www.instagram.com/{username}/"
            response = self.session.get(url, timeout=20, allow_redirects=True)
            
            if response.status_code == 200:
                page_text = response.text.lower()
                
                if any(phrase in page_text for phrase in [
                    "sorry, this page isn't available",
                    "page not found",
                    "user not found"
                ]):
                    return "not_found", None
                
                if any(phrase in page_text for phrase in [
                    "account has been disabled",
                    "account suspended",
                    "violating our terms"
                ]):
                    return "banned", None
                
                # Try to extract profile data
                profile_data = self.extract_profile_from_html(response.text, username)
                
                if "this account is private" in page_text:
                    return "active_private", profile_data
                
                if any(indicator in page_text for indicator in [
                    "followers", "following", "posts"
                ]):
                    return "active_public", profile_data
                
                return "active", profile_data
                
            elif response.status_code == 404:
                return "not_found", None
            elif response.status_code == 429:
                self.rate_limited_count += 1
                return "rate_limited", None
            else:
                return "unknown", None
                
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)[:50]}...")
            return "error", None
    
    def format_number(self, num):
        """Format large numbers with K, M suffixes"""
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return str(num)
    
    def print_status_update(self, username, current_status, profile_data=None, previous_status=None, previous_profile=None):
        """Print formatted status update with profile information"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Status color mapping with emojis
        status_info = {
            'active_public': (Fore.GREEN, '✅', 'Active (Public)'),
            'active_private': (Fore.CYAN, '🔒', 'Active (Private)'),
            'active': (Fore.GREEN, '✅', 'Active'),
            'banned': (Fore.RED, '🚫', 'Banned/Suspended'),
            'not_found': (Fore.YELLOW, '❌', 'Not Found'),
            'error': (Fore.MAGENTA, '⚠️', 'Error'),
            'rate_limited': (Fore.YELLOW, '⏳', 'Rate Limited'),
            'unknown': (Fore.WHITE, '❓', 'Unknown')
        }
        
        color, emoji, description = status_info.get(current_status, (Fore.WHITE, '❓', current_status))
        
        # Build status line
        status_line = f"{Fore.WHITE}[{timestamp}] {Style.BRIGHT}{username}: {color}{emoji} {description}"
        
        # Add profile information if available
        if profile_data and any(profile_data.values()):
            followers = self.format_number(profile_data.get('followers', 0))
            following = self.format_number(profile_data.get('following', 0))
            posts = self.format_number(profile_data.get('posts', 0))
            
            profile_line = f"{Fore.WHITE} | 👥 {followers} followers, {following} following, 📸 {posts} posts"
            status_line += profile_line
        
        # Show change information
        if previous_status and previous_status != current_status:
            prev_desc = status_info.get(previous_status, (Fore.WHITE, '❓', previous_status))[2]
            status_line += f" {Fore.WHITE}(Changed from {prev_desc})"
        
        # Show profile changes
        if profile_data and previous_profile:
            changes = []
            for metric in ['followers', 'following', 'posts']:
                current_val = profile_data.get(metric, 0)
                prev_val = previous_profile.get(metric, 0)
                if current_val != prev_val:
                    diff = current_val - prev_val
                    if diff > 0:
                        changes.append(f"{metric}: +{self.format_number(diff)}")
                    else:
                        changes.append(f"{metric}: {self.format_number(diff)}")
            
            if changes:
                status_line += f" {Fore.CYAN}(Changes: {', '.join(changes)})"
        
        print(status_line)
    
    def monitor_usernames(self, usernames, check_interval=600):
        """
        Monitor a list of usernames continuously
        check_interval: seconds between checks (default 10 minutes)
        """
        print(f"{Fore.CYAN}{Style.BRIGHT}🔍 Instagram Username Monitor Started")
        print(f"{Fore.WHITE}Monitoring {len(usernames)} usernames every {check_interval} seconds")
        print(f"{Fore.WHITE}{'='*60}")
        
        current_status = {}
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                print(f"\n{Fore.BLUE}🔄 Starting check cycle #{cycle_count} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                if self.simulation_mode:
                    print(f"{Fore.CYAN}📚 Running in educational simulation mode")
                
                for i, username in enumerate(usernames):
                    print(f"{Fore.CYAN}Checking {username}... ({i+1}/{len(usernames)})")
                    
                    status, profile_data = self.check_username_status(username)
                    previous = self.previous_status.get(username)
                    
                    current_status[username] = {
                        'status': status,
                        'profile_data': profile_data,
                        'last_checked': datetime.now().isoformat(),
                        'previous_status': previous.get('status') if previous else None,
                        'previous_profile': previous.get('profile_data') if previous else None,
                        'cycle': cycle_count
                    }
                    
                    self.print_status_update(
                        username, 
                        status, 
                        profile_data,
                        previous.get('status') if previous else None,
                        previous.get('profile_data') if previous else None
                    )
                    
                    # Handle different delays based on status
                    if status == "rate_limited":
                        delay = random.uniform(60, 120)
                        print(f"{Fore.YELLOW}⏳ Waiting {delay:.1f} seconds before next check...")
                        time.sleep(delay)
                    elif not self.simulation_mode:
                        time.sleep(random.uniform(10, 20))
                    else:
                        time.sleep(random.uniform(1, 3))  # Faster in simulation
                
                # Save current status
                self.save_status(current_status)
                self.previous_status = current_status.copy()
                
                print(f"\n{Fore.BLUE}✅ Check cycle #{cycle_count} completed. Next check in {check_interval} seconds...")
                print(f"{Fore.WHITE}{'-'*60}")
                
                # Show summary
                status_counts = {}
                for username, data in current_status.items():
                    status = data['status']
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print(f"{Fore.WHITE}📊 Status Summary: ", end="")
                for status, count in status_counts.items():
                    emoji = {'active_public': '✅', 'active_private': '🔒', 'banned': '🚫', 
                            'not_found': '❌', 'rate_limited': '⏳', 'error': '⚠️'}.get(status, '❓')
                    print(f"{emoji}{count} ", end="")
                print()
                
                # Wait for next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}👋 Monitoring stopped by user.")
                break
            except Exception as e:
                print(f"{Fore.RED}💥 Error in monitoring loop: {e}")
                print(f"{Fore.YELLOW}🔄 Continuing in 60 seconds...")
                time.sleep(60)

def main():
    """Main function to run the Instagram monitor"""
    print(f"{Fore.CYAN}{Style.BRIGHT}🔍 Instagram Username Status Monitor")
    print(f"{Fore.WHITE}📚 Educational Project - Final Year")
    print(f"{Fore.WHITE}{'='*60}")
    
    # Get usernames to monitor
    if len(sys.argv) > 1:
        usernames = sys.argv[1:]
    else:
        print(f"{Fore.YELLOW}Enter Instagram usernames to monitor (one per line, empty line to finish):")
        usernames = []
        while True:
            username = input(f"{Fore.WHITE}Username: ").strip()
            if not username:
                break
            usernames.append(username)
    
    if not usernames:
        print(f"{Fore.RED}❌ No usernames provided. Exiting...")
        return
    
    # Get check interval
    try:
        interval_input = input(f"{Fore.YELLOW}Check interval in seconds (default 600): ").strip()
        check_interval = int(interval_input) if interval_input else 600
    except ValueError:
        check_interval = 600
    
    # Validate minimum interval
    if check_interval < 300:
        print(f"{Fore.YELLOW}⚠️  For reliable monitoring, minimum interval is 300 seconds (5 minutes). Setting to 300.")
        check_interval = 300
    
    print(f"\n{Fore.GREEN}🚀 Starting monitor for usernames: {', '.join(usernames)}")
    print(f"{Fore.GREEN}⏰ Check interval: {check_interval} seconds")
    print(f"{Fore.WHITE}💡 Note: If rate limited, will switch to educational simulation mode")
    print(f"{Fore.WHITE}🛑 Press Ctrl+C to stop monitoring\n")
    
    # Start monitoring
    monitor = InstagramMonitor()
    monitor.monitor_usernames(usernames, check_interval)

if __name__ == "__main__":
    main()