"""
优化的分页工具类
提供高效的数据库分页查询和缓存机制
"""
from math import ceil
from django.core.paginator import Paginator
from django.db import models
from django.core.cache import cache
from .cache import get_cache_key_with_params, cache_query


class OptimizedPaginator:
    """
    优化的分页器，支持缓存和高效查询
    """

    def __init__(self, queryset, per_page=12, cache_timeout=300, cache_namespace='pagination'):
        """
        初始化优化分页器

        Args:
            queryset: 查询集
            per_page: 每页显示数量
            cache_timeout: 缓存超时时间（秒）
            cache_namespace: 缓存命名空间
        """
        self.queryset = queryset
        self.per_page = per_page
        self.cache_timeout = cache_timeout
        self.cache_namespace = cache_namespace
        self.paginator = None

    def get_page_data(self, page_number, **filters):
        """
        获取分页数据，支持缓存

        Args:
            page_number: 页码
            **filters: 过滤条件

        Returns:
            包含分页数据的字典
        """
        # 生成缓存键
        cache_key = get_cache_key_with_params(
            'page_data',
            page=page_number,
            per_page=self.per_page,
            total=self.queryset.count(),
            **filters
        )

        # 尝试从缓存获取
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        # 从数据库获取数据
        self.paginator = Paginator(self.queryset, self.per_page)

        try:
            page_obj = self.paginator.page(page_number)
        except:
            page_obj = self.paginator.page(1)

        # 计算分页信息
        total_pages = self.paginator.num_pages
        current_page = page_obj.number
        has_next = page_obj.has_next()
        has_previous = page_obj.has_previous()
        next_page_number = current_page + 1 if has_next else None
        prev_page_number = current_page - 1 if has_previous else None

        # 生成页码范围
        page_range = self._get_page_range(current_page, total_pages)

        # 组织数据
        data = {
            'object_list': page_obj.object_list,
            'page_obj': page_obj,
            'current_page': current_page,
            'total_pages': total_pages,
            'total_items': self.paginator.count,
            'per_page': self.per_page,
            'has_next': has_next,
            'has_previous': has_previous,
            'next_page_number': next_page_number,
            'prev_page_number': prev_page_number,
            'page_range': page_range,
            'start_index': page_obj.start_index(),
            'end_index': page_obj.end_index()
        }

        # 缓存数据
        cache.set(cache_key, data, self.cache_timeout)

        return data

    def _get_page_range(self, current_page, total_pages, window_size=5):
        """
        生成页码范围

        Args:
            current_page: 当前页
            total_pages: 总页数
            window_size: 显示的页码窗口大小

        Returns:
            页码范围列表
        """
        if total_pages <= window_size:
            return range(1, total_pages + 1)

        half_window = window_size // 2
        start_page = max(1, current_page - half_window)
        end_page = min(total_pages, current_page + half_window)

        # 调整范围，确保窗口大小
        if end_page - start_page < window_size:
            if start_page == 1:
                end_page = min(total_pages, start_page + window_size - 1)
            else:
                start_page = max(1, end_page - window_size + 1)

        return range(start_page, end_page + 1)


class CursorPagination:
    """
    基于游标的分页器，适用于大数据集
    """

    def __init__(self, queryset, per_page=12, ordering='-id'):
        """
        初始化游标分页器

        Args:
            queryset: 查询集
            per_page: 每页显示数量
            ordering: 排序字段
        """
        self.queryset = queryset
        self.per_page = per_page
        self.ordering = ordering

    def get_page_data(self, cursor=None):
        """
        获取基于游标的分页数据

        Args:
            cursor: 游标值

        Returns:
            包含分页数据的字典
        """
        queryset = self.queryset.order_by(self.ordering)

        if cursor:
            if self.ordering.startswith('-'):
                field_name = self.ordering[1:]
                queryset = queryset.filter(**{f'{field_name}__lt': cursor})
            else:
                field_name = self.ordering
                queryset = queryset.filter(**{f'{field_name}__gt': cursor})

        items = list(queryset[:self.per_page + 1])
        has_next = len(items) > self.per_page
        if has_next:
            items = items[:-1]

        # 计算下一页游标
        next_cursor = None
        if has_next and items:
            last_item = items[-1]
            if self.ordering.startswith('-'):
                field_name = self.ordering[1:]
                next_cursor = getattr(last_item, field_name)
            else:
                field_name = self.ordering
                next_cursor = getattr(last_item, field_name)

        return {
            'object_list': items,
            'has_next': has_next,
            'next_cursor': str(next_cursor) if next_cursor else None,
            'per_page': self.per_page
        }


class SmartPagination:
    """
    智能分页器，根据数据量自动选择最适合的分页策略
    """

    def __init__(self, queryset, per_page=12, strategy='auto'):
        """
        初始化智能分页器

        Args:
            queryset: 查询集
            per_page: 每页显示数量
            strategy: 分页策略 ('auto', 'offset', 'cursor')
        """
        self.queryset = queryset
        self.per_page = per_page
        self.strategy = strategy

    def get_page_data(self, page_number=None, cursor=None, **filters):
        """
        智能获取分页数据

        Args:
            page_number: 传统分页页码
            cursor: 游标分页游标
            **filters: 过滤条件

        Returns:
            包含分页数据的字典
        """
        # 自动选择策略
        if self.strategy == 'auto':
            total_count = self.queryset.count()
            if total_count > 10000:
                # 大数据集使用游标分页
                self.strategy = 'cursor'
            else:
                # 小数据集使用传统分页
                self.strategy = 'offset'

        if self.strategy == 'cursor':
            paginator = CursorPagination(self.queryset, self.per_page)
            return paginator.get_page_data(cursor)
        else:
            paginator = OptimizedPaginator(self.queryset, self.per_page)
            return paginator.get_page_data(page_number or 1, **filters)


@cache_query(timeout=600, namespace='books')
def get_paginated_books(query='', category_id='', page=1, per_page=12):
    """
    获取分页图书数据（带缓存）

    Args:
        query: 搜索查询
        category_id: 分类ID
        page: 页码
        per_page: 每页数量

    Returns:
        分页数据
    """
    from books.models import Book, Category
    from django.db.models import Q

    # 构建查询
    queryset = Book.objects.select_related('category').all().order_by('title')

    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )

    if category_id:
        queryset = queryset.filter(category_id=category_id)

    # 使用优化分页器
    paginator = SmartPagination(queryset, per_page=per_page)
    return paginator.get_page_data(page_number=page, query=query, category=category_id)


class PaginationCacheManager:
    """
    分页缓存管理器
    """

    @staticmethod
    def invalidate_pagination_cache(queryset_key, **filters):
        """
        失效特定条件的分页缓存

        Args:
            queryset_key: 查询集标识
            **filters: 过滤条件
        """
        # 生成缓存键模式
        pattern_parts = [f"page_data_*_{queryset_key}"]

        for key, value in filters.items():
            if value:
                pattern_parts.append(f"{key}_{value}")

        # 清理相关缓存
        from .cache import cache
        cache.clear()


def get_pagination_context(paginator_data, request_path=''):
    """
    生成分页上下文数据，用于模板渲染

    Args:
        paginator_data: 分页数据
        request_path: 请求路径

    Returns:
        分页上下文字典
    """
    context = {
        'page_obj': type('PageObj', (), {
            'number': paginator_data.get('current_page', 1),
            'has_previous': paginator_data.get('has_previous', False),
            'has_next': paginator_data.get('has_next', False),
            'previous_page_number': paginator_data.get('prev_page_number'),
            'next_page_number': paginator_data.get('next_page_number'),
            'start_index': paginator_data.get('start_index', 0),
            'end_index': paginator_data.get('end_index', 0),
        })(),
        'object_list': paginator_data.get('object_list', []),
        'is_paginated': paginator_data.get('total_pages', 1) > 1,
        'page_range': paginator_data.get('page_range', []),
    }

    # 添加额外的分页信息
    context.update({
        'total_pages': paginator_data.get('total_pages', 1),
        'total_items': paginator_data.get('total_items', 0),
        'per_page': paginator_data.get('per_page', 12),
        'current_page': paginator_data.get('current_page', 1),
        'show_first_page': context['current_page'] > 3,
        'show_last_page': context['current_page'] < paginator_data.get('total_pages', 1) - 2,
        'page_url_base': request_path,
    })

    return context