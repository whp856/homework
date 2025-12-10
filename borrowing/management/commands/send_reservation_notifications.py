from django.core.management.base import BaseCommand
from django.utils import timezone
from borrowing.models import BookReservation
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '发送预约通知（可借阅提醒）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只显示将要发送通知的预约，不实际发送',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write('=== 模拟模式：显示将要发送通知的预约 ===')

        # 找到应该通知但还未通知的预约
        # 这里我们可以检查状态为 pending 且已经等待了一段时间的预约
        # 或者根据业务逻辑调整
        pending_reservations = BookReservation.objects.filter(
            status='pending'
        ).order_by('priority', 'reservation_date')

        count = 0
        for reservation in pending_reservations:
            # 检查是否有可用的副本
            if reservation.book.available_copies > 0:
                if not dry_run:
                    # 处理可用的预约
                    result = BookReservation.process_available_book(reservation.book)
                    if result:
                        count += 1
                        self.stdout.write(
                            f'✓ 已发送通知给 {reservation.user.username} '
                            f'预约图书: {reservation.book.title}'
                        )
                else:
                    count += 1
                    self.stdout.write(
                        f'将发送通知给 {reservation.user.username} '
                        f'预约图书: {reservation.book.title}'
                    )

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('没有需要发送通知的预约')
            )
            return

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'成功发送了 {count} 个预约通知')
            )
            logger.info(f'发送了 {count} 个预约通知')
        else:
            self.stdout.write(
                self.style.WARNING(f'模拟模式：发现了 {count} 个待发送通知的预约')
            )