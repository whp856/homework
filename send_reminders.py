#!/usr/bin/env python
"""
定期发送借阅到期提醒邮件的脚本
可以通过crontab或Windows任务计划程序定期执行
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from borrowing.emails import check_and_send_reminders

if __name__ == "__main__":
    print("开始检查并发送到期提醒邮件...")
    check_and_send_reminders()
    print("到期提醒邮件检查完成。")