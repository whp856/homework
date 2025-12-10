import pandas as pd
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime
import io

class ExcelExporter:
    """Excel导出工具类"""

    @staticmethod
    def export_books(books, filename=None):
        """导出图书数据到Excel"""
        if filename is None:
            filename = f"图书数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # 准备数据
        data = []
        for book in books:
            data.append({
                '书名': book.title,
                '作者': book.author,
                'ISBN': book.isbn,
                '出版社': book.publisher or '',
                '出版日期': book.publication_date.strftime('%Y-%m-%d') if book.publication_date else '',
                '分类': book.category.name if book.category else '',
                '总册数': book.total_copies,
                '可借册数': book.available_copies,
                '已借册数': book.borrowed_copies,
                '书架位置': book.location or '',
                '状态': book.get_status_display(),
                '描述': book.description or '',
                '创建时间': book.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                '更新时间': book.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        # 创建DataFrame
        df = pd.DataFrame(data)

        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='图书数据', index=False)

            # 获取工作表并设置列宽
            worksheet = writer.sheets['图书数据']
            column_widths = {
                'A': 20,  # 书名
                'B': 15,  # 作者
                'C': 20,  # ISBN
                'D': 20,  # 出版社
                'E': 15,  # 出版日期
                'F': 15,  # 分类
                'G': 10,  # 总册数
                'H': 10,  # 可借册数
                'I': 10,  # 已借册数
                'J': 15,  # 书架位置
                'K': 10,  # 状态
                'L': 30,  # 描述
                'M': 20,  # 创建时间
                'N': 20   # 更新时间
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

        # 创建HTTP响应
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    @staticmethod
    def export_users(users, filename=None):
        """导出用户数据到Excel"""
        if filename is None:
            filename = f"用户数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # 准备数据
        data = []
        for user in users:
            data.append({
                '用户名': user.username,
                '姓名': user.get_full_name() or user.username,
                '邮箱': user.email,
                '角色': user.get_role_display(),
                '电话': user.phone or '',
                '地址': user.address or '',
                '出生日期': user.birth_date.strftime('%Y-%m-%d') if user.birth_date else '',
                '是否活跃': '是' if user.is_active else '否',
                '创建时间': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                '最后登录': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else ''
            })

        # 创建DataFrame
        df = pd.DataFrame(data)

        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='用户数据', index=False)

            # 设置列宽
            worksheet = writer.sheets['用户数据']
            column_widths = {
                'A': 15,  # 用户名
                'B': 15,  # 姓名
                'C': 25,  # 邮箱
                'D': 10,  # 角色
                'E': 20,  # 电话
                'F': 30,  # 地址
                'G': 15,  # 出生日期
                'H': 10,  # 是否活跃
                'I': 20,  # 创建时间
                'J': 20   # 最后登录
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

        # 创建HTTP响应
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    @staticmethod
    def export_borrow_records(records, filename=None):
        """导出借阅记录到Excel"""
        if filename is None:
            filename = f"借阅记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # 准备数据
        data = []
        for record in records:
            data.append({
                '用户名': record.user.username,
                '用户姓名': record.user.get_full_name() or record.user.username,
                '书名': record.book.title,
                '作者': record.book.author,
                'ISBN': record.book.isbn,
                '借阅时间': record.borrow_date.strftime('%Y-%m-%d %H:%M:%S'),
                '应还时间': record.due_date.strftime('%Y-%m-%d %H:%M:%S'),
                '归还时间': record.return_date.strftime('%Y-%m-%d %H:%M:%S') if record.return_date else '',
                '状态': record.get_status_display(),
                '逾期天数': record.days_overdue if record.is_overdue else 0,
                '备注': record.notes or '',
                '创建时间': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                '更新时间': record.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        # 创建DataFrame
        df = pd.DataFrame(data)

        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='借阅记录', index=False)

            # 设置列宽
            worksheet = writer.sheets['借阅记录']
            column_widths = {
                'A': 15,  # 用户名
                'B': 15,  # 用户姓名
                'C': 25,  # 书名
                'D': 15,  # 作者
                'E': 20,  # ISBN
                'F': 20,  # 借阅时间
                'G': 20,  # 应还时间
                'H': 20,  # 归还时间
                'I': 10,  # 状态
                'J': 10,  # 逾期天数
                'K': 30,  # 备注
                'L': 20,  # 创建时间
                'M': 20   # 更新时间
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

        # 创建HTTP响应
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    @staticmethod
    def export_statistics(stats_data, filename=None):
        """导出统计数据到Excel"""
        if filename is None:
            filename = f"图书馆统计_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 总体统计
            overall_df = pd.DataFrame([{
                '统计项': '总图书数量',
                '数值': stats_data.get('total_books', 0),
                '说明': '图书馆所有图书的总数量'
            }, {
                '统计项': '可借阅图书',
                '数值': stats_data.get('available_books', 0),
                '说明': '当前可以借阅的图书数量'
            }, {
                '统计项': '已借出图书',
                '数值': stats_data.get('borrowed_books', 0),
                '说明': '当前已经被借出的图书数量'
            }, {
                '统计项': '总用户数',
                '数值': stats_data.get('total_users', 0),
                '说明': '注册用户总数量'
            }, {
                '统计项': '活跃用户数',
                '数值': stats_data.get('active_users', 0),
                '说明': '当前活跃的用户数量'
            }])

            overall_df.to_excel(writer, sheet_name='总体统计', index=False)

            # 分类统计
            if 'category_stats' in stats_data:
                category_data = []
                for cat_name, cat_stats in stats_data['category_stats'].items():
                    category_data.append({
                        '分类名称': cat_name,
                        '图书数量': cat_stats.get('book_count', 0),
                        '可借阅数量': cat_stats.get('available_count', 0),
                        '借出数量': cat_stats.get('borrowed_count', 0)
                    })

                category_df = pd.DataFrame(category_data)
                category_df.to_excel(writer, sheet_name='分类统计', index=False)

            # 设置列宽
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for col in ['A', 'B', 'C', 'D']:
                    worksheet.column_dimensions[col].width = 20

        # 创建HTTP响应
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response