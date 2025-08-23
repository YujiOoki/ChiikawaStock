#!/usr/bin/env python3
"""
Debug script to examine HTML structure
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def debug_page_structure():
    url = "https://chiikawamarket.jp/collections/newitems?page=1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    response = requests.get(url, headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Content length: {len(response.content)}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 商品リンクを探す
    print("\n=== Looking for product links ===")
    
    # パターン1: /products/ を含むリンク
    products_links1 = soup.find_all('a', href=re.compile(r'/products/'))
    print(f"Links with '/products/': {len(products_links1)}")
    
    # パターン2: collections/*/products/ を含むリンク
    products_links2 = soup.find_all('a', href=re.compile(r'/collections/.*/products/'))
    print(f"Links with '/collections/.*/products/': {len(products_links2)}")
    
    # 最初の商品リンクを詳しく調べる
    if products_links2:
        first_link = products_links2[0]
        print(f"\nFirst product link:")
        print(f"  href: {first_link.get('href')}")
        print(f"  text: {first_link.get_text().strip()[:100]}")
        print(f"  parent tag: {first_link.parent.name}")
        print(f"  parent class: {first_link.parent.get('class')}")
        
        # 商品情報を抽出してみる
        parent = first_link.parent
        while parent and parent.name not in ['div', 'article', 'li']:
            parent = parent.parent
            
        if parent:
            print(f"\nProduct container:")
            print(f"  tag: {parent.name}")
            print(f"  class: {parent.get('class')}")
            
            # 価格を探す
            price_elem = parent.find(text=re.compile(r'¥'))
            if price_elem:
                print(f"  price text: {price_elem.strip()}")
    
    # 商品コンテナを探す
    print("\n=== Looking for product containers ===")
    containers1 = soup.find_all(['div', 'article'], class_=re.compile(r'product|item|card'))
    print(f"Containers with product/item/card class: {len(containers1)}")
    
    containers2 = soup.find_all(['div', 'li'], class_=re.compile(r'grid|collection'))
    print(f"Containers with grid/collection class: {len(containers2)}")
    
    # すべてのリンクを調べる
    all_links = soup.find_all('a', href=True)
    product_pattern_links = [link for link in all_links if '/products/' in link.get('href', '')]
    print(f"\nTotal links: {len(all_links)}")
    print(f"Links containing '/products/': {len(product_pattern_links)}")
    
    if product_pattern_links:
        print(f"\nFirst few product links:")
        for i, link in enumerate(product_pattern_links[:3]):
            print(f"  {i+1}. {link.get('href')}")
    
    # JSON-LDやスクリプトタグ内のデータを探す
    print("\n=== Looking for embedded JSON data ===")
    
    # JSON-LDを探す
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    print(f"JSON-LD scripts found: {len(json_ld_scripts)}")
    
    # その他のスクリプトタグを探す
    all_scripts = soup.find_all('script')
    print(f"Total script tags: {len(all_scripts)}")
    
    # window.で始まるJavaScriptデータを探す
    for script in all_scripts:
        if script.string:
            script_content = script.string.strip()
            if 'window.' in script_content and ('product' in script_content.lower() or 'collection' in script_content.lower()):
                print(f"\nFound potential product data in script:")
                print(script_content[:200] + "..." if len(script_content) > 200 else script_content)
    
    # divタグに埋め込まれたデータ属性を探す
    print("\n=== Looking for data attributes ===")
    divs_with_data = soup.find_all('div', attrs={'data-collection': True})
    print(f"Divs with data-collection: {len(divs_with_data)}")
    
    divs_with_products = soup.find_all('div', attrs={'data-products': True})
    print(f"Divs with data-products: {len(divs_with_products)}")
    
    # Shopifyの一般的なセレクタを試す
    print("\n=== Looking for Shopify-specific selectors ===")
    
    # 商品グリッド
    product_grid = soup.find('div', {'id': 'product-grid'})
    if product_grid:
        print("Found #product-grid")
    
    # データ属性付きのdiv
    collection_divs = soup.find_all('div', class_=re.compile(r'collection|grid'))
    print(f"Divs with collection/grid classes: {len(collection_divs)}")
    
    if collection_divs:
        print(f"First collection div classes: {collection_divs[0].get('class')}")

if __name__ == "__main__":
    debug_page_structure()