#!/usr/bin/env python
import os
import sys
import django
import requests
from django.conf import settings

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.urls import reverse

def test_http_responses():
    """测试HTTP响应状态"""
    print("=== 测试HTTP响应状态 ===\n")

    base_url = "http://127.0.0.1:8000"

    # 测试URL列表
    test_urls = [
        ('welcome', '欢迎页面'),
        ('home', '系统首页'),
        ('accounts:login', '登录页面'),
        ('books:book_list', '图书列表'),
        ('categories:category_list', '分类管理'),
        ('reviews:my_reviews', '我的评论'),
        ('borrowing:my_records', '我的借阅'),
    ]

    for url_name, description in test_urls:
        try:
            url = reverse(url_name)
            full_url = base_url + url

            try:
                response = requests.get(full_url, timeout=5)
                status_code = response.status_code

                if status_code == 200:
                    status = "[成功]"
                elif status_code == 302:
                    status = "[重定向]"
                elif status_code == 404:
                    status = "[不存在]"
                else:
                    status = f"[{status_code}]"

            except requests.exceptions.Timeout:
                status = "[超时]"
            except requests.exceptions.ConnectionError:
                status = "[连接失败]"
            except Exception as e:
                status = f"[错误: {e}]"

            print(f"{description:<20} {url:<30} {status}")

        except Exception as e:
            print(f"{description:<20} 无法解析URL: {e}")

if __name__ == '__main__':
    test_http_responses()