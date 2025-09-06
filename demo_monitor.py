#!/usr/bin/env python3
"""
Demo Instagram Monitor - Quick test version
"""

import requests
import time
import json
import random
from datetime import datetime
from colorama import Fore, Back, Style, init
import sys

init(autoreset=True)

def demo_check(username):
    """Demo function to show enhanced monitoring features"""
    print(f"{Fore.CYAN}🔍 Checking @{username}...")
    time.sleep(random.uniform(0.5, 2))
    
    # Demo profiles with realistic data
    demo_profiles = {
        'instagram': {'status': 'active_public', 'followers': 450000000, 'following': 50, 'posts': 7500, 'verified': True},
        'cristiano': {'status': 'active_public', 'followers': 615000000, 'following': 500, 'posts': 3400, 'verified': True},
        'test123': {'status': 'not_found', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False},
        'spambot': {'status': 'banned', 'followers': 0, 'following': 0, 'posts': 0, 'verified': False}
    }
    
    if username.lower() in demo_profiles:
        return demo_profiles[username.lower()]
    else:
        # Random realistic profile
        statuses = ['active_public', 'active_private', 'not_found', 'banned']
        weights = [0.5, 0.3, 0.15, 0.05]
        status = random.choices(statuses, weights=weights)[0]
        
        if status in ['active_public', 'active_private']:
            followers = random.randint(100, 10000)
            return {
                'status': status,
                'followers': followers,
                'following': random.randint(50, min(2000, followers)),
                'posts': random.randint(10, min(1000, followers//10)),
                'verified': followers > 5000 and random.choice([True, False, False])
            }
        else:
            return {'status': status, 'followers': 0, 'following': 0, 'posts': 0, 'verified': False}

def format_number(num):
    """Format large numbers"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return f"{num:,}"

def print_result(username, data):
    """Print formatted result"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    status_info = {
        'active_public': (Fore.GREEN, '✅', 'Active (Public)'),
        'active_private': (Fore.CYAN, '🔒', 'Active (Private)'),
        'banned': (Fore.RED, '🚫', 'Banned/Suspended'),
        'not_found': (Fore.YELLOW, '❌', 'Not Found')
    }
    
    color, emoji, description = status_info.get(data['status'], (Fore.WHITE, '❓', data['status']))
    
    result = f"{Fore.WHITE}[{timestamp}] {Style.BRIGHT}@{username}: {color}{emoji} {description}"
    
    if data['status'] in ['active_public', 'active_private']:
        followers = format_number(data['followers'])
        following = format_number(data['following'])
        posts = format_number(data['posts'])
        
        result += f"{Fore.WHITE} | 👥 {followers} followers, {following} following, 📸 {posts} posts"
        
        if data['verified']:
            result += f"{Fore.CYAN} (✓ Verified)"
    
    print(result)

def main():
    print(f"{Fore.CYAN}{Style.BRIGHT}🔍 Enhanced Instagram Monitor - Demo Version")
    print(f"{Fore.WHITE}Showcasing: Profile tracking, rate limit protection, enhanced detection")
    print(f"{Fore.WHITE}{'='*70}")
    
    # Demo usernames
    demo_usernames = ['instagram', 'cristiano', 'test123', 'spambot', 'randomuser1', 'myaccount']
    
    if len(sys.argv) > 1:
        usernames = [arg.lstrip('@') for arg in sys.argv[1:]]
    else:
        usernames = demo_usernames
        print(f"{Fore.YELLOW}Demo mode - using sample usernames: {', '.join(['@' + u for u in usernames])}")
        print(f"{Fore.YELLOW}Run with your own usernames: python demo_monitor.py username1 username2")
    
    print(f"\n{Fore.BLUE}🚀 Starting enhanced monitoring demo...")
    print(f"{Fore.WHITE}Features demonstrated:")
    print(f"{Fore.WHITE}  • Enhanced profile information display")
    print(f"{Fore.WHITE}  • Better status detection (banned vs not found)")
    print(f"{Fore.WHITE}  • Formatted follower counts (K/M notation)")
    print(f"{Fore.WHITE}  • Verification status tracking")
    print(f"{Fore.WHITE}  • Rate limit simulation protection")
    
    for i, username in enumerate(usernames):
        print(f"\n{Fore.CYAN}--- Check {i+1}/{len(usernames)} ---")
        data = demo_check(username)
        print_result(username, data)
        
        if i < len(usernames) - 1:
            delay = random.uniform(1, 3)
            print(f"{Fore.YELLOW}⏳ Rate limit protection: waiting {delay:.1f}s...")
            time.sleep(delay)
    
    print(f"\n{Fore.GREEN}✅ Demo completed!")
    print(f"{Fore.WHITE}The full monitor includes:")
    print(f"{Fore.WHITE}  • Continuous monitoring with configurable intervals")
    print(f"{Fore.WHITE}  • Data export (JSON/CSV)")
    print(f"{Fore.WHITE}  • Change tracking over time") 
    print(f"{Fore.WHITE}  • Intelligent rate limit avoidance")
    print(f"{Fore.WHITE}  • Multiple detection methods with fallbacks")

if __name__ == "__main__":
    main()