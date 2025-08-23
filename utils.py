"""
ユーティリティ関数モジュール
Utility Functions Module
"""

import re
import time
import logging
from functools import wraps
from typing import Optional, Any, Callable


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """失敗時にリトライするデコレーター"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.getLogger(__name__).debug(
                            f"リトライ {attempt + 1}/{max_retries}: {func.__name__} - {str(e)}"
                        )
                        time.sleep(delay * (attempt + 1))  # 指数バックオフ
                    else:
                        logging.getLogger(__name__).error(
                            f"最大リトライ回数に達しました: {func.__name__} - {str(e)}"
                        )
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def clean_text(text: str) -> str:
    """テキストをクリーニング"""
    if not text:
        return ""
    
    # 改行・タブ・余分な空白を除去
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 特殊文字を正規化
    text = text.replace('\u3000', ' ')  # 全角スペース
    text = text.replace('\xa0', ' ')   # non-breaking space
    
    # HTMLエンティティを処理
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&yen;': '¥'
    }
    
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    
    return text.strip()


def parse_price(price_text: str) -> Optional[float]:
    """価格テキストから数値を抽出"""
    if not price_text:
        return None
    
    # 数字以外を除去して価格を抽出
    price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
    if price_match:
        try:
            return float(price_match.group().replace(',', ''))
        except ValueError:
            pass
    
    return None


def format_currency(amount: float, currency: str = 'JPY') -> str:
    """通貨形式でフォーマット"""
    if currency == 'JPY':
        return f"¥{amount:,.0f}"
    else:
        return f"{amount:,.2f} {currency}"


def sanitize_filename(filename: str) -> str:
    """ファイル名に使用できない文字を除去"""
    # 使用できない文字を除去
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)
    
    # 連続するアンダースコアを一つに
    filename = re.sub(r'_+', '_', filename)
    
    # 先頭・末尾のアンダースコアを除去
    filename = filename.strip('_')
    
    # 長すぎる場合は切り詰め
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:100-len(ext)-1] + ('.' + ext if ext else '')
    
    return filename


def get_domain_from_url(url: str) -> str:
    """URLからドメインを抽出"""
    from urllib.parse import urlparse
    try:
        return urlparse(url).netloc
    except:
        return ""


def is_valid_url(url: str) -> bool:
    """URLの妥当性をチェック"""
    from urllib.parse import urlparse
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def calculate_processing_time(start_time: float) -> str:
    """処理時間を人間が読みやすい形式で計算"""
    elapsed = time.time() - start_time
    
    if elapsed < 60:
        return f"{elapsed:.1f}秒"
    elif elapsed < 3600:
        minutes = elapsed // 60
        seconds = elapsed % 60
        return f"{minutes:.0f}分{seconds:.0f}秒"
    else:
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        return f"{hours:.0f}時間{minutes:.0f}分"


def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """プログレスバーを作成"""
    if total == 0:
        return ""
    
    progress = current / total
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    percentage = progress * 100
    
    return f"|{bar}| {current}/{total} ({percentage:.1f}%)"


def log_performance(func_name: str, duration: float, items_processed: int = 0):
    """パフォーマンス情報をログ出力"""
    logger = logging.getLogger(__name__)
    
    rate = items_processed / duration if duration > 0 and items_processed > 0 else 0
    
    if items_processed > 0:
        logger.info(
            f"🚀 {func_name} 完了: {calculate_processing_time(time.time() - duration)} "
            f"({items_processed} 件, {rate:.1f} 件/秒)"
        )
    else:
        logger.info(f"🚀 {func_name} 完了: {calculate_processing_time(time.time() - duration)}")


class RateLimiter:
    """レート制限クラス"""
    
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def wait_if_needed(self):
        """必要に応じて待機"""
        now = time.time()
        
        # 時間窓外のリクエストを除去
        self.requests = [req_time for req_time in self.requests if now - req_time <= self.time_window]
        
        # 制限に達している場合は待機
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # 現在のリクエストを記録
        self.requests.append(now)


def setup_user_agent_rotation():
    """ユーザーエージェントのローテーション用リストを作成"""
    return [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
