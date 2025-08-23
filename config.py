"""
設定管理モジュール
Configuration Management Module
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ScrapingConfig:
    """スクレイピング設定クラス"""
    
    # 基本設定
    delay: float = 1.0  # リクエスト間隔（秒）
    max_products: Optional[int] = None  # 最大取得商品数
    timeout: int = 30  # リクエストタイムアウト（秒）
    
    # フィルタリング設定
    collections: Optional[List[str]] = None  # 対象コレクション
    status_filter: Optional[List[str]] = None  # 在庫状況フィルター
    
    # 詳細取得設定
    fetch_details: bool = False  # 商品詳細ページを取得するか
    
    # エラーハンドリング設定
    max_retries: int = 3  # 最大リトライ回数
    retry_delay: float = 2.0  # リトライ間隔（秒）
    
    # 出力設定
    include_images: bool = False  # 画像URL情報を含めるか
    include_descriptions: bool = True  # 商品説明を含めるか
    
    def __post_init__(self):
        """設定の妥当性をチェック"""
        if self.delay < 0.1:
            self.delay = 0.1
        
        if self.max_products is not None and self.max_products < 1:
            self.max_products = None
        
        if self.timeout < 5:
            self.timeout = 5
        
        if self.max_retries < 0:
            self.max_retries = 0
    
    @classmethod
    def create_fast_config(cls) -> 'ScrapingConfig':
        """高速取得用設定を作成"""
        return cls(
            delay=0.5,
            max_products=100,
            fetch_details=False,
            max_retries=1
        )
    
    @classmethod
    def create_detailed_config(cls) -> 'ScrapingConfig':
        """詳細取得用設定を作成"""
        return cls(
            delay=2.0,
            fetch_details=True,
            include_descriptions=True,
            max_retries=3
        )
    
    @classmethod
    def create_safe_config(cls) -> 'ScrapingConfig':
        """安全な取得用設定を作成"""
        return cls(
            delay=3.0,
            max_products=50,
            fetch_details=False,
            max_retries=5,
            retry_delay=5.0
        )


# デフォルト設定
DEFAULT_CONFIG = ScrapingConfig()

# よく使われる在庫状況フィルター
STOCK_STATUS_FILTERS = {
    'in_stock': ['in_stock'],
    'sold_out': ['sold_out'],
    'new_items': ['new_items'],
    'available': ['in_stock', 'new_items'],
    'all': ['in_stock', 'sold_out', 'new_items', 'pre_order']
}

# よく使われるコレクション
POPULAR_COLLECTIONS = [
    'newitems',
    'chiikawarestaurant',
    'tokyomiyage',
    'magicalchiikawa',
    'parallelworld'
]
