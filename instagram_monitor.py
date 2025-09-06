#!/usr/bin/env python3
"""
Enhanced Instagram Username Status Monitor
Educational project for monitoring Instagram username status with advanced features
"""

import requests
import time
import json
import os
import random
import re
from datetime import datetime, timedelta
from colorama import Fore, Back, Style, init
from bs4 import BeautifulSoup
import sys
from urllib.parse import quote
import threading
# from fake_useragent import UserAgent  # Optional import

# Initialize colorama for colored output
init(autoreset=True)

class EnhancedInstagramMonitor:
    def __init__(self):
        # Initialize session with connection pooling
        self.session = requests.Session()
        self.session.adapters.clear()
        
        # Add connection pooling adapter
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=2,
            pool_maxsize=5,
            max_retries=0  # We handle retries manually
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Enhanced user agent rotation with better mobile support
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 14; Mobile; rv:109.0) Gecko/109.0 Firefox/115.0',
        ]
        
        self.update_headers()
        self.status_file = 'instagram_status.json'
        self.rate_limit_file = 'rate_limits.json'
        self.load_previous_status()
        self.load_rate_limit_data()
        
        # Initialize logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup efficient logging system"""
        try:
            import logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_file),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            self.logger = logging.getLogger(__name__)
            self.log_message("🚀 Instagram Monitor initialized with enhanced logging", level='info')
        except Exception:
            self.logger = None
            print(f"{Fore.YELLOW}⚠️ Logging setup failed, using print fallback")
    
    def log_message(self, message, level='info'):
        """Unified logging with fallback to print"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if self.logger:
            if level == 'error':
                self.logger.error(message)
            elif level == 'warning':
                self.logger.warning(message)
            else:
                self.logger.info(message)
        else:
            # Fallback to colored print
            colors = {
                'info': Fore.CYAN,
                'warning': Fore.YELLOW,
                'error': Fore.RED
            }
            color = colors.get(level, Fore.WHITE)
            print(f"{color}[{timestamp}] {message}")
    
    def get_request_stats(self):
        """Get comprehensive request statistics"""
        total_requests = self.successful_requests + self.failed_requests
        success_rate = (self.successful_requests / max(1, total_requests)) * 100
        
        return {
            'total_requests': total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': f"{success_rate:.1f}%",
            'rate_limited_count': self.rate_limited_count,
            'consecutive_failures': self.consecutive_failures,
            'simulation_mode': self.simulation_mode,
            'recent_requests_per_hour': len(self.request_history)
        }
        
        # Enhanced tracking with better configuration
        self.request_count = 0
        self.simulation_mode = False
        self.rate_limited_count = 0
        self.consecutive_failures = 0
        self.last_rate_limit = None
        self.min_delay = 15  # Reduced minimum delay
        self.max_delay = 35  # Reduced maximum delay
        
        # Improved success tracking
        self.successful_requests = 0
        self.failed_requests = 0
        self.rate_limit_threshold = 0.25  # More aggressive threshold
        
        # Request timing optimization
        self.last_request_time = datetime.now()
        self.request_history = []  # Track request timing
        self.max_requests_per_hour = 30  # Conservative limit
        
        # Logging configuration
        self.verbose_logging = True
        self.log_file = 'instagram_monitor.log'
        
    def update_headers(self):
        """Enhanced header rotation with better fingerprint randomization"""
        ua = random.choice(self.user_agents)
        
        # Randomize common headers to avoid fingerprinting
        accept_values = [
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '*/*'
        ]
        
        languages = [
            'en-US,en;q=0.9',
            'en-US,en;q=0.5',
            'en-GB,en;q=0.9',
            'en-US,en;q=0.9,es;q=0.8'
        ]
        
        self.session.headers.clear()
        self.session.headers.update({
            'User-Agent': ua,
            'Accept': random.choice(accept_values),
            'Accept-Language': random.choice(languages),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': str(random.choice([0, 1])),
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
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
    
    def load_rate_limit_data(self):
        """Load rate limiting data to track patterns"""
        try:
            if os.path.exists(self.rate_limit_file):
                with open(self.rate_limit_file, 'r') as f:
                    self.rate_limit_data = json.load(f)
            else:
                self.rate_limit_data = {'timestamps': [], 'delays': []}
        except Exception:
            self.rate_limit_data = {'timestamps': [], 'delays': []}
    
    def save_rate_limit_data(self):
        """Save rate limiting patterns for analysis"""
        try:
            with open(self.rate_limit_file, 'w') as f:
                json.dump(self.rate_limit_data, f, indent=2)
        except Exception:
            pass
    
    def calculate_adaptive_delay(self):
        """Smart adaptive delay calculation with request history"""
        current_time = datetime.now()
        
        # Clean old request history (older than 1 hour)
        self.request_history = [
            req_time for req_time in self.request_history 
            if (current_time - req_time).seconds < 3600
        ]
        
        # Check if we're approaching request limits
        recent_requests = len(self.request_history)
        if recent_requests >= self.max_requests_per_hour:
            self.log_message(f"⚠️ Approaching rate limit: {recent_requests}/hour", level='warning')
            return self.max_delay + 30  # Extended delay
        
        # Calculate failure rate
        total_requests = max(1, self.successful_requests + self.failed_requests)
        failure_rate = self.failed_requests / total_requests
        
        if failure_rate > self.rate_limit_threshold:
            # Exponential backoff for failures
            delay = self.max_delay + (failure_rate * 25)
            delay = min(delay, 75)  # Cap at 75 seconds
            self.log_message(f"🐌 High failure rate ({failure_rate:.2%}), using {delay:.1f}s delay", level='warning')
            return delay
        else:
            # Normal adaptive delay
            base_delay = random.uniform(self.min_delay, self.max_delay)
            # Add small buffer based on recent activity
            activity_buffer = min(recent_requests * 0.5, 10)
            return base_delay + activity_buffer
    
    def save_status(self, status_data):
        """Save current status data to file"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            print(f"{Fore.RED}Error saving status: {e}")
    
    def simulate_username_check(self, username):
        """Enhanced simulation with more realistic profile data patterns"""
        time.sleep(random.uniform(1, 3))
        
        # High-profile accounts with realistic follower patterns
        celebrity_accounts = {
            'instagram': (450000000, 500000000),
            'cristiano': (600000000, 650000000),
            'kyliejenner': (380000000, 420000000),
            'selenagomez': (420000000, 450000000),
            'therock': (390000000, 410000000),
            'arianagrande': (370000000, 390000000),
            'kimkardashian': (350000000, 370000000),
            'beyonce': (310000000, 330000000),
            'justinbieber': (290000000, 310000000),
            'taylorswift': (270000000, 290000000)
        }
        
        if username.lower() in celebrity_accounts:
            follower_range = celebrity_accounts[username.lower()]
            status = random.choice(['active_public', 'active_public', 'active_private'])
            profile_data = {
                'followers': random.randint(*follower_range),
                'following': random.randint(50, 500),
                'posts': random.randint(1000, 8000),
                'bio': f"Verified celebrity account simulation for @{username}",
                'verified': True,
                'business_account': random.choice([True, False])
            }
            return status, profile_data
            
        elif any(word in username.lower() for word in ['test', 'fake', 'spam', 'bot']):
            # Higher chance of being banned/not found for suspicious names
            return random.choice(['not_found', 'banned', 'banned', 'not_found']), None
            
        elif len(username) > 15 or any(char in username for char in ['!', '@', '#', '$', '%']):
            return 'not_found', None
            
        else:
            # Realistic distribution for regular accounts
            statuses = ['active_public', 'active_private', 'not_found', 'banned']
            weights = [0.45, 0.35, 0.15, 0.05]
            status = random.choices(statuses, weights=weights)[0]
            
            if status in ['active_public', 'active_private']:
                # Simulate realistic follower distributions
                follower_tiers = [
                    (10, 100, 0.3),      # New users
                    (100, 1000, 0.4),    # Regular users
                    (1000, 10000, 0.2),  # Popular users
                    (10000, 100000, 0.08), # Influencers
                    (100000, 1000000, 0.02) # Major influencers
                ]
                
                tier = random.choices(follower_tiers, weights=[t[2] for t in follower_tiers])[0]
                followers = random.randint(tier[0], tier[1])
                
                profile_data = {
                    'followers': followers,
                    'following': random.randint(max(50, followers // 20), min(2000, followers // 5)),
                    'posts': random.randint(max(5, followers // 100), min(5000, followers // 10)),
                    'bio': f"Simulated profile for educational purposes",
                    'verified': followers > 50000 and random.choice([True, False, False, False]),
                    'business_account': followers > 1000 and random.choice([True, False, False])
                }
                return status, profile_data
            else:
                return status, None
    
    def detect_banned_patterns(self, response_text, status_code):
        """Enhanced banned account detection with more patterns"""
        text_lower = response_text.lower()
        
        # Direct ban indicators
        ban_patterns = [
            "sorry, this page isn't available",
            "page not found",
            "user not found", 
            "account has been disabled",
            "account suspended",
            "violating our terms",
            "violating our community guidelines",
            "this account has been deactivated",
            "account temporarily restricted",
            "account has been removed",
            "content isn't available right now",
            "account doesn't exist",
            "this account is private and you don't follow",  # Not banned, just private
            "sorry, something went wrong",
            "account has been terminated",
            "profile unavailable",
            "user has restricted their account"
        ]
        
        # Check for ban patterns
        for pattern in ban_patterns:
            if pattern in text_lower:
                if "private" in pattern and "don't follow" in pattern:
                    return "active_private"  # Private account, not banned
                elif any(word in pattern for word in ["disabled", "suspended", "violating", "terminated", "removed"]):
                    return "banned"
                elif any(word in pattern for word in ["not found", "doesn't exist", "unavailable"]):
                    return "not_found"
        
        # Check for Instagram's error page structure
        if any(indicator in text_lower for indicator in [
            'class="error-container"',
            'id="react-root"',
            '"Page Not Found"',
            'something went wrong'
        ]):
            return "not_found"
        
        return None
    
    def extract_enhanced_profile_data(self, response_text, username):
        """Enhanced profile data extraction with multiple methods"""
        try:
            # Method 1: JSON extraction from script tags
            profile_data = self.extract_json_profile_data(response_text)
            if profile_data:
                return profile_data
            
            # Method 2: Meta tag extraction
            profile_data = self.extract_meta_profile_data(response_text)
            if profile_data:
                return profile_data
            
            # Method 3: HTML content parsing
            profile_data = self.extract_html_profile_data(response_text)
            if profile_data:
                return profile_data
                
        except Exception as e:
            print(f"{Fore.YELLOW}Profile extraction error: {str(e)[:50]}...")
        
        return None
    
    def extract_json_profile_data(self, html_content):
        """Extract profile data from JSON in script tags"""
        try:
            # Look for various JSON patterns
            json_patterns = [
                r'window\._sharedData\s*=\s*({.+?});',
                r'window\.__additionalDataLoaded\([^,]+,\s*({.+?})\);',
                r'"ProfilePage"\s*:\s*\[({.+?})\]',
                r'"user"\s*:\s*({.+?"edge_followed_by".+?})'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        profile = self.parse_json_profile(data)
                        if profile:
                            return profile
                    except:
                        continue
                        
        except Exception:
            pass
        return None
    
    def parse_json_profile(self, data):
        """Parse profile data from JSON object"""
        try:
            # Navigate through different JSON structures
            user_data = None
            
            # Try different paths to user data
            if isinstance(data, dict):
                # Path 1: Direct user object
                if 'edge_followed_by' in data:
                    user_data = data
                
                # Path 2: Nested in entry_data
                elif 'entry_data' in data:
                    pages = data.get('entry_data', {}).get('ProfilePage', [])
                    if pages and len(pages) > 0:
                        user_data = pages[0].get('graphql', {}).get('user', {})
                
                # Path 3: Direct graphql user
                elif 'graphql' in data:
                    user_data = data.get('graphql', {}).get('user', {})
            
            if user_data and 'edge_followed_by' in user_data:
                return {
                    'followers': user_data.get('edge_followed_by', {}).get('count', 0),
                    'following': user_data.get('edge_follow', {}).get('count', 0),
                    'posts': user_data.get('edge_owner_to_timeline_media', {}).get('count', 0),
                    'bio': user_data.get('biography', ''),
                    'verified': user_data.get('is_verified', False),
                    'business_account': user_data.get('is_business_account', False),
                    'full_name': user_data.get('full_name', ''),
                    'private': user_data.get('is_private', False)
                }
                
        except Exception:
            pass
        return None
    
    def extract_meta_profile_data(self, html_content):
        """Extract profile data from meta tags"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for meta description with follower info
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc and hasattr(meta_desc, 'get'):
                content = meta_desc.get('content', '')
                if content and isinstance(content, str):
                    # Parse patterns like "1.2M Followers, 500 Following, 1,234 Posts"
                    follower_match = re.search(r'([\d,\.]+[KMB]?)\s*Followers', content, re.IGNORECASE)
                    following_match = re.search(r'([\d,\.]+[KMB]?)\s*Following', content, re.IGNORECASE)
                    posts_match = re.search(r'([\d,\.]+[KMB]?)\s*Posts', content, re.IGNORECASE)
                
                    if any([follower_match, following_match, posts_match]):
                        return {
                            'followers': self.parse_number(follower_match.group(1)) if follower_match else 0,
                            'following': self.parse_number(following_match.group(1)) if following_match else 0,
                            'posts': self.parse_number(posts_match.group(1)) if posts_match else 0,
                            'bio': '',
                            'verified': False,
                            'business_account': False
                        }
                    
        except Exception:
            pass
        return None
    
    def extract_html_profile_data(self, html_content):
        """Extract profile data from visible HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            
            # Look for number patterns in the text
            patterns = {
                'followers': [r'([\d,\.]+[KMB]?)\s*followers?', r'Followers\s*([\d,\.]+[KMB]?)'],
                'following': [r'([\d,\.]+[KMB]?)\s*following', r'Following\s*([\d,\.]+[KMB]?)'],
                'posts': [r'([\d,\.]+[KMB]?)\s*posts?', r'Posts\s*([\d,\.]+[KMB]?)']
            }
            
            result = {}
            for key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        result[key] = self.parse_number(match.group(1))
                        break
                else:
                    result[key] = 0
            
            if any(result.values()):
                result.update({
                    'bio': '',
                    'verified': 'verified' in text.lower(),
                    'business_account': 'business' in text.lower()
                })
                return result
                
        except Exception:
            pass
        return None
    
    def parse_number(self, num_str):
        """Parse number strings like '1.2M', '500K', etc."""
        try:
            num_str = num_str.replace(',', '')
            if num_str.endswith('B'):
                return int(float(num_str[:-1]) * 1000000000)
            elif num_str.endswith('M'):
                return int(float(num_str[:-1]) * 1000000)
            elif num_str.endswith('K'):
                return int(float(num_str[:-1]) * 1000)
            else:
                return int(float(num_str))
        except:
            return 0
    
    def check_username_optimized(self, username):
        """Optimized unified username checking with intelligent fallbacks"""
        self.request_count += 1
        
        # Check if simulation mode should be activated
        if self.should_use_simulation():
            if not self.simulation_mode:
                print(f"{Fore.YELLOW}🔄 Switching to simulation mode - Rate limit protection activated")
                print(f"{Fore.CYAN}📚 Educational Mode: Generating realistic data for learning")
                self.simulation_mode = True
            return self.simulate_username_check(username)
        
        # Adaptive delay and header rotation
        delay = self.calculate_adaptive_delay()
        if self.request_count % 3 == 0:
            self.update_headers()
        
        # Record request timing  
        current_time = datetime.now()
        self.request_history.append(current_time)
        self.last_request_time = current_time
        
        self.log_message(f"⏳ Using {delay:.1f}s delay (adaptive rate limiting)", level='info')
        time.sleep(delay)
        
        # Try checking methods in order of reliability
        for method_name, method in self.get_checking_methods().items():
            try:
                result = method(username)
                if self.is_successful_result(result):
                    self.successful_requests += 1
                    self.consecutive_failures = 0
                    print(f"{Fore.GREEN}✅ Success with {method_name}")
                    return result
                elif self.is_rate_limited_result(result):
                    self.handle_rate_limit()
                    return result
                else:
                    print(f"{Fore.YELLOW}⚠️ {method_name} returned: {result[0] if result else 'None'}")
            except Exception as e:
                self.failed_requests += 1
                self.consecutive_failures += 1
                print(f"{Fore.RED}❌ {method_name} failed: {str(e)[:40]}...")
                continue
        
        print(f"{Fore.RED}🚫 All methods failed for @{username}")
        return "error", None
    
    def should_use_simulation(self):
        """Determine if simulation mode should be used"""
        return (self.rate_limited_count >= 2 or 
                self.consecutive_failures >= 3 or 
                self.simulation_mode)
    
    def get_checking_methods(self):
        """Get ordered dictionary of checking methods"""
        return {
            'Mobile API': self.try_mobile_api,
            'Web Scraping': self.try_web_endpoint,
            'Public Endpoint': self.try_public_endpoint
        }
    
    def is_successful_result(self, result):
        """Check if result indicates success"""
        return (result and 
                len(result) >= 2 and 
                result[0] in ['active_public', 'active_private', 'not_found', 'banned'])
    
    def is_rate_limited_result(self, result):
        """Check if result indicates rate limiting"""
        return result and result[0] == 'rate_limited'
    
    def handle_rate_limit(self):
        """Handle rate limiting detection"""
        self.failed_requests += 1
        self.rate_limited_count += 1
        self.consecutive_failures += 1
        self.rate_limit_data['timestamps'].append(datetime.now().isoformat())
        self.save_rate_limit_data()
        print(f"{Fore.RED}🚫 Rate limited - count: {self.rate_limited_count}")
    
    def try_mobile_api(self, username):
        """Try Instagram mobile API endpoint"""
        mobile_url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        headers = {
            'User-Agent': 'Instagram 219.0.0.12.117 Android (29/10; 300dpi; 720x1448; samsung; SM-A505F; a50; exynos9610; en_US; 219.0.0.12.117)',
            'Accept': '*/*',
            'X-IG-App-ID': '936619743392459',
            'X-Instagram-AJAX': '1',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = self.session.get(mobile_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'data' in data and 'user' in data['data']:
                    user_data = data['data']['user']
                    
                    profile_data = {
                        'followers': user_data.get('edge_followed_by', {}).get('count', 0),
                        'following': user_data.get('edge_follow', {}).get('count', 0),
                        'posts': user_data.get('edge_owner_to_timeline_media', {}).get('count', 0),
                        'bio': user_data.get('biography', ''),
                        'verified': user_data.get('is_verified', False),
                        'business_account': user_data.get('is_business_account', False),
                        'full_name': user_data.get('full_name', ''),
                        'private': user_data.get('is_private', False)
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
        
        return 'error', None
    
    def try_web_endpoint(self, username):
        """Try Instagram web endpoint with enhanced detection"""
        url = f"https://www.instagram.com/{username}/"
        
        try:
            response = self.session.get(url, timeout=20, allow_redirects=True)
            
            if response.status_code == 200:
                # Check for banned patterns first
                ban_status = self.detect_banned_patterns(response.text, response.status_code)
                if ban_status:
                    return ban_status, None
                
                # Extract profile data
                profile_data = self.extract_enhanced_profile_data(response.text, username)
                
                # Determine privacy status
                text_lower = response.text.lower()
                if "this account is private" in text_lower:
                    return "active_private", profile_data
                elif any(indicator in text_lower for indicator in ["followers", "following", "posts"]):
                    return "active_public", profile_data
                else:
                    return "active", profile_data
                    
            elif response.status_code == 404:
                return "not_found", None
            elif response.status_code == 429:
                return "rate_limited", None
            else:
                return "unknown", None
                
        except Exception:
            return "error", None
    
    def try_public_endpoint(self, username):
        """Try alternative public endpoint"""
        try:
            # Use a different approach - try the username availability check
            check_url = f"https://www.instagram.com/accounts/web_create_ajax/attempt/"
            
            data = {
                'username': username,
                'email': 'test@example.com',  # Dummy email
                'first_name': 'Test',
                'opt_into_one_tap': 'false'
            }
            
            headers = {
                'X-CSRFToken': 'dummy',
                'X-Instagram-AJAX': '1',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://www.instagram.com/accounts/emailsignup/'
            }
            
            response = self.session.post(check_url, data=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'username' in data.get('errors', {}):
                        # Username exists (taken)
                        return 'active', None
                    elif 'dryrun_passed' in data:
                        # Username available
                        return 'not_found', None
                except:
                    pass
            elif response.status_code == 429:
                return 'rate_limited', None
                
        except Exception:
            pass
            
        return 'error', None
    
    def format_number(self, num):
        """Enhanced number formatting"""
        if num >= 1000000000:
            return f"{num/1000000000:.1f}B"
        elif num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return f"{num:,}"
    
    def print_enhanced_status_update(self, username, current_status, profile_data=None, previous_status=None, previous_profile=None):
        """Enhanced status printing with more profile information"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Enhanced status mapping (treating not_found as banned for monitoring purposes)
        status_info = {
            'active_public': (Fore.GREEN, '✅', 'Active (Public)'),
            'active_private': (Fore.CYAN, '🔒', 'Active (Private)'),
            'active': (Fore.GREEN, '✅', 'Active'),
            'banned': (Fore.RED, '🚫', 'Banned/Unavailable'),
            'not_found': (Fore.RED, '🚫', 'Banned/Unavailable'),  # Treat not found as banned
            'error': (Fore.MAGENTA, '⚠️', 'Error'),
            'rate_limited': (Fore.YELLOW, '⏳', 'Rate Limited'),
            'unknown': (Fore.WHITE, '❓', 'Unknown')
        }
        
        color, emoji, description = status_info.get(current_status, (Fore.WHITE, '❓', current_status))
        
        # Build main status line
        status_line = f"{Fore.WHITE}[{timestamp}] {Style.BRIGHT}@{username}: {color}{emoji} {description}"
        
        # Add comprehensive profile information
        if profile_data and any(v for v in profile_data.values() if v):
            profile_parts = []
            
            # Core metrics
            if profile_data.get('followers', 0) > 0:
                profile_parts.append(f"👥 {self.format_number(profile_data['followers'])} followers")
            
            if profile_data.get('following', 0) > 0:
                profile_parts.append(f"{self.format_number(profile_data['following'])} following")
            
            if profile_data.get('posts', 0) > 0:
                profile_parts.append(f"📸 {self.format_number(profile_data['posts'])} posts")
            
            # Additional info
            extra_info = []
            if profile_data.get('verified'):
                extra_info.append("✓ Verified")
            if profile_data.get('business_account'):
                extra_info.append("🏢 Business")
            if profile_data.get('private'):
                extra_info.append("🔒 Private")
            
            if profile_parts:
                status_line += f"{Fore.WHITE} | {', '.join(profile_parts)}"
            
            if extra_info:
                status_line += f"{Fore.CYAN} ({', '.join(extra_info)})"
            
            # Show bio if available and not too long
            if profile_data.get('bio') and len(profile_data['bio']) < 50:
                status_line += f"{Fore.WHITE} | Bio: \"{profile_data['bio'][:47]}...\""
        
        # Show status changes
        if previous_status and previous_status != current_status:
            prev_desc = status_info.get(previous_status, (Fore.WHITE, '❓', previous_status))[2]
            status_line += f" {Fore.MAGENTA}(Changed from {prev_desc})"
        
        # Show profile metric changes
        if profile_data and previous_profile:
            changes = []
            metrics = ['followers', 'following', 'posts']
            
            for metric in metrics:
                current_val = profile_data.get(metric, 0)
                prev_val = previous_profile.get(metric, 0) if previous_profile else 0
                
                if current_val != prev_val and prev_val > 0:
                    diff = current_val - prev_val
                    if abs(diff) > 0:
                        sign = "+" if diff > 0 else ""
                        changes.append(f"{metric}: {sign}{self.format_number(diff)}")
            
            if changes:
                status_line += f" {Fore.CYAN}(∆ {', '.join(changes)})"
        
        print(status_line)
        
        # Additional line for engagement rate if we have enough data
        if profile_data and profile_data.get('followers', 0) > 0 and profile_data.get('posts', 0) > 0:
            avg_engagement = (profile_data['followers'] / profile_data['posts']) if profile_data['posts'] > 0 else 0
            if avg_engagement > 1000:  # Only show for accounts with decent following
                print(f"{Fore.WHITE}   └─ Estimated avg engagement potential: {self.format_number(avg_engagement)} per post")
    
    def export_data(self, status_data, export_format='json'):
        """Export monitoring data to various formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if export_format == 'json':
            filename = f"instagram_export_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(status_data, f, indent=2)
            print(f"{Fore.GREEN}✅ Data exported to {filename}")
        
        elif export_format == 'csv':
            filename = f"instagram_export_{timestamp}.csv"
            import csv
            
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Username', 'Status', 'Followers', 'Following', 'Posts', 'Verified', 'Business', 'Last Checked'])
                
                for username, data in status_data.items():
                    profile = data.get('profile_data', {}) or {}
                    writer.writerow([
                        username,
                        data.get('status', 'unknown'),
                        profile.get('followers', 0),
                        profile.get('following', 0),
                        profile.get('posts', 0),
                        profile.get('verified', False),
                        profile.get('business_account', False),
                        data.get('last_checked', '')
                    ])
            
            print(f"{Fore.GREEN}✅ Data exported to {filename}")
    
    def monitor_usernames(self, usernames, check_interval=600, export_enabled=True):
        """Enhanced monitoring with better error handling and export options"""
        print(f"{Fore.CYAN}{Style.BRIGHT}🔍 Enhanced Instagram Username Monitor")
        print(f"{Fore.WHITE}Monitoring {len(usernames)} usernames every {check_interval} seconds")
        print(f"{Fore.WHITE}Features: Advanced profile tracking, rate limit protection, export options")
        print(f"{Fore.WHITE}{'='*70}")
        
        current_status = {}
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                print(f"\n{Fore.BLUE}🔄 Check cycle #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                if self.simulation_mode:
                    print(f"{Fore.CYAN}📚 Running in educational simulation mode")
                else:
                    success_rate = self.successful_requests / max(1, self.successful_requests + self.failed_requests)
                    print(f"{Fore.WHITE}📊 Success rate: {success_rate:.1%} | Requests: {self.request_count}")
                
                for i, username in enumerate(usernames):
                    print(f"\n{Fore.CYAN}🔍 Checking @{username}... ({i+1}/{len(usernames)})")
                    
                    status, profile_data = self.check_username_with_minimal_detection(username)
                    previous = self.previous_status.get(username, {})
                    
                    current_status[username] = {
                        'status': status,
                        'profile_data': profile_data,
                        'last_checked': datetime.now().isoformat(),
                        'previous_status': previous.get('status'),
                        'previous_profile': previous.get('profile_data'),
                        'cycle': cycle_count,
                        'check_method': 'simulation' if self.simulation_mode else 'live'
                    }
                    
                    self.print_enhanced_status_update(
                        username, 
                        status, 
                        profile_data,
                        previous.get('status'),
                        previous.get('profile_data')
                    )
                    
                    # Handle rate limiting with intelligent backoff
                    if status == "rate_limited":
                        backoff_time = min(300, 60 * (self.rate_limited_count ** 2))  # Exponential backoff
                        print(f"{Fore.YELLOW}⏳ Rate limited! Backing off for {backoff_time} seconds...")
                        time.sleep(backoff_time)
                    elif not self.simulation_mode:
                        # Short pause between users
                        time.sleep(random.uniform(5, 10))
                
                # Save data and update previous status
                self.save_status(current_status)
                self.previous_status = current_status.copy()
                
                # Export data periodically if enabled
                if export_enabled and cycle_count % 10 == 0:  # Export every 10 cycles
                    self.export_data(current_status, 'json')
                
                # Enhanced summary
                print(f"\n{Fore.BLUE}✅ Cycle #{cycle_count} completed")
                self.print_monitoring_summary(current_status)
                
                print(f"\n{Fore.WHITE}{'='*70}")
                print(f"{Fore.WHITE}⏰ Next check in {check_interval} seconds... (Ctrl+C to stop)")
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}👋 Monitoring stopped by user.")
                if export_enabled:
                    self.export_data(current_status, 'json')
                    self.export_data(current_status, 'csv')
                break
            except Exception as e:
                print(f"{Fore.RED}💥 Error in monitoring loop: {e}")
                print(f"{Fore.YELLOW}🔄 Continuing in 60 seconds...")
                time.sleep(60)
    
    def print_monitoring_summary(self, status_data):
        """Print detailed monitoring summary"""
        # Status distribution
        status_counts = {}
        total_followers = 0
        verified_count = 0
        business_count = 0
        
        for username, data in status_data.items():
            status = data['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
            profile = data.get('profile_data', {})
            if profile:
                total_followers += profile.get('followers', 0)
                if profile.get('verified'):
                    verified_count += 1
                if profile.get('business_account'):
                    business_count += 1
        
        # Combine banned and not_found for display purposes
        combined_counts = status_counts.copy()
        banned_total = combined_counts.get('banned', 0) + combined_counts.get('not_found', 0)
        if banned_total > 0:
            combined_counts['banned'] = banned_total
            if 'not_found' in combined_counts:
                del combined_counts['not_found']
        
        # Print status summary
        print(f"{Fore.WHITE}📊 Status Summary: ", end="")
        status_emojis = {
            'active_public': '✅', 'active_private': '🔒', 'banned': '🚫', 
            'rate_limited': '⏳', 'error': '⚠️'
        }
        
        for status, count in combined_counts.items():
            emoji = status_emojis.get(status, '❓')
            print(f"{emoji}{count} ", end="")
        
        print(f"\n{Fore.WHITE}📈 Total followers tracked: {self.format_number(total_followers)}")
        
        if verified_count > 0:
            print(f"{Fore.WHITE}✓ Verified accounts: {verified_count}")
        if business_count > 0:
            print(f"{Fore.WHITE}🏢 Business accounts: {business_count}")

def main():
    """Enhanced main function with better options"""
    print(f"{Fore.CYAN}{Style.BRIGHT}🔍 Enhanced Instagram Username Status Monitor")
    print(f"{Fore.WHITE}📚 Educational Project - Advanced Features")
    print(f"{Fore.WHITE}Features: Profile tracking, rate limit protection, data export")
    print(f"{Fore.WHITE}{'='*70}")
    
    # Get usernames
    if len(sys.argv) > 1:
        usernames = [arg.lstrip('@') for arg in sys.argv[1:]]  # Remove @ if present
    else:
        print(f"{Fore.YELLOW}Enter Instagram usernames to monitor (without @, one per line, empty line to finish):")
        usernames = []
        while True:
            username = input(f"{Fore.WHITE}Username: ").strip().lstrip('@')
            if not username:
                break
            usernames.append(username)
    
    if not usernames:
        print(f"{Fore.RED}❌ No usernames provided. Exiting...")
        return
    
    # Get monitoring options (handle non-interactive environments)
    try:
        interval_input = input(f"{Fore.YELLOW}Check interval in seconds (default 600): ").strip()
        check_interval = int(interval_input) if interval_input else 600
    except (ValueError, EOFError):
        check_interval = 600
        print(f"{Fore.YELLOW}Using default check interval: {check_interval} seconds")
    
    # Validate interval with better limits
    if check_interval < 300:
        print(f"{Fore.YELLOW}⚠️  For rate limit protection, minimum interval is 300 seconds. Setting to 300.")
        check_interval = 300
    
    # Export option (handle non-interactive environments)
    try:
        export_choice = input(f"{Fore.YELLOW}Enable data export? (y/n, default y): ").strip().lower()
        export_enabled = export_choice != 'n'
    except EOFError:
        export_enabled = True
        print(f"{Fore.YELLOW}Using default export setting: enabled")
    
    print(f"\n{Fore.GREEN}🚀 Starting enhanced monitor")
    print(f"{Fore.GREEN}📝 Usernames: {', '.join(['@' + u for u in usernames])}")
    print(f"{Fore.GREEN}⏰ Check interval: {check_interval} seconds")
    print(f"{Fore.GREEN}💾 Export enabled: {'Yes' if export_enabled else 'No'}")
    print(f"{Fore.WHITE}💡 Features: Adaptive rate limiting, profile tracking, change detection")
    print(f"{Fore.WHITE}🛑 Press Ctrl+C to stop monitoring\n")
    
    # Start enhanced monitoring
    monitor = EnhancedInstagramMonitor()
    monitor.monitor_usernames(usernames, check_interval, export_enabled)

if __name__ == "__main__":
    main()