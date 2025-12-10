"""
缓存中间件，用于页面级缓存
"""
import hashlib
from django.utils.cache import patch_vary_headers
from django.core.cache import cache
from django.http import HttpResponse
from library_management.cache import get_cache_key_with_params


class PageCacheMiddleware:
    """
    页面缓存中间件
    为静态内容和查询结果较慢的页面提供缓存
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # 定义需要缓存的页面及其配置
        self.cache_config = {
            # 页面路径: (缓存时间秒, 是否缓存GET参数)
            '/': (300, False),  # 首页，5分钟
            '/books/list/': (180, True),  # 图书列表，3分钟，缓存GET参数
            '/books/': (300, False),  # 图书首页，5分钟
        }

    def __call__(self, request):
        # 只缓存GET请求
        if request.method != 'GET':
            return self.get_response(request)

        # 检查是否需要缓存该页面
        path = request.path
        if path not in self.cache_config:
            return self.get_response(request)

        cache_timeout, cache_params = self.cache_config[path]

        # 生成缓存键
        if cache_params:
            # 包含GET参数
            cache_key = self._generate_cache_key(request, include_params=True)
        else:
            # 不包含GET参数
            cache_key = self._generate_cache_key(request, include_params=False)

        # 尝试从缓存获取响应
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return cached_response

        # 生成响应并缓存
        response = self.get_response(request)

        # 只缓存成功的响应
        if response.status_code == 200:
            # 为响应添加Vary头，确保不同用户看到正确的内容
            patch_vary_headers(response, ['Cookie', 'User-Agent'])

            # 缓存响应
            cache.set(cache_key, response, cache_timeout)

        return response

    def _generate_cache_key(self, request, include_params=False):
        """生成页面缓存键"""
        # 基础键包含路径和方法
        key_parts = [
            'page_cache',
            request.path,
            request.method,
        ]

        # 如果需要包含GET参数
        if include_params:
            # 对参数进行排序以确保一致性
            sorted_params = sorted(request.GET.items())
            params_str = '&'.join(f"{k}={v}" for k, v in sorted_params)
            key_parts.append(params_str)

        # 如果用户已登录，包含用户ID（但这样会导致每个用户都有单独的缓存）
        # 可以根据需要调整
        if request.user.is_authenticated:
            key_parts.append(f"user_{request.user.id}")

        # 生成MD5哈希作为最终的键
        key_string = ':'.join(str(part) for part in key_parts)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()


class CacheStatsMiddleware:
    """
    缓存统计中间件
    用于监控和收集缓存性能数据
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 在请求开始前记录时间
        from library_management.cache import cache
        stats_before = cache.get_stats()

        response = self.get_response(request)

        # 在请求结束后记录时间
        stats_after = cache.get_stats()

        # 将统计信息添加到响应头（仅在DEBUG模式下）
        if hasattr(response, 'items') and hasattr(response, '__setitem__'):
            response['X-Cache-Hits-Before'] = stats_before.get('hits', 0)
            response['X-Cache-Hits-After'] = stats_after.get('hits', 0)
            response['X-Cache-Hit-Rate'] = f"{stats_after.get('hit_rate', 0)}%"

        return response


class CacheInvalidationMiddleware:
    """
    缓存失效中间件
    当数据变更时自动清除相关缓存
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # 检查是否是数据修改请求
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            # 根据请求路径自动清除相关缓存
            self._auto_invalidate_cache(request.path, request.user)

        return response

    def _auto_invalidate_cache(self, path, user):
        """根据路径自动失效缓存"""
        from library_management.cache import cache, invalidate_user_cache

        # 如果是图书相关的修改，清除图书缓存
        if '/books/' in path:
            cache.clear(namespace='books')

        # 如果是用户相关的修改，清除用户缓存
        if '/accounts/' in path and user.is_authenticated:
            invalidate_user_cache(user.id)

        # 如果是借阅记录相关的修改，清除借阅缓存
        if '/borrowing/' in path:
            cache.clear(namespace='borrowing')

        # 清除首页缓存（通常包含各种统计信息）
        cache.delete('home_stats', namespace='books')