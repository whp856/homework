"""
缓存管理视图
"""
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .cache import cache, CACHE_KEY_HOME_STATS, CACHE_KEY_POPULAR_BOOKS


def is_admin(user):
    return user.is_authenticated and user.is_admin


@login_required
@user_passes_test(is_admin)
def cache_stats(request):
    """缓存统计页面"""
    # 获取缓存统计信息
    stats = cache.get_stats()

    # 获取缓存大小信息
    try:
        cache_size = len(cache._cache)
    except:
        cache_size = 0

    # 测试缓存操作
    test_key = 'cache_test_key'
    test_value = {'test': 'data', 'timestamp': '2024-01-01'}

    # 设置测试缓存
    cache.set(test_key, test_value, timeout=60)

    # 获取测试缓存
    retrieved_value = cache.get(test_key)

    # 删除测试缓存
    cache.delete(test_key)

    context = {
        'stats': stats,
        'cache_size': cache_size,
        'test_result': {
            'set_success': cache.get(test_key) is not None,
            'get_success': retrieved_value == test_value,
            'delete_success': cache.get(test_key) is None
        }
    }

    return render(request, 'cache/stats.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def clear_cache(request):
    """清除缓存"""
    cache_type = request.POST.get('cache_type', 'all')

    if cache_type == 'all':
        # 清除所有缓存
        cache.clear()
        messages.success(request, '已清除所有缓存')
    elif cache_type == 'home':
        # 清除首页相关缓存
        cache.delete(CACHE_KEY_HOME_STATS, namespace='books')
        cache.delete('popular_books', namespace='books')
        cache.delete('recent_books', namespace='books')
        messages.success(request, '已清除首页缓存')
    elif cache_type == 'books':
        # 清除图书相关缓存
        cache.clear(namespace='books')
        messages.success(request, '已清除图书相关缓存')
    elif cache_type == 'users':
        # 清除用户相关缓存
        cache.clear(namespace='users')
        messages.success(request, '已清除用户相关缓存')
    elif cache_type == 'expired':
        # 只清除过期缓存
        expired_count = cache.clear_expired()
        messages.success(request, f'已清除 {expired_count} 个过期缓存项')

    return redirect('cache_stats')


@login_required
@user_passes_test(is_admin)
def cache_health_check(request):
    """缓存健康检查（AJAX接口）"""
    health_data = {
        'status': 'healthy',
        'stats': cache.get_stats(),
        'timestamp': str(cache._lru.get('last_access', 0)) if hasattr(cache, '_lru') else 'N/A'
    }

    # 执行基本的缓存操作测试
    try:
        test_key = f"health_check_{hash(str(request))}"
        test_value = {"test": True}

        # 测试设置
        cache.set(test_key, test_value, timeout=10)

        # 测试获取
        retrieved = cache.get(test_key)

        # 测试删除
        cache.delete(test_key)

        if retrieved == test_value:
            health_data['operations'] = 'passed'
        else:
            health_data['operations'] = 'failed'
            health_data['status'] = 'degraded'

    except Exception as e:
        health_data['operations'] = 'error'
        health_data['status'] = 'unhealthy'
        health_data['error'] = str(e)

    return JsonResponse(health_data)


@login_required
@user_passes_test(is_admin)
def cache_inspector(request):
    """缓存检查器 - 显示详细缓存内容"""
    # 获取所有缓存键（仅显示，不修改）
    cache_keys = []

    try:
        if hasattr(cache, '_cache'):
            cache_keys = list(cache._cache.keys())
    except:
        pass

    # 按命名空间分组
    namespaced_keys = {}
    for key in cache_keys:
        if ':' in key:
            namespace = key.split(':', 1)[0]
            if namespace not in namespaced_keys:
                namespaced_keys[namespace] = []
            namespaced_keys[namespace].append(key)
        else:
            if 'global' not in namespaced_keys:
                namespaced_keys['global'] = []
            namespaced_keys['global'].append(key)

    context = {
        'namespaced_keys': namespaced_keys,
        'total_keys': len(cache_keys),
        'stats': cache.get_stats()
    }

    return render(request, 'cache/inspector.html', context)