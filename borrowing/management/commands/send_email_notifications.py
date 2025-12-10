from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from borrowing.emails import send_new_book_recommendation_email, check_and_send_reminders
from books.models import Book
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '发送各类邮件通知：逾期提醒、新书推荐等'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['overdue', 'new_books', 'all'],
            default='all',
            help='选择要发送的邮件类型'
        )

        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='新书推荐的天数范围（默认30天内的图书）'
        )

    def handle(self, *args, **options):
        User = get_user_model()
        email_type = options['type']
        days = options['days']

        self.stdout.write(self.style.SUCCESS(f'开始发送邮件通知 - 类型: {email_type}'))

        total_emails = 0

        if email_type in ['overdue', 'all']:
            self.stdout.write('检查逾期和即将到期的图书...')
            try:
                check_and_send_reminders()
                total_emails += 1  # 无法直接统计，至少表示执行了
                self.stdout.write(self.style.SUCCESS('逾期提醒邮件检查完成'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'逾期提醒邮件发送失败: {e}'))

        if email_type in ['new_books', 'all']:
            self.stdout.write(f'发送新书推荐邮件（最近{days}天）...')
            try:
                # 获取最近添加的图书
                cutoff_date = timezone.now() - timedelta(days=days)
                new_books = Book.objects.filter(
                    created_at__gte=cutoff_date,
                    available_copies__gt=0
                ).select_related('category')[:5]  # 每次最多推荐5本

                if not new_books:
                    self.stdout.write(self.style.WARNING('没有新书可推荐'))
                else:
                    # 获取所有活跃用户（最近登录过）
                    active_cutoff = timezone.now() - timedelta(days=30)
                    active_users = User.objects.filter(
                        is_active=True,
                        email__isnull=False,
                        email__gt='',
                        last_login__gte=active_cutoff
                    )

                    for user in active_users:
                        try:
                            # 可以根据用户历史借阅记录个性化推荐
                            # 这里简单发送同样的新书列表
                            result = send_new_book_recommendation_email(user, new_books)
                            if result:
                                total_emails += 1
                        except Exception as e:
                            logger.error(f"发送新书推荐邮件失败 - 用户: {user.username}, 错误: {e}")

                    self.stdout.write(
                        self.style.SUCCESS(f'新书推荐邮件发送完成 - {len(active_users)}个用户, {len(new_books)}本新书')
                    )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'新书推荐邮件发送失败: {e}'))

        self.stdout.write(self.style.SUCCESS(f'邮件通知发送完成！'))

        # 输出统计信息
        self.stdout.write('\n邮件发送统计:')
        self.stdout.write(f'  - 处理的邮件类型: {email_type}')
        self.stdout.write(f'  - 新书时间范围: {days}天')
        self.stdout.write(f'  - 发送完成时间: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')

        self.stdout.write(self.style.SUCCESS('所有邮件通知任务完成！'))