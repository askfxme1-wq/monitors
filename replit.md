# Instagram Username Monitor

## Overview

An educational Python project for monitoring Instagram username status with advanced features. The application provides real-time checking of Instagram usernames to determine their availability, account status, and comprehensive profile information including follower counts, verification status, and engagement metrics. It includes both a production-ready enhanced monitor and a demo version for testing purposes.

## Recent Changes (September 2025)

**Enhanced Profile Information Display:**
- Added comprehensive follower/following/posts count tracking
- Implemented K/M/B number formatting for large follower counts
- Added verification status and business account detection
- Enhanced profile data extraction from multiple sources (JSON, meta tags, HTML)

**Improved Banned Account Detection:**
- Enhanced pattern matching for banned, suspended, and disabled accounts
- Better distinction between "not found" vs "banned" status
- Added detection for various Instagram error messages and account states

**Minimal Rate Detection System:**
- Implemented adaptive delay calculation based on success/failure rates
- Added intelligent rate limit avoidance with exponential backoff
- Enhanced request success tracking and automatic simulation mode switching
- Rate limit pattern tracking and analysis for optimization

**Advanced Features:**
- Data export functionality (JSON and CSV formats)
- Enhanced error handling with multiple endpoint fallbacks
- Improved user agent rotation and header randomization
- Better profile change detection and historical tracking

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Application Design

The system is built around a class-based Python architecture with the main `EnhancedInstagramMonitor` class handling all monitoring operations. The application uses object-oriented principles to encapsulate functionality and maintain state across multiple requests.

### Web Scraping and Request Management

The monitor uses the `requests` library with session management to handle HTTP requests to Instagram. It implements sophisticated user agent rotation using a predefined list of common browser user agents to avoid detection. The system includes rate limiting protection with configurable delays between requests and tracks request counts to prevent hitting Instagram's anti-bot measures.

### Status Tracking and Persistence

The application maintains persistent storage of monitoring results using JSON files (`instagram_status.json` and `rate_limits.json`). This allows the system to track changes over time and maintain state between application restarts. The status tracking includes historical data comparison to detect when usernames become available or unavailable.

### Error Handling and Resilience

The monitor implements comprehensive error handling with retry mechanisms, rate limit detection, and fallback modes. It includes a simulation mode for testing without making actual requests to Instagram, and tracks consecutive failures to implement exponential backoff strategies.

### User Interface and Output

The system uses the `colorama` library to provide colored terminal output for better user experience. It formats large numbers appropriately and provides clear status indicators for different account states (active, private, not found, banned, verified).

### Threading and Concurrent Operations

The application is designed with threading capabilities to handle multiple username checks concurrently while respecting rate limits. This allows for efficient batch processing of username lists.

## External Dependencies

**Core Libraries:**
- `requests` - HTTP client for web scraping Instagram pages
- `beautifulsoup4` - HTML parsing for extracting profile information
- `colorama` - Terminal color formatting for enhanced user interface

**Standard Library Dependencies:**
- `json` - Data serialization for status persistence
- `datetime` - Timestamp management and rate limiting calculations
- `time` - Request delays and timing controls
- `random` - User agent rotation and delay randomization
- `threading` - Concurrent username checking capabilities
- `urllib.parse` - URL encoding for safe username handling
- `re` - Regular expressions for data validation
- `os` - File system operations for status persistence
- `sys` - System-level operations and exit handling

**Target Service:**
- Instagram web interface - Primary data source for username status checking (educational purposes only)

**Optional Dependencies:**
- `fake_useragent` - Advanced user agent rotation (commented out, can be added for enhanced stealth)