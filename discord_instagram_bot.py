#!/usr/bin/env python3
"""
Discord Instagram Monitor Bot
Advanced Discord bot for monitoring Instagram accounts with real-time notifications
"""

import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import time
import random
from datetime import datetime, timedelta
from colorama import Fore, Style, init
import requests
from bs4 import BeautifulSoup
import re
import instaloader
from instaloader import Profile, ProfileNotExistsException, PrivateProfileNotFollowedException, LoginException
from cfonts import render

# Initialize colorama
init(autoreset=True)

def display_logo():
    """Display beautiful startup logo using cfonts"""
    try:
        # Create stylish ASCII art for "ASK" using cfonts
        logo = render('ASK', colors=['red', 'cyan'], align='center', size=(80, 20))
        print(logo)
        
        # Add subtitle with styling
        subtitle = "Instagram Monitoring Bot by 2unviolates"
        subtitle_styled = render(subtitle, colors=['cyan'], align='center', font='console', size=(80, 5))
        print(subtitle_styled)
        
        # Add decorative border
        print(f"{Fore.RED}{'='*80}{Style.RESET_ALL}\n")
        
    except Exception as e:
        # Fallback to simple text if cfonts fails
        print(f"\n{Fore.RED}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.RED} █████{Fore.CYAN}  ███████{Fore.RED} ██   ██ {Style.RESET_ALL}")
        print(f"{Fore.RED}██   ██{Fore.CYAN} ██     {Fore.RED} ██  ██  {Style.RESET_ALL}")
        print(f"{Fore.RED}███████{Fore.CYAN} ███████{Fore.RED} █████   {Style.RESET_ALL}")
        print(f"{Fore.RED}██   ██{Fore.CYAN}      ██{Fore.RED} ██  ██  {Style.RESET_ALL}")
        print(f"{Fore.RED}██   ██{Fore.CYAN} ███████{Fore.RED} ██   ██ {Style.RESET_ALL}")
        print(f"{Fore.CYAN}Instagram Monitoring Bot by 2unviolates{Style.RESET_ALL}")
        print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}\n")

# Global monitoring cache and optimization config
monitoring_cache = {}
monitoring_config = {
    'max_concurrent_checks': 3,
    'check_interval': 120,  # 2 minutes instead of 1
    'cache_duration': 180,  # 3 minutes cache
    'batch_size': 8
}

# Notification channel configuration
ban_notification_channel_id = None
unban_notification_channel_id = None

def clean_monitoring_cache(current_time):
    """Clean old entries from monitoring cache"""
    try:
        expired_keys = []
        for key, (cache_time, _) in monitoring_cache.items():
            if (current_time - cache_time).seconds > monitoring_config['cache_duration']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del monitoring_cache[key]
            
        if expired_keys:
            print(f"🧹 Cleaned {len(expired_keys)} expired cache entries")
    except Exception as e:
        print(f"❌ Error cleaning cache: {e}")

def extract_username_from_url(input_text):
    """Extract Instagram username from URL or return username directly"""
    if not input_text:
        return None
    
    input_text = input_text.strip()
    
    # If it's an Instagram URL, extract username
    if 'instagram.com/' in input_text:
        try:
            # Handle various Instagram URL formats
            if '/p/' in input_text:  # Post URL
                return None  # Cannot extract username from post URL
            
            # Profile URL patterns
            patterns = [
                r'instagram\.com/([^/?#]+)',  # Basic pattern
                r'instagram\.com/p/[^/]+/.*?tagged/([^/?#]+)',  # Tagged user
                r'instagram\.com/stories/([^/?#]+)'  # Stories
            ]
            
            for pattern in patterns:
                import re
                match = re.search(pattern, input_text)
                if match:
                    username = match.group(1)
                    # Clean up username
                    username = username.strip('/')  # Remove trailing slash
                    if username and username != 'p' and username != 'stories':
                        return username.lstrip('@')
        except Exception:
            pass
    
    # If not a URL, treat as username
    return input_text.lstrip('@')

def calculate_duration(added_at, current_time):
    """Calculate monitoring duration efficiently"""
    if not added_at:
        return "Unknown"
    
    try:
        start_time = datetime.fromisoformat(added_at)
        duration = current_time - start_time
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes, {seconds} seconds"
        else:
            return f"{minutes} minutes, {seconds} seconds"
    except Exception:
        return "Unknown"

def add_account_info_to_embed(embed, data, result):
    """Add account information to embed efficiently"""
    initial_data = data.get('initial_data', {})
    followers = initial_data.get('followers') or result.get('followers', 0)
    following = initial_data.get('following') or result.get('following', 0)
    posts = initial_data.get('posts') or result.get('posts', 0)
    
    if followers and int(followers) > 0:
        embed.add_field(
            name="Account Info",
            value=f"👥 {monitor.format_number(int(followers))} followers\n👤 {monitor.format_number(int(following))} following\n📸 {monitor.format_number(int(posts))} posts",
            inline=True
        )

# Enhanced Instagram Monitor class for Discord integration
class DiscordInstagramMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        ]
        self.update_headers()
        self.request_count = 0
        self.simulation_mode = False  # Use real Instagram checking
        self.rate_limited_count = 0
        self.consecutive_failures = 0
        
        # Initialize basic monitoring variables
        self.last_check_time = datetime.now()
        
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
            'DNT': '1'
        })
    
    def simulate_username_check(self, username):
        """Enhanced simulation for Discord bot"""
        time.sleep(random.uniform(0.5, 2))
        
        # Celebrity accounts with realistic data
        celebrity_accounts = {
            'instagram': {'status': 'active_public', 'followers': 450000000, 'following': 50, 'posts': 7500, 'verified': True},
            'cristiano': {'status': 'active_public', 'followers': 615000000, 'following': 500, 'posts': 3400, 'verified': True},
            'kyliejenner': {'status': 'active_public', 'followers': 400000000, 'following': 200, 'posts': 5000, 'verified': True},
            'selenagomez': {'status': 'active_public', 'followers': 430000000, 'following': 300, 'posts': 4500, 'verified': True},
            'therock': {'status': 'active_public', 'followers': 395000000, 'following': 100, 'posts': 6200, 'verified': True}
        }
        
        # Banned/problematic accounts for testing
        banned_accounts = {
            'banneduser': {'status': 'banned', 'reason': 'Account suspended for violating community guidelines'},
            'spambot123': {'status': 'banned', 'reason': 'Account disabled due to suspicious activity'},
            'fakeaccount': {'status': 'not_found', 'reason': 'Account not found or deleted'},
            'violatedterms': {'status': 'banned', 'reason': 'Account terminated for terms violation'}
        }
        
        username_lower = username.lower()
        
        if username_lower in celebrity_accounts:
            return celebrity_accounts[username_lower]
        elif username_lower in banned_accounts:
            return banned_accounts[username_lower]
        else:
            # Random realistic profile generation
            statuses = ['active_public', 'active_private', 'not_found', 'banned']
            weights = [0.5, 0.3, 0.15, 0.05]
            status = random.choices(statuses, weights=weights)[0]
            
            if status in ['active_public', 'active_private']:
                followers = random.randint(100, 50000)
                return {
                    'status': status,
                    'followers': followers,
                    'following': random.randint(50, min(2000, followers)),
                    'posts': random.randint(10, min(1000, followers//10)),
                    'verified': followers > 10000 and random.choice([True, False, False])
                }
            else:
                reasons = [
                    'Account suspended for policy violations',
                    'Account not found or deleted by user',
                    'Account temporarily restricted',
                    'Account disabled for suspicious activity'
                ]
                return {
                    'status': status,
                    'followers': 0,
                    'following': 0,
                    'posts': 0,
                    'verified': False,
                    'reason': random.choice(reasons)
                }
    
    def format_number(self, num):
        """Format large numbers with K/M/B suffixes"""
        if num >= 1000000000:
            return f"{num/1000000000:.1f}B"
        elif num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return f"{num:,}"
    
    def check_username_status(self, username):
        """Check Instagram username status using reliable web methods"""
        self.request_count += 1
        
        if self.simulation_mode:
            return self.simulate_username_check(username)
        
        # Use stable web scraping methods first
        return self.check_with_stable_methods(username)
    
    def check_with_stable_methods(self, username):
        """Check Instagram username using stable web scraping methods only"""
        errors = []
        
        try:
            # Add small delay to be respectful
            time.sleep(random.uniform(1, 2))
            
            # Try web scraping first (most stable)
            web_result = self.try_web_scraping(username)
            if web_result and isinstance(web_result, dict):
                status = web_result.get('status')
                if status in ['active_public', 'active_private', 'not_found', 'banned']:
                    return web_result
                elif status == 'rate_limited':
                    self.rate_limited_count += 1
                    errors.append(f"Web scraping: {web_result.get('reason', 'rate limited')}")
                else:
                    errors.append(f"Web scraping: {web_result.get('reason', 'unknown error')}")
            
            # Try mobile API as backup
            mobile_result = self.try_mobile_api(username)
            if mobile_result and isinstance(mobile_result, dict):
                status = mobile_result.get('status')
                if status in ['active_public', 'active_private', 'not_found', 'banned']:
                    return mobile_result
                elif status == 'rate_limited':
                    self.rate_limited_count += 1
                    errors.append(f"Mobile API: {mobile_result.get('reason', 'rate limited')}")
                else:
                    errors.append(f"Mobile API: {mobile_result.get('reason', 'unknown error')}")
                
            # If both fail, return error with proper structure and detailed reasons
            return {
                'status': 'error',
                'followers': 0,
                'following': 0,
                'posts': 0,
                'verified': False,
                'reason': f'All methods failed: {" | ".join(errors) if errors else "No valid response from any method"}'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'followers': 0,
                'following': 0,
                'posts': 0,
                'verified': False,
                'reason': f'Network error: {str(e)[:50]}...'
            }
    
    def check_fallback_methods(self, username):
        """Fallback methods using web scraping to get followers/following data"""
        errors = []
        
        try:
            # Try mobile API first
            mobile_result = self.try_mobile_api(username)
            if mobile_result and isinstance(mobile_result, dict):
                status = mobile_result.get('status')
                if status in ['active_public', 'active_private', 'not_found', 'banned']:
                    return mobile_result
                elif status == 'rate_limited':
                    self.rate_limited_count += 1
                    errors.append(f"Mobile API: rate limited")
                else:
                    errors.append(f"Mobile API: {mobile_result.get('reason', 'error')}")
            
            # Try web scraping as final fallback
            web_result = self.try_web_scraping(username)
            if web_result and isinstance(web_result, dict):
                status = web_result.get('status')
                if status in ['active_public', 'active_private', 'not_found', 'banned']:
                    return web_result
                elif status == 'rate_limited':
                    self.rate_limited_count += 1
                    errors.append(f"Web scraping: rate limited")
                else:
                    errors.append(f"Web scraping: {web_result.get('reason', 'error')}")
                
            # If all methods fail, return error with details
            return {
                'status': 'error',
                'followers': 0,
                'following': 0,
                'posts': 0,
                'verified': False,
                'reason': f'All fallback methods failed: {" | ".join(errors) if errors else "No valid responses"}'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'followers': 0,
                'following': 0,
                'posts': 0,
                'verified': False,
                'reason': f'Fallback error: {str(e)[:50]}...'
            }
    
    def try_mobile_api(self, username):
        """Try mobile API endpoint for profile data - enhanced error handling"""
        try:
            mobile_url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
            
            headers = {
                'User-Agent': 'Instagram 219.0.0.12.117 Android',
                'Accept': 'application/json, */*',
                'X-IG-App-ID': '936619743392459',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            response = self.session.get(mobile_url, headers=headers, timeout=8)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'data' in data and 'user' in data['data']:
                        user_data = data['data']['user']
                        
                        # Extract profile information with fallback for different field structures
                        followers = self._extract_count(user_data, ['edge_followed_by', 'follower_count', 'followers'])
                        following = self._extract_count(user_data, ['edge_follow', 'following_count', 'following'])
                        posts = self._extract_count(user_data, ['edge_owner_to_timeline_media', 'media_count', 'posts'])
                        
                        return {
                            'status': 'active_private' if user_data.get('is_private') else 'active_public',
                            'followers': followers,
                            'following': following,
                            'posts': posts,
                            'verified': user_data.get('is_verified', False),
                            'bio': user_data.get('biography', ''),
                            'full_name': user_data.get('full_name', ''),
                            'reason': 'Private account' if user_data.get('is_private') else 'Public account'
                        }
                        
                except (json.JSONDecodeError, KeyError, AttributeError) as e:
                    return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': f'JSON parsing error: {str(e)[:30]}...'}
                    
            elif response.status_code == 404:
                return {'status': 'not_found', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Account not found'}
            elif response.status_code == 429:
                return {'status': 'rate_limited', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Rate limited'}
            elif response.status_code == 401:
                return {'status': 'rate_limited', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Unauthorized - rate limited'}
            else:
                return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': f'HTTP {response.status_code}'}
                
        except requests.exceptions.Timeout:
            return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Mobile API timeout'}
        except requests.exceptions.ConnectionError:
            return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Mobile API connection error'}
        except Exception as e:
            return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': f'Mobile API error: {str(e)[:20]}...'}
            
        # Should never reach here
        return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Mobile API unknown error'}
    
    def _extract_count(self, user_data, field_names):
        """Extract count data from user_data trying multiple possible field names"""
        for field_name in field_names:
            if field_name in user_data:
                field_data = user_data[field_name]
                if isinstance(field_data, dict) and 'count' in field_data:
                    return field_data['count']
                elif isinstance(field_data, (int, float)):
                    return int(field_data)
        return 0
    
    def try_web_scraping(self, username):
        """Try web scraping for profile data - enhanced and robust"""
        try:
            url = f"https://www.instagram.com/{username}/"
            
            # Use safer headers
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = self.session.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                page_text = response.text.lower()
                
                # Check for banned/deleted accounts first
                if any(phrase in page_text for phrase in [
                    "sorry, this page isn't available",
                    "page not found", 
                    "user not found",
                    "page isn't available"
                ]):
                    return {'status': 'not_found', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Account not found or deleted'}
                
                if any(phrase in page_text for phrase in [
                    "account has been disabled",
                    "account suspended",
                    "violating our terms",
                    "user not found"
                ]):
                    return {'status': 'banned', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Account suspended/disabled'}
                
                # Initialize default values
                followers = 0
                following = 0
                posts = 0
                verified = False
                bio = ''
                full_name = ''
                
                # Try to extract profile data
                try:
                    profile_data = self.extract_enhanced_profile_data(response.text, username)
                    if profile_data:
                        followers = profile_data.get('followers', 0)
                        following = profile_data.get('following', 0)
                        posts = profile_data.get('posts', 0)
                        verified = profile_data.get('verified', False)
                        bio = profile_data.get('bio', '')
                        full_name = profile_data.get('full_name', '')
                except Exception:
                    # If extraction fails, use defaults
                    pass
                
                # Determine account status
                if "this account is private" in page_text:
                    return {
                        'status': 'active_private',
                        'followers': followers,
                        'following': following,
                        'posts': posts,
                        'verified': verified,
                        'bio': bio,
                        'full_name': full_name,
                        'reason': 'Private account'
                    }
                
                # Check if it's a public account
                if any(indicator in page_text for indicator in [
                    "followers", "following", "posts", "biography"
                ]):
                    return {
                        'status': 'active_public',
                        'followers': followers,
                        'following': following,
                        'posts': posts,
                        'verified': verified,
                        'bio': bio,
                        'full_name': full_name,
                        'reason': 'Public account'
                    }
                
                # Default to active if we got a 200 response
                return {
                    'status': 'active_public',
                    'followers': followers,
                    'following': following,
                    'posts': posts,
                    'verified': verified,
                    'bio': bio,
                    'full_name': full_name,
                    'reason': 'Account exists'
                }
                
            elif response.status_code == 404:
                return {'status': 'not_found', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Account not found (HTTP 404)'}
            elif response.status_code == 429:
                return {'status': 'rate_limited', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Rate limited by Instagram'}
            else:
                return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': f'HTTP {response.status_code}'}
                
        except requests.exceptions.Timeout:
            return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Connection error'}
        except Exception as e:
            return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': f'Error: {str(e)[:30]}...'}
            
        # Should never reach here
        return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Unknown error'}
    
    def check_real_instagram_status(self, username):
        """Use the proven methods from instagram_monitor.py"""
        # Check if we should use simulation mode due to rate limiting
        if self.rate_limited_count >= 2 or self.simulation_mode:
            print(f"{Fore.YELLOW}📊 Using simulation mode due to rate limiting protection")
            return self.simulate_username_check(username)
        
        # Rate limiting and header rotation
        if self.request_count % 2 == 0:
            self.update_headers()
        
        # Try alternative method first (from instagram_monitor.py)
        result = self.check_username_alternative(username)
        
        if result and isinstance(result, dict):
            status = result.get('status')
            if status == 'rate_limited':
                self.rate_limited_count += 1
                print(f"{Fore.YELLOW}⚠️ Rate limited detected. Count: {self.rate_limited_count}")
                # If we hit rate limit twice, switch to simulation mode
                if self.rate_limited_count >= 2:
                    print(f"{Fore.YELLOW}🔄 Switching to simulation mode due to repeated rate limiting")
                    self.simulation_mode = True
                    return self.simulate_username_check(username)
                return result
            elif status in ['active_public', 'active_private', 'not_found', 'banned']:
                # Reset consecutive failures on success
                self.consecutive_failures = 0
                return result
            else:
                self.consecutive_failures += 1
        
        # Check if we should switch to simulation mode due to consecutive failures
        if self.consecutive_failures >= 3:
            print(f"{Fore.YELLOW}🔄 Switching to simulation mode due to consecutive failures")
            self.simulation_mode = True
            return self.simulate_username_check(username)
        
        # Fallback to web scraping (from instagram_monitor.py)
        try:
            # Adaptive delay based on failure count
            delay = min(15 + (self.consecutive_failures * 5), 30)
            time.sleep(random.uniform(delay, delay + 10))
            
            url = f"https://www.instagram.com/{username}/"
            response = self.session.get(url, timeout=20, allow_redirects=True)
            
            if response.status_code == 200:
                page_text = response.text.lower()
                
                if any(phrase in page_text for phrase in [
                    "sorry, this page isn't available",
                    "page not found", 
                    "user not found"
                ]):
                    self.consecutive_failures = 0
                    return {'status': 'not_found', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Account not found or deleted'}
                
                if any(phrase in page_text for phrase in [
                    "account has been disabled",
                    "account suspended",
                    "violating our terms"
                ]):
                    self.consecutive_failures = 0
                    return {'status': 'banned', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Account suspended/disabled'}
                
                # Try to extract profile data
                profile_data = self.extract_enhanced_profile_data(response.text, username)
                base_result = {'followers': 0, 'following': 0, 'posts': 0, 'verified': False}
                if profile_data:
                    base_result.update(profile_data)
                
                if "this account is private" in page_text:
                    self.consecutive_failures = 0
                    result = {'status': 'active_private', 'reason': 'Private account'}
                    result.update(base_result)
                    return result
                
                if any(indicator in page_text for indicator in [
                    "followers", "following", "posts"
                ]):
                    self.consecutive_failures = 0
                    result = {'status': 'active_public', 'reason': 'Public account'}
                    result.update(base_result)
                    return result
                
                self.consecutive_failures = 0
                result = {'status': 'active_public', 'reason': 'Account exists'}
                result.update(base_result)
                return result
                
            elif response.status_code == 404:
                self.consecutive_failures = 0
                return {'status': 'not_found', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Account not found (HTTP 404)'}
            elif response.status_code == 429:
                self.rate_limited_count += 1
                self.consecutive_failures += 1
                print(f"{Fore.YELLOW}⚠️ Rate limited in web scraping. Count: {self.rate_limited_count}")
                if self.rate_limited_count >= 2:
                    self.simulation_mode = True
                return {'status': 'rate_limited', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Rate limited by Instagram'}
            else:
                self.consecutive_failures += 1
                return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': f'HTTP {response.status_code}'}
                
        except Exception as e:
            self.consecutive_failures += 1
            return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': f'Error: {str(e)[:50]}...'}
    
    def check_username_alternative(self, username):
        """Alternative checking method using different endpoints (from instagram_monitor.py)"""
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
                        
                        # Extract profile information with fallback for missing fields
                        followers = 0
                        following = 0
                        posts = 0
                        
                        # Try different possible field names
                        if 'edge_followed_by' in user_data:
                            followers = user_data['edge_followed_by'].get('count', 0)
                        elif 'follower_count' in user_data:
                            followers = user_data.get('follower_count', 0)
                        
                        if 'edge_follow' in user_data:
                            following = user_data['edge_follow'].get('count', 0)
                        elif 'following_count' in user_data:
                            following = user_data.get('following_count', 0)
                        
                        if 'edge_owner_to_timeline_media' in user_data:
                            posts = user_data['edge_owner_to_timeline_media'].get('count', 0)
                        elif 'media_count' in user_data:
                            posts = user_data.get('media_count', 0)
                        
                        result = {
                            'status': 'active_private' if user_data.get('is_private') else 'active_public',
                            'followers': followers,
                            'following': following,
                            'posts': posts,
                            'verified': user_data.get('is_verified', False),
                            'bio': user_data.get('biography', ''),
                            'full_name': user_data.get('full_name', ''),
                            'reason': 'Private account' if user_data.get('is_private') else 'Public account'
                        }
                        return result
                        
                except (json.JSONDecodeError, KeyError, AttributeError):
                    return {'status': 'active', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Data parsing error'}
                    
            elif response.status_code == 404:
                return {'status': 'not_found', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Account not found'}
            elif response.status_code == 429:
                return {'status': 'rate_limited', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': 'Rate limited'}
            else:
                return {'status': 'unknown', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'status': 'error', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False, 'reason': f'Error: {str(e)[:50]}...'}
    
    def extract_enhanced_profile_data(self, response_text, username):
        """Enhanced profile data extraction (from instagram_monitor.py)"""
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
            print(f"Profile extraction error: {str(e)[:50]}...")
        
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
                            'verified': False
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
                    'verified': 'verified' in text.lower()
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

# Discord bot setup - fix privileged intents issue
intents = discord.Intents.default()
intents.message_content = True
intents.members = False  # Disable privileged intent
intents.presences = False  # Disable privileged intent
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Global variables for bot state
monitor = DiscordInstagramMonitor()
ban_watch_list = {}  # {channel_id: {username: {data}}}
unban_watch_list = {}  # {channel_id: {username: {data}}}
monitoring_data = {}  # Persistent storage

# Load/Save monitoring data
def load_monitoring_data():
    """Load monitoring data from file"""
    global monitoring_data, ban_watch_list, unban_watch_list
    try:
        if os.path.exists('discord_monitor_data.json'):
            with open('discord_monitor_data.json', 'r') as f:
                data = json.load(f)
                monitoring_data = data.get('monitoring_data', {})
                ban_watch_list = {int(k): v for k, v in data.get('ban_watch_list', {}).items()}
                unban_watch_list = {int(k): v for k, v in data.get('unban_watch_list', {}).items()}
    except Exception as e:
        print(f"Error loading data: {e}")
        monitoring_data = {}
        ban_watch_list = {}
        unban_watch_list = {}

def save_monitoring_data():
    """Save monitoring data to file"""
    try:
        data = {
            'monitoring_data': monitoring_data,
            'ban_watch_list': ban_watch_list,
            'unban_watch_list': unban_watch_list,
            'last_updated': datetime.now().isoformat()
        }
        with open('discord_monitor_data.json', 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving data: {e}")

@bot.event
async def on_ready():
    """Bot startup event"""
    print(f'{Fore.GREEN}{bot.user} is online and ready!')
    print(f'{Fore.CYAN}Instagram Monitor Discord Bot - Advanced Features')
    total_members = sum(guild.member_count or 0 for guild in bot.guilds)
    print(f'{Fore.WHITE}Servers: {len(bot.guilds)} | Users: {total_members}')
    
    # Load existing data
    load_monitoring_data()
    
    # Start background monitoring
    if not background_monitor.is_running():
        background_monitor.start()
    
    print(f'{Fore.GREEN}Background monitoring started')

@bot.command(name='setbanchannel')
async def set_ban_notification_channel(ctx):
    """Set the current channel for ban notifications"""
    global ban_notification_channel_id
    try:
        ban_notification_channel_id = ctx.channel.id
        
        embed = discord.Embed(
            title="🚫 Ban Channel Set Successfully",
            description=f"This channel ({ctx.channel.name}) will now receive all ban notifications.",
            color=0xff0000
        )
        embed.add_field(name="Channel ID", value=str(ctx.channel.id), inline=True)
        embed.add_field(name="Notification Type", value="Ban notifications only", inline=True)
        
        await ctx.send(embed=embed)
        print(f"✅ Ban notification channel set to {ctx.channel.name} ({ctx.channel.id}) by {ctx.author}")
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to set ban notification channel: {str(e)}",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='setunbanchannel')
async def set_unban_notification_channel(ctx):
    """Set the current channel for unban notifications"""
    global unban_notification_channel_id
    try:
        unban_notification_channel_id = ctx.channel.id
        
        embed = discord.Embed(
            title="✅ Unban Channel Set Successfully",
            description=f"This channel ({ctx.channel.name}) will now receive all unban/recovery notifications.",
            color=0x00ff00
        )
        embed.add_field(name="Channel ID", value=str(ctx.channel.id), inline=True)
        embed.add_field(name="Notification Type", value="Unban/recovery notifications only", inline=True)
        
        await ctx.send(embed=embed)
        print(f"✅ Unban notification channel set to {ctx.channel.name} ({ctx.channel.id}) by {ctx.author}")
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to set unban notification channel: {str(e)}",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='setchannel')
async def set_notification_channel(ctx):
    """Set the current channel for notifications (legacy command)"""
    try:
        channel_id = ctx.channel.id
        
        # Update existing ban watch entries to use this channel
        old_channels = list(ban_watch_list.keys())
        for old_channel_id in old_channels:
            if old_channel_id in ban_watch_list:
                ban_watch_list[channel_id] = ban_watch_list.pop(old_channel_id)
        
        # Update existing unban watch entries to use this channel
        old_channels = list(unban_watch_list.keys())
        for old_channel_id in old_channels:
            if old_channel_id in unban_watch_list:
                unban_watch_list[channel_id] = unban_watch_list.pop(old_channel_id)
        
        # Save the updated data
        save_monitoring_data()
        
        embed = discord.Embed(
            title="✅ Channel Set Successfully",
            description=f"This channel ({ctx.channel.name}) will now receive all Instagram monitoring notifications.\n\n**Tip:** Use `!setbanchannel` and `!setunbanchannel` for separate notification channels.",
            color=0x00ff00
        )
        embed.add_field(name="Channel ID", value=str(channel_id), inline=True)
        embed.add_field(name="All Monitoring", value="Moved to this channel", inline=True)
        
        await ctx.send(embed=embed)
        print(f"✅ Channel updated to {ctx.channel.name} ({channel_id}) by {ctx.author}")
        
    except Exception as e:
        await ctx.send(f"❌ Error setting channel: {e}")
        print(f"❌ Error setting channel: {e}")

@bot.command(name='help')
async def help_command(ctx):
    """Show help information"""
    embed = discord.Embed(
        title="Instagram Monitor Bot Commands",
        description="Advanced Instagram account monitoring with real-time notifications",
        color=0x00ff00
    )
    
    embed.add_field(
        name="Monitoring Commands",
        value="""
        `!check <username>` - Check account status once
        `!bancheck <username>` - Monitor for account bans
        `!unbancheck <username>` - Monitor for account unbans
        `!remove <username>` - Stop monitoring account
        """,
        inline=False
    )
    
    embed.add_field(
        name="Information Commands", 
        value="""
        `!list` - Show all monitored accounts
        `!stats` - Show monitoring statistics
        `!status` - Show bot status and performance
        """,
        inline=False
    )
    
    embed.add_field(
        name="Utility Commands",
        value="""
        `!clear` - Clear all monitoring for this channel
        `!export` - Export monitoring data
        `!help` - Show this help message
        """,
        inline=False
    )
    
    embed.set_footer(text="Advanced rate limiting and change detection included")
    await ctx.send(embed=embed, file=discord.File('attached_assets/naruto-shippuden-itachi-uchiha-amaterasu-eyes-paimcqzrmjzhp025_1756983756974.gif'))

@bot.command(name='check')
async def check_account(ctx, username: str = None):
    """Check a single Instagram account status"""
    if not username:
        embed = discord.Embed(
            title="Error",
            description="Please provide a username!\nUsage: `!check <username>`",
            color=0xff0000
        )
        await ctx.send(embed=embed, file=discord.File('attached_assets/naruto-shippuden-itachi-uchiha-amaterasu-eyes-paimcqzrmjzhp025_1756983756974.gif'))
        await ctx.send(embed=embed)
        return
    
    # Remove @ if present
    username = username.lstrip('@')
    
    # Send checking message
    checking_embed = discord.Embed(
        title="Checking Account",
        description=f"Checking @{username}...",
        color=0xffa500
    )
    message = await ctx.send(embed=checking_embed, file=discord.File('attached_assets/naruto-shippuden-itachi-uchiha-amaterasu-eyes-paimcqzrmjzhp025_1756983756974.gif'))
    
    # Check the account
    try:
        result = monitor.check_username_status(username)
        
        # Create result embed
        if result['status'] in ['active_public', 'active_private']:
            color = 0x00ff00 if result['status'] == 'active_public' else 0x0099ff
            status_text = "Active (Public)" if result['status'] == 'active_public' else "Active (Private)"
            
            embed = discord.Embed(
                title=f"@{username}",
                description=f"Account Status Check",
                color=color,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Username", value=f"@{username}", inline=True)
            embed.add_field(name="Current Status", value=f"Active - {status_text}", inline=True)
            embed.add_field(name="Check Type", value="One-time Check", inline=True)
            
            # Always show profile info for active accounts
            followers = result.get('followers', 0)
            following = result.get('following', 0)
            posts = result.get('posts', 0)
            
            if followers and int(followers) > 0:
                embed.add_field(
                    name="Profile Info",
                    value=f"{monitor.format_number(int(followers))} followers, {monitor.format_number(int(following))} following, {monitor.format_number(int(posts))} posts",
                    inline=False
                )
            
            # Add verification status
            if result.get('verified'):
                embed.add_field(name="Verified", value="Yes", inline=True)
            
        else:
            # Banned/Not found account
            embed = discord.Embed(
                title=f"@{username}",
                description=f"Account Status Check",
                color=0xff0000,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Username", value=f"@{username}", inline=True)
            embed.add_field(name="Current Status", value=f"Banned - {result['status'].replace('_', ' ').title()}", inline=True)
            embed.add_field(name="Check Type", value="One-time Check", inline=True)
            
            if result.get('reason'):
                embed.add_field(name="Additional Info", value=str(result['reason']), inline=False)
        
        embed.set_footer(text=f"Checked by {ctx.author.display_name}")
        await message.edit(embed=embed, attachments=[discord.File('attached_assets/naruto-shippuden-itachi-uchiha-amaterasu-eyes-paimcqzrmjzhp025_1756983756974.gif')])
        
    except Exception as e:
        error_embed = discord.Embed(
            title="Error",
            description=f"Failed to check @{username}: {str(e)}",
            color=0xff0000
        )
        await message.edit(embed=error_embed)

@bot.command(name='bancheck')
async def ban_check(ctx, *, user_input: str = None):
    """Start monitoring an account for bans - accepts username or Instagram URL"""
    if not user_input:
        embed = discord.Embed(
            title="❌ Error",
            description="Please provide a username or Instagram profile URL!\nUsage: `!bancheck <username/URL>`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    # Extract username from URL or use as is
    username = extract_username_from_url(user_input)
    if not username:
        embed = discord.Embed(
            title="❌ Error",
            description="Could not extract username from the provided URL.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    channel_id = ctx.channel.id
    
    # Initialize channel if not exists
    if channel_id not in ban_watch_list:
        ban_watch_list[channel_id] = {}
    
    # Check if already monitoring
    if username in ban_watch_list[channel_id]:
        embed = discord.Embed(
            title="⚠️ Already Monitoring",
            description=f"@{username} is already being monitored for bans in this channel.",
            color=0xffa500
        )
        await ctx.send(embed=embed)
        return
    
    # Do initial check
    result = monitor.check_username_status(username)
    
    # Add to watch list
    ban_watch_list[channel_id][username] = {
        'added_by': ctx.author.id,
        'added_at': datetime.now().isoformat(),
        'last_status': result['status'],
        'last_check': datetime.now().isoformat(),
        'initial_data': result
    }
    
    save_monitoring_data()
    
    # Send monitoring status notification to general channel (screenshot format)
    await send_monitoring_status(ctx.channel, username)
    
    # Send confirmation (optional - can remove if you only want the status notification)
    # For now keeping both to ensure compatibility

@bot.command(name='unbancheck')
async def unban_check(ctx, *, user_input: str = None):
    """Start monitoring a banned account for unbans - accepts username or Instagram URL"""
    if not user_input:
        embed = discord.Embed(
            title="❌ Error", 
            description="Please provide a username or Instagram profile URL!\nUsage: `!unbancheck <username/URL>`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    # Extract username from URL or use as is
    username = extract_username_from_url(user_input)
    if not username:
        embed = discord.Embed(
            title="❌ Error",
            description="Could not extract username from the provided URL.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    channel_id = ctx.channel.id
    
    # Initialize channel if not exists
    if channel_id not in unban_watch_list:
        unban_watch_list[channel_id] = {}
    
    # Check if already monitoring
    if username in unban_watch_list[channel_id]:
        embed = discord.Embed(
            title="⚠️ Already Monitoring",
            description=f"@{username} is already being monitored for unbans in this channel.",
            color=0xffa500
        )
        await ctx.send(embed=embed)
        return
    
    # Do initial check
    result = monitor.check_username_status(username)
    
    # Add to unban watch list
    unban_watch_list[channel_id][username] = {
        'added_by': ctx.author.id,
        'added_at': datetime.now().isoformat(),
        'last_status': result['status'],
        'last_check': datetime.now().isoformat(),
        'initial_data': result
    }
    
    save_monitoring_data()
    
    # Send monitoring status notification to general channel (screenshot format)
    await send_monitoring_status(ctx.channel, username)

@bot.command(name='list')
async def list_monitored(ctx):
    """Show all monitored accounts for this channel"""
    channel_id = ctx.channel.id
    
    ban_accounts = ban_watch_list.get(channel_id, {})
    unban_accounts = unban_watch_list.get(channel_id, {})
    
    if not ban_accounts and not unban_accounts:
        embed = discord.Embed(
            title="📋 No Accounts Monitored",
            description="No accounts are currently being monitored in this channel.\nUse `!bancheck <username>` or `!unbancheck <username>` to start monitoring.",
            color=0xffa500
        )
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(
        title="📋 Monitored Accounts",
        description=f"Accounts being monitored in {ctx.channel.name}",
        color=0x0099ff
    )
    
    # Ban monitoring list
    if ban_accounts:
        ban_list = []
        for username, data in ban_accounts.items():
            status_emoji = "✅" if data['last_status'] in ['active_public', 'active_private'] else "🚫"
            added_by = bot.get_user(data['added_by'])
            ban_list.append(f"{status_emoji} @{username} (by {added_by.display_name if added_by else 'Unknown'})")
        
        embed.add_field(
            name="🚫 Ban Monitoring",
            value="\n".join(ban_list[:10]) + (f"\n... and {len(ban_list) - 10} more" if len(ban_list) > 10 else ""),
            inline=False
        )
    
    # Unban monitoring list
    if unban_accounts:
        unban_list = []
        for username, data in unban_accounts.items():
            status_emoji = "🚫" if data['last_status'] in ['banned', 'not_found'] else "✅"
            added_by = bot.get_user(data['added_by'])
            unban_list.append(f"{status_emoji} @{username} (by {added_by.display_name if added_by else 'Unknown'})")
        
        embed.add_field(
            name="🔓 Unban Monitoring", 
            value="\n".join(unban_list[:10]) + (f"\n... and {len(unban_list) - 10} more" if len(unban_list) > 10 else ""),
            inline=False
        )
    
    total_monitored = len(ban_accounts) + len(unban_accounts)
    embed.set_footer(text=f"Total: {total_monitored} accounts monitored")
    await ctx.send(embed=embed)

@bot.command(name='remove')
async def remove_monitoring(ctx, username: str = None):
    """Remove an account from monitoring"""
    if not username:
        embed = discord.Embed(
            title="❌ Error",
            description="Please provide a username!\nUsage: `!remove <username>`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    username = username.lstrip('@')
    channel_id = ctx.channel.id
    removed = False
    
    # Remove from ban watch list
    if channel_id in ban_watch_list and username in ban_watch_list[channel_id]:
        del ban_watch_list[channel_id][username]
        removed = True
    
    # Remove from unban watch list
    if channel_id in unban_watch_list and username in unban_watch_list[channel_id]:
        del unban_watch_list[channel_id][username]
        removed = True
    
    if removed:
        save_monitoring_data()
        embed = discord.Embed(
            title="✅ Monitoring Removed",
            description=f"Stopped monitoring @{username} in this channel.",
            color=0x00ff00
        )
    else:
        embed = discord.Embed(
            title="❌ Not Found",
            description=f"@{username} is not being monitored in this channel.",
            color=0xff0000
        )
    
    await ctx.send(embed=embed)

@bot.command(name='stats')
async def show_stats(ctx):
    """Show monitoring statistics"""
    total_ban_monitors = sum(len(accounts) for accounts in ban_watch_list.values())
    total_unban_monitors = sum(len(accounts) for accounts in unban_watch_list.values())
    total_channels = len(set(list(ban_watch_list.keys()) + list(unban_watch_list.keys())))
    
    embed = discord.Embed(
        title="📊 Bot Statistics",
        description="Instagram Monitor Bot Performance",
        color=0x9932cc
    )
    
    embed.add_field(name="🚫 Ban Monitors", value=f"{total_ban_monitors:,}", inline=True)
    embed.add_field(name="🔓 Unban Monitors", value=f"{total_unban_monitors:,}", inline=True)
    embed.add_field(name="📱 Active Channels", value=f"{total_channels:,}", inline=True)
    
    embed.add_field(name="🔍 Total Requests", value=f"{monitor.request_count:,}", inline=True)
    embed.add_field(name="🤖 Bot Mode", value="Simulation" if monitor.simulation_mode else "Live", inline=True)
    embed.add_field(name="🔄 Status", value="Online", inline=True)
    
    embed.set_footer(text=f"Monitoring since bot startup")
    await ctx.send(embed=embed)

@bot.command(name='clear')
async def clear_monitoring(ctx):
    """Clear all monitoring for this channel (admin only)"""
    if not ctx.author.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Permission Denied", 
            description="Only administrators can clear all monitoring.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    channel_id = ctx.channel.id
    
    ban_count = len(ban_watch_list.get(channel_id, {}))
    unban_count = len(unban_watch_list.get(channel_id, {}))
    
    if channel_id in ban_watch_list:
        del ban_watch_list[channel_id]
    if channel_id in unban_watch_list:
        del unban_watch_list[channel_id]
    
    save_monitoring_data()
    
    embed = discord.Embed(
        title="🧹 Monitoring Cleared",
        description=f"Removed {ban_count} ban monitors and {unban_count} unban monitors from this channel.",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

async def check_account_cached(username, current_time):
    """Check account with caching support"""
    cache_key = f"check_{username}"
    
    # Check cache first
    if cache_key in monitoring_cache:
        cache_time, cached_result = monitoring_cache[cache_key]
        if (current_time - cache_time).seconds < monitoring_config['cache_duration']:
            return cached_result
    
    # If not in cache or expired, check and cache
    result = await asyncio.to_thread(monitor.check_username_status, username)
    monitoring_cache[cache_key] = (current_time, result)
    return result

async def process_accounts_batch(accounts_data, current_time):
    """Process a batch of accounts concurrently with rate limiting"""
    semaphore = asyncio.Semaphore(monitoring_config['max_concurrent_checks'])
    
    async def check_single(item):
        channel, username, data, account_type = item
        async with semaphore:
            try:
                result = await check_account_cached(username, current_time)
                previous_status = data['last_status']
                current_status = result['status']
                
                if previous_status != current_status:
                    print(f"[{current_time.strftime('%H:%M:%S')}] 🔄 {account_type.upper()} MONITOR {username}: {previous_status} -> {current_status}")
                
                # Update data
                data['last_status'] = current_status
                data['last_check'] = current_time.isoformat()
                
                # Determine if notification needed
                active_statuses = ['active_public', 'active_private']
                
                if account_type == 'ban' and previous_status in active_statuses and current_status not in active_statuses:
                    return await send_optimized_notification(channel, username, data, result, current_time, "banned")
                elif account_type == 'ban' and previous_status not in active_statuses and current_status in active_statuses:
                    return await send_optimized_notification(channel, username, data, result, current_time, "recovered")
                elif account_type == 'unban' and previous_status not in active_statuses and current_status in active_statuses:
                    return await send_optimized_notification(channel, username, data, result, current_time, "unbanned")
                
                return 0
            except Exception as e:
                print(f"❌ Error checking {username}: {e}")
                return 0
    
    # Process in batches with small delay between batches
    all_results = 0
    for i in range(0, len(accounts_data), monitoring_config['batch_size']):
        batch = accounts_data[i:i + monitoring_config['batch_size']]
        tasks = [check_single(item) for item in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_results += sum(result for result in results if isinstance(result, int))
        
        # Small delay between batches to be respectful
        if i + monitoring_config['batch_size'] < len(accounts_data):
            await asyncio.sleep(1)
    
    return all_results

async def send_optimized_notification(channel, username, data, result, current_time, notification_type):
    """Send notification matching screenshot format exactly"""
    try:
        if notification_type == "banned":
            # Match screenshot format: "Success! @username has been banned! ❌"
            embed = discord.Embed(
                title="Monitoring Status",
                description=f"Success! @{username} has been banned! ❌",
                color=0xff0000,
                timestamp=current_time
            )
            embed.set_footer(text="Instagram Monitor Bot")
            
        elif notification_type in ["recovered", "unbanned"]:
            # Match screenshot format: "Account Recovered | @username ✅✔️ | Followers: 1381 | ⏱️ Time taken: 16 hours, 22 minutes, 14 seconds"
            duration_text = calculate_duration(data.get('added_at'), current_time)
            
            # Get follower count from result or initial data
            initial_data = data.get('initial_data', {})
            followers = result.get('followers', 0) or initial_data.get('followers', 0)
            
            description = f"Account Recovered | @{username} ✅✔️"
            if followers and int(followers) > 0:
                description += f" | Followers: {followers}"
            description += f" | ⏱️ Time taken: {duration_text}"
            
            embed = discord.Embed(
                title="Monitoring Status",
                description=description,
                color=0x00ff00,
                timestamp=current_time
            )
            embed.set_footer(text="Instagram Monitor Bot")
        else:
            # Fallback
            embed = discord.Embed(
                title="Monitoring Status",
                description=f"@{username} status update",
                color=0x0099ff,
                timestamp=current_time
            )
        
        # Send the notification
        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"❌ Error sending notification: {e}")
            return 0
        
        return 1
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return 0
        
async def send_monitoring_status(channel, username):
    """Send monitoring status notification to general channel"""
    try:
        embed = discord.Embed(
            title="Monitoring Status",
            description=f"User @{username} is being monitored!",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        embed.set_footer(text="Instagram Monitor Bot")
        await channel.send(embed=embed)
        return True
    except Exception as e:
        print(f"❌ Error sending monitoring status: {e}")
        return False

@tasks.loop(seconds=120)  # Every 2 minutes for better performance  
async def background_monitor():
    """Optimized background task with concurrent processing and caching"""
    try:
        current_time = datetime.now()
        notifications_sent = 0
        # Track notifications sent this cycle to prevent duplicates
        sent_notifications = set()  # Format: "username:status_change:channel_id"
        
        # Debug - show total accounts being monitored  
        total_ban_accounts = sum(len(accounts) for accounts in ban_watch_list.values())
        total_unban_accounts = sum(len(accounts) for accounts in unban_watch_list.values()) 
        print(f"[{current_time.strftime('%H:%M:%S')}] Monitoring: {total_ban_accounts} ban accounts, {total_unban_accounts} unban accounts")
        
        # Check ban monitoring list
        for channel_id, accounts in ban_watch_list.items():
            try:
                channel = bot.get_channel(channel_id)
                if not channel:
                    print(f"[{current_time.strftime('%H:%M:%S')}] ❌ Channel {channel_id} not found - use !setchannel command to set a valid channel")
                    # Show available channels as a hint
                    available_channels = [ch for ch in bot.get_all_channels() if hasattr(ch, 'send') and ch.type == discord.ChannelType.text]
                    if available_channels and len(available_channels) <= 3:
                        print(f"[{current_time.strftime('%H:%M:%S')}] 💡 Available channels: {', '.join([f'{ch.name} ({ch.id})' for ch in available_channels])}")
                    continue
                # Check if channel supports sending messages
                if not hasattr(channel, 'send'):
                    print(f"[{current_time.strftime('%H:%M:%S')}] Warning: Channel {channel_id} cannot send messages")
                    continue
            except Exception as e:
                print(f"[{current_time.strftime('%H:%M:%S')}] Error accessing channel {channel_id}: {e}")
                continue
            
            for username, data in accounts.items():
                try:
                    # Check account status
                    result = monitor.check_username_status(username)
                    previous_status = data['last_status']
                    current_status = result['status']
                    
                    if previous_status != current_status:
                        print(f"[{current_time.strftime('%H:%M:%S')}] BAN MONITOR {username}: {previous_status} -> {current_status}")
                    
                    # Update data
                    data['last_status'] = current_status
                    data['last_check'] = current_time.isoformat()
                    
                    # Simplified ban detection: active → any other status = banned
                    active_statuses = ['active_public', 'active_private']
                    
                    # Check for ban (active → any other status) 
                    if (previous_status in active_statuses and current_status not in active_statuses):
                        notification_key = f"{username}:banned"
                        if notification_key not in sent_notifications:
                            # Use dedicated ban channel if set, otherwise use monitoring channel
                            target_channel = bot.get_channel(ban_notification_channel_id) if ban_notification_channel_id else channel
                            if target_channel:
                                sent_count = await send_optimized_notification(
                                    target_channel, username, data, result, current_time, "banned"
                                )
                                notifications_sent += sent_count
                                sent_notifications.add(notification_key)
                    
                    # Check for recovery (any other status → active) - Only notify once per username per cycle
                    elif (previous_status not in active_statuses and current_status in active_statuses):
                        notification_key = f"{username}:recovered"
                        if notification_key not in sent_notifications:
                            # Use dedicated unban channel if set, otherwise use monitoring channel
                            target_channel = bot.get_channel(unban_notification_channel_id) if unban_notification_channel_id else channel
                            if target_channel:
                                sent_count = await send_optimized_notification(
                                    target_channel, username, data, result, current_time, "recovered"
                                )
                                notifications_sent += sent_count
                                sent_notifications.add(notification_key)
                    
                    # Small delay between checks
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error checking {username}: {e}")
        
        # Check unban monitoring list
        for channel_id, accounts in unban_watch_list.items():
            try:
                channel = bot.get_channel(channel_id)
                if not channel:
                    print(f"[{current_time.strftime('%H:%M:%S')}] ❌ Unban channel {channel_id} not found - use !setchannel command to set a valid channel")
                    continue
                if not hasattr(channel, 'send'):
                    print(f"[{current_time.strftime('%H:%M:%S')}] Warning: Unban channel {channel_id} cannot send messages")
                    continue
            except Exception as e:
                print(f"[{current_time.strftime('%H:%M:%S')}] Error accessing unban channel {channel_id}: {e}")
                continue
            
            for username, data in accounts.items():
                try:
                    # Check account status
                    result = monitor.check_username_status(username)
                    previous_status = data['last_status']
                    current_status = result['status']
                    
                    if previous_status != current_status:
                        print(f"[{current_time.strftime('%H:%M:%S')}] UNBAN MONITOR {username}: {previous_status} -> {current_status}")
                    
                    # Update data
                    data['last_status'] = current_status
                    data['last_check'] = current_time.isoformat()
                    
                    # Simplified unban detection: any other status → active = unbanned
                    active_statuses = ['active_public', 'active_private']
                    
                    if (previous_status not in active_statuses and current_status in active_statuses):
                        # Check if we already sent a recovery notification for this username in this cycle
                        notification_key = f"{username}:unbanned"
                        if notification_key not in sent_notifications:
                            # Use dedicated unban channel if set, otherwise use monitoring channel
                            target_channel = bot.get_channel(unban_notification_channel_id) if unban_notification_channel_id else channel
                            if target_channel:
                                sent_count = await send_optimized_notification(
                                    target_channel, username, data, result, current_time, "unbanned"
                                )
                                notifications_sent += sent_count
                                sent_notifications.add(notification_key)
                    
                    # Small delay between checks
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error checking {username}: {e}")
        
        # Save data after all checks
        save_monitoring_data()
        print(f"[{current_time.strftime('%H:%M:%S')}] Background monitoring completed. Sent {notifications_sent} notifications")
    
    except Exception as e:
        current_time = datetime.now()
        print(f"[{current_time.strftime('%H:%M:%S')}] Background monitor error: {e}")

# Error handling
@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Argument",
            description=f"Missing required argument. Use `!help` for command usage.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
    
    else:
        embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred: {str(error)}",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        print(f"Command error: {error}")

# Run the bot
if __name__ == "__main__":
    # Display beautiful logo
    display_logo()
    
    # Use Discord bot token from secrets
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print(f"{Fore.RED}❌ DISCORD_BOT_TOKEN not found in environment variables!")
        print(f"{Fore.YELLOW}Please add your Discord bot token to Replit Secrets.")
        exit(1)
    
    print(f"{Fore.CYAN}🚀 Starting Instagram Monitor Discord Bot...")
    print(f"{Fore.WHITE}Features: Real-time ban/unban monitoring, profile tracking, advanced notifications")
    
    try:
        bot.run(token)
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to start bot: {e}")
        print(f"{Fore.YELLOW}Make sure your Discord bot token is correct and the bot has proper permissions.")