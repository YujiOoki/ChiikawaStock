"""
ちいかわオンラインマーケット スクレイピングモジュール
Chiikawa Online Market Scraping Module
"""

import re
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Any
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from config import ScrapingConfig
from utils import retry_on_failure, clean_text, parse_price


class ChiikawaMarketScraper:
    """ちいかわオンラインマーケットスクレイパー"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.base_url = "https://chiikawamarket.jp"
        self.session = self._create_session()
        self.logger = logging.getLogger(__name__)
        
        # 既知のコレクション
        self.known_collections = [
            'newitems', 'chiikawarestaurant', 'tokyomiyage', 'ramenbuta',
            'tenshitoakuma', 'rakko20250718', 'chiikawa-sushi', 'chiikawabakery',
            'magicalchiikawa', 'shisamatsuri', 'smartphonesticker', 'parallelworld',
            'oshikatsu'
        ]
    
    def _create_session(self) -> requests.Session:
        """HTTPセッションを作成"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        return session
    
    @retry_on_failure(max_retries=3, delay=2)
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """ページを取得してBeautifulSoupオブジェクトを返す"""
        try:
            self.logger.debug(f"ページを取得中: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # レート制限
            time.sleep(self.config.delay)
            
            # 文字エンコーディングを明示的に設定
            response.encoding = response.apparent_encoding or 'utf-8'
            
            return BeautifulSoup(response.text, 'html.parser')
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"ページ取得エラー {url}: {str(e)}")
            return None
    
    def discover_collections(self) -> List[str]:
        """サイトからコレクションを自動発見"""
        collections = set(self.known_collections)
        
        try:
            # メインページからコレクションリンクを発見
            soup = self._fetch_page(self.base_url)
            if soup:
                # コレクションリンクを検索
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/collections/' in href:
                        collection_name = href.split('/collections/')[-1].split('?')[0]
                        if collection_name and collection_name != '':
                            collections.add(collection_name)
            
            self.logger.info(f"発見されたコレクション数: {len(collections)}")
            return list(collections)
        
        except Exception as e:
            self.logger.warning(f"コレクション自動発見エラー: {str(e)}")
            return self.known_collections
    
    def get_collection_products(self, collection: str) -> List[Dict[str, Any]]:
        """指定されたコレクションの商品リストを取得"""
        products = []
        page = 1
        
        while True:
            if self.config.max_products and len(products) >= self.config.max_products:
                break
            
            url = f"{self.base_url}/collections/{collection}?page={page}"
            soup = self._fetch_page(url)
            
            if not soup:
                break
            
            # 商品グリッドを探す - card クラスを含む要素を優先的に探す
            product_items = soup.find_all(['div'], class_=re.compile(r'card'))
            
            if not product_items:
                # 商品リンクを直接探す
                product_items = soup.find_all('a', href=re.compile(rf'/collections/{collection}/products/'))
                
            if not product_items:
                # より一般的なパターンで商品リンクを探す
                product_items = soup.find_all('a', href=re.compile(r'/products/'))
            
            if not product_items:
                self.logger.debug(f"コレクション {collection} のページ {page} で商品が見つかりませんでした")
                # デバッグ用：ページの内容を少し確認
                if soup:
                    all_links = soup.find_all('a', href=True)
                    product_links = [link for link in all_links if '/products/' in link.get('href', '')]
                    self.logger.debug(f"ページ内の全リンク数: {len(all_links)}, 商品リンク数: {len(product_links)}")
                break
            
            page_products = 0
            for item in product_items:
                if self.config.max_products and len(products) >= self.config.max_products:
                    break
                
                product_data = self._extract_product_from_listing(item, collection)
                if product_data:
                    products.append(product_data)
                    page_products += 1
            
            if page_products == 0:
                break
            
            self.logger.debug(f"コレクション {collection} ページ {page}: {page_products} 商品")
            page += 1
            
            # 無限ループ防止
            if page > 50:
                break
        
        return products
    
    def _extract_product_from_listing(self, item: BeautifulSoup, collection: str) -> Optional[Dict[str, Any]]:
        """商品リスト項目から基本情報を抽出"""
        try:
            # 商品リンクを取得
            link_elem = item.find('a', href=re.compile(r'/products/'))
            if not link_elem:
                link_elem = item if item.name == 'a' and item.get('href') and '/products/' in str(item.get('href')) else None
            if not link_elem:
                # コレクション内の商品リンクパターンも試す
                link_elem = item.find('a', href=re.compile(r'/collections/.*/products/'))
                if not link_elem:
                    link_elem = item if item.name == 'a' and item.get('href') and '/collections/' in str(item.get('href')) and '/products/' in str(item.get('href')) else None
            
            if not link_elem:
                return None
            
            product_url = urljoin(self.base_url, str(link_elem.get('href', '')))
            
            # 商品名を取得 - card__heading などShopifyの一般的なクラスも確認
            title_elem = item.find(['h2', 'h3', 'h4', 'div'], class_=re.compile(r'title|name|product|heading'))
            if not title_elem:
                title_elem = link_elem
            
            title = clean_text(title_elem.get_text()) if title_elem else "タイトル不明"
            
            # 価格を取得
            price_elem = item.find(['span', 'div'], class_=re.compile(r'price|cost'))
            if not price_elem:
                price_elem = item.find(string=re.compile(r'¥|円'))
                if price_elem:
                    price_elem = price_elem.parent
            
            price = parse_price(price_elem.get_text()) if price_elem else None
            
            # 在庫状況を判定
            stock_status = self._determine_stock_status(item)
            
            # 商品IDを抽出
            product_id = self._extract_product_id(product_url)
            
            return {
                'id': product_id,
                'title': title,
                'url': product_url,
                'price': price,
                'collection': collection,
                'stock_status': stock_status,
                'extracted_at': datetime.now()
            }
        
        except Exception as e:
            self.logger.debug(f"商品抽出エラー: {str(e)}")
            return None
    
    def _determine_stock_status(self, item: BeautifulSoup) -> str:
        """商品の在庫状況を判定"""
        text_content = item.get_text().lower()
        
        # 売り切れパターン
        if any(pattern in text_content for pattern in ['売り切れ', 'sold out', '完売', '在庫なし']):
            return 'sold_out'
        
        # 新着商品パターン（NEWバッジなど）
        if any(pattern in text_content for pattern in ['new', '新着', '新商品']):
            return 'new_items'
        
        # 予約商品パターン
        if any(pattern in text_content for pattern in ['予約', 'pre-order', '予約受付']):
            return 'pre_order'
        
        # デフォルトは在庫あり
        return 'in_stock'
    
    def _extract_product_id(self, url: str) -> str:
        """商品URLから商品IDを抽出"""
        try:
            # URLの最後の部分を商品IDとして使用
            return url.split('/')[-1].split('?')[0]
        except:
            return url
    
    def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """商品の詳細情報を取得"""
        soup = self._fetch_page(product_url)
        if not soup:
            return {}
        
        details = {}
        
        try:
            # 商品名
            title_elem = soup.find(['h1', 'h2'], class_=re.compile(r'product.*title|title'))
            if title_elem:
                details['detailed_title'] = clean_text(title_elem.get_text())
            
            # 価格情報
            price_elem = soup.find(['span', 'div'], class_=re.compile(r'price'))
            if price_elem:
                details['detailed_price'] = parse_price(price_elem.get_text())
            
            # 商品説明
            desc_elem = soup.find(['div', 'section'], class_=re.compile(r'description|product.*desc'))
            if desc_elem:
                details['description'] = clean_text(desc_elem.get_text())[:500]  # 500文字まで
            
            # SKU/商品コード
            sku_elem = soup.find(text=re.compile(r'SKU|商品コード'))
            if sku_elem:
                details['sku'] = clean_text(sku_elem.parent.get_text())
            
            # JSON-LDから構造化データを抽出
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    import json
                    data = json.loads(json_ld.string)
                    if isinstance(data, dict):
                        if 'offers' in data:
                            offer = data['offers']
                            if isinstance(offer, list):
                                offer = offer[0]
                            details['availability'] = offer.get('availability', '')
                            details['price_currency'] = offer.get('priceCurrency', 'JPY')
                except:
                    pass
        
        except Exception as e:
            self.logger.debug(f"商品詳細取得エラー {product_url}: {str(e)}")
        
        return details
    
    def scrape_all_products(self) -> List[Dict[str, Any]]:
        """全商品データをスクレイピング"""
        all_products = []
        
        # 対象コレクションを決定
        if self.config.collections:
            collections = self.config.collections
        else:
            collections = self.discover_collections()
        
        self.logger.info(f"対象コレクション: {collections}")
        
        for collection in collections:
            self.logger.info(f"コレクション '{collection}' を処理中...")
            
            try:
                products = self.get_collection_products(collection)
                self.logger.info(f"コレクション '{collection}': {len(products)} 商品")
                
                # 詳細情報を取得（必要に応じて）
                for product in products:
                    if self.config.fetch_details:
                        details = self.get_product_details(product['url'])
                        product.update(details)
                
                all_products.extend(products)
                
            except Exception as e:
                self.logger.error(f"コレクション '{collection}' 処理エラー: {str(e)}")
                continue
        
        # ステータスフィルターを適用
        if self.config.status_filter:
            filtered_products = [
                p for p in all_products 
                if p.get('stock_status') in self.config.status_filter
            ]
            self.logger.info(f"ステータスフィルター適用: {len(filtered_products)}/{len(all_products)} 商品")
            all_products = filtered_products
        
        return all_products
