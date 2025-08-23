# Chiikawa Online Market Scraper

## Overview

This is a Python-based web scraping tool designed to extract product inventory information from the Chiikawa Online Market (chiikawamarket.jp). The application scrapes product data including prices, availability status, descriptions, and collection information, then processes and exports the data in various formats (CSV, Excel). The system is built with modularity in mind, featuring separate components for scraping, data processing, configuration management, and utilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Components

**Scraper Module (`scraper.py`)**
- Implements the main `ChiikawaMarketScraper` class using requests and BeautifulSoup
- Handles HTTP session management with proper headers and user agent spoofing
- Includes retry logic with exponential backoff for robust error handling
- Supports filtering by collections and product status
- Uses rate limiting to avoid overwhelming the target server

**Data Processing (`data_processor.py`)**
- `DataProcessor` class converts scraped data into pandas DataFrames
- Handles data cleaning, type conversion, and optimization
- Provides analysis capabilities and multiple export formats
- Includes data validation and error handling

**Configuration Management (`config.py`)**
- `ScrapingConfig` dataclass with comprehensive settings
- Validates configuration parameters with sensible defaults
- Supports different scraping modes (fast vs thorough)
- Configurable rate limiting, retry behavior, and output options

**Utilities (`utils.py`)**
- Retry decorator with exponential backoff for resilient operations
- Text cleaning and price parsing utilities
- Common helper functions used across modules

**Main Application (`main.py`)**
- Command-line interface with argument parsing
- Orchestrates the scraping process and data export
- Configurable logging with file and console output
- Support for multiple output formats and collection filtering

### Design Patterns

**Modular Architecture**: Clear separation of concerns with dedicated modules for scraping, processing, configuration, and utilities.

**Configuration-Driven**: Centralized configuration management allowing easy customization of scraping behavior without code changes.

**Error Resilience**: Comprehensive error handling with retry mechanisms, timeouts, and graceful degradation.

**Data Pipeline**: Clean flow from raw scraped data through processing to final export formats.

### Key Features

- **Product categorization by stock status**: 在庫あり, 売り切れ, 新着商品, 予約商品
- **Multiple export formats**: CSV, Excel with statistics sheets
- **Collection/store organization**: Filter by specific product collections
- **Comprehensive product data**: ID, name, URL, price, collection, stock status, timestamp
- **Advanced filtering**: By collection and stock status
- **Respectful scraping**: Configurable delays and rate limiting
- **Robust error handling**: Retry mechanisms, timeouts, and graceful degradation
- **Data validation and cleaning**: Automatic text processing and price parsing
- **Statistical analysis**: Automatic generation of summary statistics and insights

## External Dependencies

### Python Libraries
- **requests**: HTTP client for web scraping
- **beautifulsoup4**: HTML parsing and navigation
- **pandas**: Data manipulation and analysis
- **openpyxl**: Excel file generation (implied by Excel export functionality)

### Target Website
- **chiikawamarket.jp**: Primary data source for product information
- Scrapes product listings, prices, availability, and collection data

### System Dependencies
- Python 3.7+ runtime environment
- Standard library modules: argparse, logging, datetime, pathlib, re, time, urllib

### Data Storage
- File-based output (CSV, Excel, JSON formats)
- No persistent database storage - operates as a data extraction tool