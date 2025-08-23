#!/usr/bin/env python3
"""
Working Chiikawa scraper based on exact debug script approach
"""

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime
import argparse
import logging
from utils import clean_text, parse_price

def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_chiikawa_products(collection_name='newitems', max_products=50):
    """Chiikawa商品を取得 - debug_scraperで動作した方法を使用"""
    url = f"https://chiikawamarket.jp/collections/{collection_name}?page=1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    response = requests.get(url, headers=headers)
    logging.info(f"Status code: {response.status_code}, Content length: {len(response.content)}")
    
    # Use the exact same approach as debug_scraper.py
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # debug_scraperで成功したパターンを使用
    products_links = soup.find_all('a', href=re.compile(rf'/collections/{collection_name}/products/'))
    logging.info(f"Found {len(products_links)} product links")
    
    if not products_links:
        # 代替パターンを試す
        all_links = soup.find_all('a', href=True)
        product_pattern_links = [link for link in all_links if '/products/' in link.get('href', '')]
        logging.info(f"Alternative search found {len(product_pattern_links)} product links")
        products_links = product_pattern_links[:max_products] if product_pattern_links else []
    
    products = []
    
    for i, link in enumerate(products_links[:max_products]):
        try:
            href = link.get('href', '')
            if href.startswith('/'):
                product_url = f"https://chiikawamarket.jp{href}"
            else:
                product_url = href
            
            # 商品ID
            product_id = href.split('/')[-1] if '/' in href else f"product_{i+1}"
            
            # 商品名
            title_text = clean_text(link.get_text()) if link.get_text().strip() else "商品名不明"
            
            # 価格を親要素から探す
            price = None
            current = link.parent
            for _ in range(10):  # 最大10階層まで遡る
                if current:
                    text_content = current.get_text()
                    if '¥' in text_content:
                        price = parse_price(text_content)
                        if price:
                            break
                    current = current.parent
                else:
                    break
            
            # 在庫状況の判定
            stock_status = "在庫あり"  # デフォルト
            parent_text = link.parent.get_text().lower() if link.parent else ""
            
            if any(keyword in parent_text for keyword in ['売り切れ', 'sold out', '完売', '在庫なし']):
                stock_status = "売り切れ"
            elif any(keyword in parent_text for keyword in ['予約', 'pre-order']):
                stock_status = "予約商品"
            
            # newitems コレクションの商品は新着商品とみなす
            if collection_name == 'newitems':
                stock_status = "新着商品"
            
            product = {
                '商品ID': product_id,
                '商品名': title_text,
                '商品URL': product_url,
                '価格': price,
                'コレクション': collection_name,
                '在庫状況': stock_status,
                '取得日時': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            products.append(product)
            logging.debug(f"Product {i+1}: {title_text} - ¥{price} ({stock_status})")
            
        except Exception as e:
            logging.warning(f"Error processing product {i+1}: {str(e)}")
            continue
    
    return products

def export_data(products, format_type, filename=None):
    """データを指定された形式で出力"""
    if not products:
        logging.warning("出力するデータがありません")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = filename or f"chiikawa_products_{timestamp}"
    
    df = pd.DataFrame(products)
    
    if format_type in ['csv', 'both']:
        csv_file = f"{base_filename}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logging.info(f"CSVファイル出力: {csv_file}")
    
    if format_type in ['excel', 'both']:
        excel_file = f"{base_filename}.xlsx"
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # メインデータ
            df.to_excel(writer, sheet_name='商品データ', index=False)
            
            # 統計情報
            stats = []
            stats.append(['項目', '値'])
            stats.append(['総商品数', len(df)])
            stats.append(['取得日時', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            stats.append(['', ''])
            stats.append(['在庫状況', '商品数'])
            
            for status, count in df['在庫状況'].value_counts().items():
                stats.append([status, count])
            
            if not df['価格'].isna().all():
                stats.extend([
                    ['', ''],
                    ['価格統計', ''],
                    ['平均価格', f"¥{df['価格'].mean():.0f}"],
                    ['最高価格', f"¥{df['価格'].max():.0f}"],
                    ['最低価格', f"¥{df['価格'].min():.0f}"]
                ])
            
            stats_df = pd.DataFrame(stats)
            stats_df.to_excel(writer, sheet_name='統計情報', index=False, header=False)
        
        logging.info(f"Excelファイル出力: {excel_file}")

def main():
    parser = argparse.ArgumentParser(description='ちいかわオンラインマーケット スクレイピングツール')
    parser.add_argument('--collections', '-c', default='newitems', help='取得するコレクション')
    parser.add_argument('--max-products', '-m', type=int, default=50, help='最大商品数')
    parser.add_argument('--format', '-f', choices=['csv', 'excel', 'both'], default='csv', help='出力形式')
    parser.add_argument('--output', '-o', help='出力ファイル名')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細ログ')
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    collections = [c.strip() for c in args.collections.split(',')]
    all_products = []
    
    for collection in collections:
        logging.info(f"コレクション '{collection}' を処理中...")
        products = scrape_chiikawa_products(collection, args.max_products)
        all_products.extend(products)
        logging.info(f"コレクション '{collection}': {len(products)} 商品を取得")
    
    if not all_products:
        logging.error("商品データを取得できませんでした")
        return
    
    # 結果統計
    df = pd.DataFrame(all_products)
    print(f"\n📊 スクレイピング結果:")
    print(f"🎯 総商品数: {len(df)} 件")
    print(f"📦 在庫状況分布:")
    for status, count in df['在庫状況'].value_counts().items():
        print(f"  {status}: {count} 件")
    
    if not df['価格'].isna().all():
        print(f"💰 価格統計:")
        print(f"  平均価格: ¥{df['価格'].mean():.0f}")
        print(f"  価格範囲: ¥{df['価格'].min():.0f} - ¥{df['価格'].max():.0f}")
    
    # データ出力
    export_data(all_products, args.format, args.output)

if __name__ == "__main__":
    main()