from django.core.management.base import BaseCommand
from django.utils import timezone
from borrowing.models import BookReservation
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '处理过期的图书预约'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只显示将要过期的预约，不实际处理',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write('=== 模拟模式：显示将要过期的预约 ===')

        # 获取所有过期的预约
        expired_reservations = BookReservation.objects.filter(
            status='pending',
            expiry_date__lt=timezone.now()
        )

        count = expired_reservations.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('没有找到过期的预约')
            )
            return

        self.stdout.write(f'找到 {count} 个过期的预约:')

        for reservation in expired_reservations:
            self.stdout.write(
                f'- 用户: {reservation.user.username}, '
                f'图书: {reservation.book.title}, '
                f'预约时间: {reservation.reservation_date.strftime("%Y-%m-%d %H:%M")}, '
                f'过期时间: {reservation.expiry_date.strftime("%Y-%m-%d %H:%M")}'
            )

            if not dry_run:
                # 更新状态为过期
                reservation.status = 'expired'
                reservation.save()
                self.stdout.write(f'  ✓ 已标记为过期')

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'成功处理了 {count} 个过期预约')
            )
            logger.info(f'处理了 {count} 个过期预约')
        else:
            self.stdout.write(
                self.style.WARNING(f'模拟模式：发现了 {count} 个过期预约，使用 --dry-run 参数可实际处理')
            )