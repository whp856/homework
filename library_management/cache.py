import time
from threading import RLock
from typing import Dict, Any, Optional, Callable, Tuple, List
from collections import OrderedDict


class EnhancedCache:
    """增强版内存缓存实现，支持过期时间、线程安全、命名空间、LRU策略和统计"""
    
    def __init__(self, default_timeout: int = 300, max_size: int = 1000):
        """
        初始化缓存
        
        Args:
            default_timeout: 默认缓存过期时间（秒），默认为5分钟
            max_size: 缓存最大项数，超过将使用LRU策略移除
        """
        self._cache: Dict[str, Tuple[Any, float, float]] = {}  # (value, expiry, last_accessed)
        self._lock = RLock()  # 使用可重入锁保证线程安全
        self.default_timeout = default_timeout
        self.max_size = max_size
        # 用于LRU策略的有序字典
        self._lru = OrderedDict()
        # 统计信息
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'expired': 0
        }
    
    def _make_key(self, key: Any, namespace: Optional[str] = None) -> str:
        """将任意类型的键转换为字符串，支持命名空间"""
        if namespace:
            return f"{namespace}:{str(key)}"
        return str(key)
    
    def _enforce_lru(self) -> None:
        """实施LRU策略，当缓存超过最大大小时删除最久未使用的项"""
        while len(self._cache) >= self.max_size:
            # 移除最久未使用的项
            oldest_key, _ = self._lru.popitem(last=False)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
    
    def get(self, key: Any, default: Any = None, namespace: Optional[str] = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 缓存不存在或已过期时返回的默认值
            namespace: 命名空间，用于隔离缓存
            
        Returns:
            缓存的值或默认值
        """
        key_str = self._make_key(key, namespace)
        current_time = time.time()
        
        with self._lock:
            # 检查键是否存在
            if key_str not in self._cache:
                self._stats['misses'] += 1
                return default
            
            # 获取缓存值和过期时间
            value, expiry, _ = self._cache[key_str]
            
            # 检查是否已过期
            if expiry < current_time:
                # 删除过期缓存
                del self._cache[key_str]
                if key_str in self._lru:
                    del self._lru[key_str]
                self._stats['misses'] += 1
                self._stats['expired'] += 1
                return default
            
            # 更新访问时间和LRU顺序
            self._cache[key_str] = (value, expiry, current_time)
            if key_str in self._lru:
                self._lru.move_to_end(key_str)
            else:
                self._lru[key_str] = current_time
            
            self._stats['hits'] += 1
            return value
    
    def set(self, key: Any, value: Any, timeout: Optional[int] = None, namespace: Optional[str] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 过期时间（秒），None表示使用默认值
            namespace: 命名空间，用于隔离缓存
        """
        key_str = self._make_key(key, namespace)
        timeout = self.default_timeout if timeout is None else timeout
        expiry = time.time() + timeout
        current_time = time.time()
        
        with self._lock:
            # 实施LRU策略
            if key_str not in self._cache and len(self._cache) >= self.max_size:
                self._enforce_lru()
            
            # 存储缓存值
            self._cache[key_str] = (value, expiry, current_time)
            # 更新LRU顺序
            if key_str in self._lru:
                self._lru.move_to_end(key_str)
            else:
                self._lru[key_str] = current_time
            
            self._stats['sets'] += 1
    
    def delete(self, key: Any, namespace: Optional[str] = None) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            namespace: 命名空间，用于隔离缓存
            
        Returns:
            是否成功删除
        """
        key_str = self._make_key(key, namespace)
        
        with self._lock:
            if key_str in self._cache:
                del self._cache[key_str]
                if key_str in self._lru:
                    del self._lru[key_str]
                self._stats['deletes'] += 1
                return True
            return False
    
    def clear(self, namespace: Optional[str] = None) -> None:
        """
        清空所有缓存或指定命名空间的缓存
        
        Args:
            namespace: 命名空间，如果指定则只清空该命名空间的缓存
        """
        with self._lock:
            if namespace:
                # 清空指定命名空间的缓存
                namespace_prefix = f"{namespace}:"
                keys_to_delete = [k for k in self._cache.keys() if k.startswith(namespace_prefix)]
                for key in keys_to_delete:
                    del self._cache[key]
                    if key in self._lru:
                        del self._lru[key]
                    self._stats['deletes'] += 1
            else:
                # 清空所有缓存
                self._cache.clear()
                self._lru.clear()
                self._stats['deletes'] += len(self._cache)
    
    def get_or_set(self, key: Any, func: Callable[[], Any], timeout: Optional[int] = None, namespace: Optional[str] = None) -> Any:
        """
        获取缓存，如果不存在则执行函数并缓存结果
        
        Args:
            key: 缓存键
            func: 生成缓存值的函数
            timeout: 过期时间
            namespace: 命名空间
            
        Returns:
            缓存的值或函数的执行结果
        """
        # 尝试获取缓存
        value = self.get(key, namespace=namespace)
        
        # 如果缓存不存在，执行函数并缓存结果
        if value is None:
            value = func()
            self.set(key, value, timeout, namespace)
        
        return value
    
    def clear_expired(self) -> int:
        """
        清理过期缓存
        
        Returns:
            清理的过期项数量
        """
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            # 找出所有过期的键
            for key, (_, expiry, _) in self._cache.items():
                if expiry < current_time:
                    expired_keys.append(key)
            
            # 删除过期的缓存项
            for key in expired_keys:
                del self._cache[key]
                if key in self._lru:
                    del self._lru[key]
                self._stats['deletes'] += 1
                self._stats['expired'] += 1
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存统计信息的字典
        """
        with self._lock:
            # 计算命中率
            total = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
            
            return {
                **self._stats,
                'total': total,
                'hit_rate': round(hit_rate, 2),
                'current_size': len(self._cache)
            }
    
    def get_many(self, keys: List[Any], namespace: Optional[str] = None) -> Dict[Any, Any]:
        """
        批量获取缓存
        
        Args:
            keys: 键列表
            namespace: 命名空间
            
        Returns:
            键值对字典
        """
        result = {}
        for key in keys:
            value = self.get(key, namespace=namespace)
            if value is not None:
                result[key] = value
        return result
    
    def set_many(self, data: Dict[Any, Any], timeout: Optional[int] = None, namespace: Optional[str] = None) -> None:
        """
        批量设置缓存

        Args:
            data: 键值对字典
            timeout: 过期时间
            namespace: 命名空间
        """
        for key, value in data.items():
            self.set(key, value, timeout, namespace)

# 缓存装饰器和辅助函数
def cache_result(key_func=None, timeout=None, namespace=None):
    """
    缓存函数结果的装饰器

    Args:
        key_func: 生成缓存键的函数，接收函数的参数
        timeout: 过期时间
        namespace: 命名空间
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"

            # 尝试从缓存获取
            cached_result = cache.get(cache_key, namespace=namespace)
            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout, namespace)
            return result

        return wrapper
    return decorator

def cache_query(timeout=None, namespace='query'):
    """
    缓存数据库查询结果的装饰器

    Args:
        timeout: 过期时间，默认15分钟
        namespace: 命名空间
    """
    return cache_result(timeout=timeout or 900, namespace=namespace)

def invalidate_user_cache(user_id):
    """
    清除与特定用户相关的所有缓存

    Args:
        user_id: 用户ID
    """
    patterns = [
        f"user_stats:{user_id}",
        f"user_borrow_records:{user_id}",
        f"user_recommendations:{user_id}",
    ]

    for pattern in patterns:
        cache.delete(pattern, namespace='user')

def invalidate_book_cache(book_id):
    """
    清除与特定图书相关的所有缓存

    Args:
        book_id: 图书ID
    """
    patterns = [
        f"book_detail:{book_id}",
        f"popular_books",
        f"recent_books",
        f"home_stats",
        f"book_list",
        f"category_stats",
    ]

    for pattern in patterns:
        cache.delete(pattern, namespace='books')

def invalidate_category_cache(category_id):
    """
    清除与特定分类相关的所有缓存

    Args:
        category_id: 分类ID
    """
    patterns = [
        f"category_stats:{category_id}",
        f"categories",
        f"home_stats",
        f"book_list",
    ]

    for pattern in patterns:
        cache.delete(pattern, namespace='categories')

def get_cache_key_with_params(base_key, **params):
    """
    生成带参数的缓存键

    Args:
        base_key: 基础键名
        **params: 参数

    Returns:
        缓存键
    """
    if not params:
        return base_key

    # 对参数进行排序以确保一致性
    sorted_params = sorted(params.items())
    param_str = "_".join(f"{k}_{v}" for k, v in sorted_params)
    return f"{base_key}_{param_str}"


# 在文件开头添加
from django.conf import settings

# 然后在创建缓存实例时使用配置
cache = EnhancedCache(
    default_timeout=getattr(settings, 'CACHE_DEFAULT_TIMEOUT', 300),
    max_size=getattr(settings, 'CACHE_MAX_SIZE', 1000)
)

# 缓存键常量，用于保持一致性
CACHE_KEY_HOME_STATS = 'home_stats'
CACHE_KEY_CATEGORIES = 'categories'
CACHE_KEY_BOOK_COUNT = 'book_count'
CACHE_KEY_AVAILABLE_COUNT = 'available_count'
CACHE_KEY_PAGINATED_BOOKS = 'paginated_books'
CACHE_KEY_BOOK_LIST = 'cached_book_list'
CACHE_KEY_CATEGORY_LIST = 'cached_category_list'

# 新增缓存键
CACHE_KEY_POPULAR_BOOKS = 'popular_books'
CACHE_KEY_RECENT_BOOKS = 'recent_books'
CACHE_KEY_USER_STATS = 'user_stats'
CACHE_KEY_BORROW_STATS = 'borrow_stats'
CACHE_KEY_USER_BORROW_RECORDS = 'user_borrow_records'
CACHE_KEY_USER_RECOMMENDATIONS = 'user_recommendations'
CACHE_KEY_BOOK_DETAIL = 'book_detail'
CACHE_KEY_CATEGORY_STATS = 'category_stats'
CACHE_KEY_SEARCH_RESULTS = 'search_results'
CACHE_KEY_ADMIN_DASHBOARD = 'admin_dashboard'
CACHE_KEY_REVIEWS_STATS = 'reviews_stats'