import time
from threading import RLock
from typing import Dict, Any, Optional, Callable, Tuple


class SimpleCache:
    """简易内存缓存实现，支持过期时间和线程安全"""
    
    def __init__(self, default_timeout: int = 300):
        """
        初始化缓存
        
        Args:
            default_timeout: 默认缓存过期时间（秒），默认为5分钟
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = RLock()  # 使用可重入锁保证线程安全
        self.default_timeout = default_timeout
    
    def _make_key(self, key: Any) -> str:
        """将任意类型的键转换为字符串"""
        return str(key)
    
    def get(self, key: Any, default: Any = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 缓存不存在或已过期时返回的默认值
            
        Returns:
            缓存的值或默认值
        """
        key_str = self._make_key(key)
        
        with self._lock:
            # 检查键是否存在
            if key_str not in self._cache:
                return default
            
            # 获取缓存值和过期时间
            value, expiry = self._cache[key_str]
            
            # 检查是否已过期
            if expiry < time.time():
                # 删除过期缓存
                del self._cache[key_str]
                return default
            
            return value
    
    def set(self, key: Any, value: Any, timeout: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 过期时间（秒），None表示使用默认值
        """
        key_str = self._make_key(key)
        timeout = self.default_timeout if timeout is None else timeout
        expiry = time.time() + timeout
        
        with self._lock:
            self._cache[key_str] = (value, expiry)
    
    def delete(self, key: Any) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        key_str = self._make_key(key)
        
        with self._lock:
            if key_str in self._cache:
                del self._cache[key_str]
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    def get_or_set(self, key: Any, func: Callable[[], Any], timeout: Optional[int] = None) -> Any:
        """
        获取缓存，如果不存在则执行函数并缓存结果
        
        Args:
            key: 缓存键
            func: 生成缓存值的函数
            timeout: 过期时间
            
        Returns:
            缓存的值或函数的执行结果
        """
        # 尝试获取缓存
        value = self.get(key)
        
        # 如果缓存不存在，执行函数并缓存结果
        if value is None:
            value = func()
            self.set(key, value, timeout)
        
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
            for key, (_, expiry) in self._cache.items():
                if expiry < current_time:
                    expired_keys.append(key)
            
            # 删除过期的缓存项
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)


# 在文件开头添加
from django.conf import settings

# 然后在创建缓存实例时使用配置
cache = SimpleCache(default_timeout=getattr(settings, 'CACHE_DEFAULT_TIMEOUT', 300))

# 缓存键常量，用于保持一致性
CACHE_KEY_HOME_STATS = 'home_stats'
CACHE_KEY_CATEGORIES = 'categories'
CACHE_KEY_BOOK_COUNT = 'book_count'
CACHE_KEY_AVAILABLE_COUNT = 'available_count'