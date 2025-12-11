import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime
import io
from django.core.exceptions import ValidationError
from books.models import Book, Category
from accounts.models import CustomUser

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


class ExcelImporter:
    """Excel导入工具类"""

    @staticmethod
    def import_books_from_excel(excel_file):
        """
        从Excel文件导入图书数据
        返回格式: {'success': bool, 'message': str, 'imported_count': int, 'errors': list}
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_file, sheet_name=0)

            # 验证必需的列
            required_columns = ['书名', '作者', 'ISBN', '总册数']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                return {
                    'success': False,
                    'message': f'Excel文件缺少必需的列: {", ".join(missing_columns)}',
                    'imported_count': 0,
                    'errors': [f'缺少必需列: {col}' for col in missing_columns]
                }

            imported_count = 0
            errors = []
            skipped_count = 0

            # 逐行处理数据
            for index, row in df.iterrows():
                try:
                    # 获取基本信息
                    title = str(row['书名']).strip()
                    author = str(row['作者']).strip()
                    isbn = str(row['ISBN']).strip()

                    # 验证必填字段
                    if not title or title == 'nan':
                        errors.append(f'第{index+2}行: 书名不能为空')
                        continue

                    if not author or author == 'nan':
                        errors.append(f'第{index+2}行: 作者不能为空')
                        continue

                    if not isbn or isbn == 'nan':
                        errors.append(f'第{index+2}行: ISBN不能为空')
                        continue

                    # 检查ISBN是否已存在
                    if Book.objects.filter(isbn=isbn).exists():
                        skipped_count += 1
                        continue

                    # 获取可选字段
                    publisher = str(row.get('出版社', '')).strip() if pd.notna(row.get('出版社')) else ''
                    publication_date = None
                    if '出版日期' in row and pd.notna(row['出版日期']):
                        try:
                            publication_date = pd.to_datetime(row['出版日期']).date()
                        except:
                            pass

                    # 处理分类
                    category = None
                    if '分类' in row and pd.notna(row['分类']):
                        category_name = str(row['分类']).strip()
                        if category_name and category_name != 'nan':
                            category, created = Category.objects.get_or_create(
                                name=category_name,
                                defaults={'description': f'通过Excel导入创建的分类: {category_name}'}
                            )

                    # 获取数字字段
                    total_copies = int(row.get('总册数', 1)) if pd.notna(row.get('总册数')) else 1
                    available_copies = int(row.get('可借册数', total_copies)) if pd.notna(row.get('可借册数')) else total_copies

                    # 验证册数
                    if total_copies <= 0:
                        errors.append(f'第{index+2}行: 总册数必须大于0')
                        continue

                    if available_copies > total_copies:
                        available_copies = total_copies

                    # 获取其他字段
                    location = str(row.get('书架位置', '')).strip() if pd.notna(row.get('书架位置')) else ''
                    description = str(row.get('描述', '')).strip() if pd.notna(row.get('描述')) else ''

                    # 处理状态
                    status = 'available'
                    if '状态' in row and pd.notna(row['状态']):
                        status_map = {
                            '可借阅': 'available',
                            '已借出': 'borrowed',
                            '维护中': 'maintenance',
                            '丢失': 'lost'
                        }
                        status = status_map.get(str(row['状态']).strip(), 'available')

                    # 创建图书
                    book = Book.objects.create(
                        title=title,
                        author=author,
                        isbn=isbn,
                        publisher=publisher if publisher else None,
                        publication_date=publication_date,
                        category=category,
                        description=description if description else None,
                        total_copies=total_copies,
                        available_copies=available_copies,
                        location=location if location else None,
                        status=status
                    )

                    imported_count += 1

                except Exception as e:
                    errors.append(f'第{index+2}行: {str(e)}')
                    continue

            # 构建返回消息
            message = f'成功导入 {imported_count} 本图书'
            if skipped_count > 0:
                message += f'，跳过 {skipped_count} 本重复ISBN的图书'
            if errors:
                message += f'，{len(errors)} 个错误'

            return {
                'success': True,
                'message': message,
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'errors': errors
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'文件处理失败: {str(e)}',
                'imported_count': 0,
                'errors': [f'文件处理失败: {str(e)}']
            }

    @staticmethod
    def get_import_template():
        """
        生成图书导入模板
        """
        # 创建模板数据
        template_data = [
            {
                '书名': '示例图书1',
                '作者': '作者姓名',
                'ISBN': '9787000000001',
                '出版社': '出版社名称',
                '出版日期': '2023-01-01',
                '分类': '文学',
                '总册数': 5,
                '可借册数': 5,
                '书架位置': 'A1-001',
                '状态': '可借阅',
                '描述': '图书描述信息'
            },
            {
                '书名': '示例图书2',
                '作者': '作者姓名',
                'ISBN': '9787000000002',
                '出版社': '出版社名称',
                '出版日期': '2023-01-01',
                '分类': '科技',
                '总册数': 3,
                '可借册数': 3,
                '书架位置': 'B2-005',
                '状态': '可借阅',
                '描述': '图书描述信息'
            }
        ]

        # 创建DataFrame
        df = pd.DataFrame(template_data)

        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='图书导入模板', index=False)

            # 设置列宽
            worksheet = writer.sheets['图书导入模板']
            column_widths = {
                'A': 20,  # 书名
                'B': 15,  # 作者
                'C': 20,  # ISBN
                'D': 20,  # 出版社
                'E': 15,  # 出版日期
                'F': 15,  # 分类
                'G': 10,  # 总册数
                'H': 10,  # 可借册数
                'I': 15,  # 书架位置
                'J': 10,  # 状态
                'K': 30,  # 描述
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

        # 创建HTTP响应
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=图书导入模板.xlsx'

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


class ExcelImporter:
    """Excel导入工具类"""

    @staticmethod
    def import_books_from_excel(excel_file):
        """
        从Excel文件导入图书数据
        返回格式: {'success': bool, 'message': str, 'imported_count': int, 'errors': list}
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_file, sheet_name=0)

            # 验证必需的列
            required_columns = ['书名', '作者', 'ISBN', '总册数']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                return {
                    'success': False,
                    'message': f'Excel文件缺少必需的列: {", ".join(missing_columns)}',
                    'imported_count': 0,
                    'errors': [f'缺少必需列: {col}' for col in missing_columns]
                }

            imported_count = 0
            errors = []
            skipped_count = 0

            # 逐行处理数据
            for index, row in df.iterrows():
                try:
                    # 获取基本信息
                    title = str(row['书名']).strip()
                    author = str(row['作者']).strip()
                    isbn = str(row['ISBN']).strip()

                    # 验证必填字段
                    if not title or title == 'nan':
                        errors.append(f'第{index+2}行: 书名不能为空')
                        continue

                    if not author or author == 'nan':
                        errors.append(f'第{index+2}行: 作者不能为空')
                        continue

                    if not isbn or isbn == 'nan':
                        errors.append(f'第{index+2}行: ISBN不能为空')
                        continue

                    # 检查ISBN是否已存在
                    if Book.objects.filter(isbn=isbn).exists():
                        skipped_count += 1
                        continue

                    # 获取可选字段
                    publisher = str(row.get('出版社', '')).strip() if pd.notna(row.get('出版社')) else ''
                    publication_date = None
                    if '出版日期' in row and pd.notna(row['出版日期']):
                        try:
                            publication_date = pd.to_datetime(row['出版日期']).date()
                        except:
                            pass

                    # 处理分类
                    category = None
                    if '分类' in row and pd.notna(row['分类']):
                        category_name = str(row['分类']).strip()
                        if category_name and category_name != 'nan':
                            category, created = Category.objects.get_or_create(
                                name=category_name,
                                defaults={'description': f'通过Excel导入创建的分类: {category_name}'}
                            )

                    # 获取数字字段
                    total_copies = int(row.get('总册数', 1)) if pd.notna(row.get('总册数')) else 1
                    available_copies = int(row.get('可借册数', total_copies)) if pd.notna(row.get('可借册数')) else total_copies

                    # 验证册数
                    if total_copies <= 0:
                        errors.append(f'第{index+2}行: 总册数必须大于0')
                        continue

                    if available_copies > total_copies:
                        available_copies = total_copies

                    # 获取其他字段
                    location = str(row.get('书架位置', '')).strip() if pd.notna(row.get('书架位置')) else ''
                    description = str(row.get('描述', '')).strip() if pd.notna(row.get('描述')) else ''

                    # 处理状态
                    status = 'available'
                    if '状态' in row and pd.notna(row['状态']):
                        status_map = {
                            '可借阅': 'available',
                            '已借出': 'borrowed',
                            '维护中': 'maintenance',
                            '丢失': 'lost'
                        }
                        status = status_map.get(str(row['状态']).strip(), 'available')

                    # 创建图书
                    book = Book.objects.create(
                        title=title,
                        author=author,
                        isbn=isbn,
                        publisher=publisher if publisher else None,
                        publication_date=publication_date,
                        category=category,
                        description=description if description else None,
                        total_copies=total_copies,
                        available_copies=available_copies,
                        location=location if location else None,
                        status=status
                    )

                    imported_count += 1

                except Exception as e:
                    errors.append(f'第{index+2}行: {str(e)}')
                    continue

            # 构建返回消息
            message = f'成功导入 {imported_count} 本图书'
            if skipped_count > 0:
                message += f'，跳过 {skipped_count} 本重复ISBN的图书'
            if errors:
                message += f'，{len(errors)} 个错误'

            return {
                'success': True,
                'message': message,
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'errors': errors
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'文件处理失败: {str(e)}',
                'imported_count': 0,
                'errors': [f'文件处理失败: {str(e)}']
            }

    @staticmethod
    def get_import_template():
        """
        生成图书导入模板
        """
        # 创建模板数据
        template_data = [
            {
                '书名': '示例图书1',
                '作者': '作者姓名',
                'ISBN': '9787000000001',
                '出版社': '出版社名称',
                '出版日期': '2023-01-01',
                '分类': '文学',
                '总册数': 5,
                '可借册数': 5,
                '书架位置': 'A1-001',
                '状态': '可借阅',
                '描述': '图书描述信息'
            },
            {
                '书名': '示例图书2',
                '作者': '作者姓名',
                'ISBN': '9787000000002',
                '出版社': '出版社名称',
                '出版日期': '2023-01-01',
                '分类': '科技',
                '总册数': 3,
                '可借册数': 3,
                '书架位置': 'B2-005',
                '状态': '可借阅',
                '描述': '图书描述信息'
            }
        ]

        # 创建DataFrame
        df = pd.DataFrame(template_data)

        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='图书导入模板', index=False)

            # 设置列宽
            worksheet = writer.sheets['图书导入模板']
            column_widths = {
                'A': 20,  # 书名
                'B': 15,  # 作者
                'C': 20,  # ISBN
                'D': 20,  # 出版社
                'E': 15,  # 出版日期
                'F': 15,  # 分类
                'G': 10,  # 总册数
                'H': 10,  # 可借册数
                'I': 15,  # 书架位置
                'J': 10,  # 状态
                'K': 30,  # 描述
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

        # 创建HTTP响应
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=图书导入模板.xlsx'

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


class ExcelImporter:
    """Excel导入工具类"""

    @staticmethod
    def import_books_from_excel(excel_file):
        """
        从Excel文件导入图书数据
        返回格式: {'success': bool, 'message': str, 'imported_count': int, 'errors': list}
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_file, sheet_name=0)

            # 验证必需的列
            required_columns = ['书名', '作者', 'ISBN', '总册数']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                return {
                    'success': False,
                    'message': f'Excel文件缺少必需的列: {", ".join(missing_columns)}',
                    'imported_count': 0,
                    'errors': [f'缺少必需列: {col}' for col in missing_columns]
                }

            imported_count = 0
            errors = []
            skipped_count = 0

            # 逐行处理数据
            for index, row in df.iterrows():
                try:
                    # 获取基本信息
                    title = str(row['书名']).strip()
                    author = str(row['作者']).strip()
                    isbn = str(row['ISBN']).strip()

                    # 验证必填字段
                    if not title or title == 'nan':
                        errors.append(f'第{index+2}行: 书名不能为空')
                        continue

                    if not author or author == 'nan':
                        errors.append(f'第{index+2}行: 作者不能为空')
                        continue

                    if not isbn or isbn == 'nan':
                        errors.append(f'第{index+2}行: ISBN不能为空')
                        continue

                    # 检查ISBN是否已存在
                    if Book.objects.filter(isbn=isbn).exists():
                        skipped_count += 1
                        continue

                    # 获取可选字段
                    publisher = str(row.get('出版社', '')).strip() if pd.notna(row.get('出版社')) else ''
                    publication_date = None
                    if '出版日期' in row and pd.notna(row['出版日期']):
                        try:
                            publication_date = pd.to_datetime(row['出版日期']).date()
                        except:
                            pass

                    # 处理分类
                    category = None
                    if '分类' in row and pd.notna(row['分类']):
                        category_name = str(row['分类']).strip()
                        if category_name and category_name != 'nan':
                            category, created = Category.objects.get_or_create(
                                name=category_name,
                                defaults={'description': f'通过Excel导入创建的分类: {category_name}'}
                            )

                    # 获取数字字段
                    total_copies = int(row.get('总册数', 1)) if pd.notna(row.get('总册数')) else 1
                    available_copies = int(row.get('可借册数', total_copies)) if pd.notna(row.get('可借册数')) else total_copies

                    # 验证册数
                    if total_copies <= 0:
                        errors.append(f'第{index+2}行: 总册数必须大于0')
                        continue

                    if available_copies > total_copies:
                        available_copies = total_copies

                    # 获取其他字段
                    location = str(row.get('书架位置', '')).strip() if pd.notna(row.get('书架位置')) else ''
                    description = str(row.get('描述', '')).strip() if pd.notna(row.get('描述')) else ''

                    # 处理状态
                    status = 'available'
                    if '状态' in row and pd.notna(row['状态']):
                        status_map = {
                            '可借阅': 'available',
                            '已借出': 'borrowed',
                            '维护中': 'maintenance',
                            '丢失': 'lost'
                        }
                        status = status_map.get(str(row['状态']).strip(), 'available')

                    # 创建图书
                    book = Book.objects.create(
                        title=title,
                        author=author,
                        isbn=isbn,
                        publisher=publisher if publisher else None,
                        publication_date=publication_date,
                        category=category,
                        description=description if description else None,
                        total_copies=total_copies,
                        available_copies=available_copies,
                        location=location if location else None,
                        status=status
                    )

                    imported_count += 1

                except Exception as e:
                    errors.append(f'第{index+2}行: {str(e)}')
                    continue

            # 构建返回消息
            message = f'成功导入 {imported_count} 本图书'
            if skipped_count > 0:
                message += f'，跳过 {skipped_count} 本重复ISBN的图书'
            if errors:
                message += f'，{len(errors)} 个错误'

            return {
                'success': True,
                'message': message,
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'errors': errors
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'文件处理失败: {str(e)}',
                'imported_count': 0,
                'errors': [f'文件处理失败: {str(e)}']
            }

    @staticmethod
    def get_import_template():
        """
        生成图书导入模板
        """
        # 创建模板数据
        template_data = [
            {
                '书名': '示例图书1',
                '作者': '作者姓名',
                'ISBN': '9787000000001',
                '出版社': '出版社名称',
                '出版日期': '2023-01-01',
                '分类': '文学',
                '总册数': 5,
                '可借册数': 5,
                '书架位置': 'A1-001',
                '状态': '可借阅',
                '描述': '图书描述信息'
            },
            {
                '书名': '示例图书2',
                '作者': '作者姓名',
                'ISBN': '9787000000002',
                '出版社': '出版社名称',
                '出版日期': '2023-01-01',
                '分类': '科技',
                '总册数': 3,
                '可借册数': 3,
                '书架位置': 'B2-005',
                '状态': '可借阅',
                '描述': '图书描述信息'
            }
        ]

        # 创建DataFrame
        df = pd.DataFrame(template_data)

        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='图书导入模板', index=False)

            # 设置列宽
            worksheet = writer.sheets['图书导入模板']
            column_widths = {
                'A': 20,  # 书名
                'B': 15,  # 作者
                'C': 20,  # ISBN
                'D': 20,  # 出版社
                'E': 15,  # 出版日期
                'F': 15,  # 分类
                'G': 10,  # 总册数
                'H': 10,  # 可借册数
                'I': 15,  # 书架位置
                'J': 10,  # 状态
                'K': 30,  # 描述
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

        # 创建HTTP响应
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=图书导入模板.xlsx'

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


class ExcelImporter:
    """Excel导入工具类"""

    @staticmethod
    def import_books_from_excel(excel_file):
        """
        从Excel文件导入图书数据
        返回格式: {'success': bool, 'message': str, 'imported_count': int, 'errors': list}
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_file, sheet_name=0)

            # 验证必需的列
            required_columns = ['书名', '作者', 'ISBN', '总册数']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                return {
                    'success': False,
                    'message': f'Excel文件缺少必需的列: {", ".join(missing_columns)}',
                    'imported_count': 0,
                    'errors': [f'缺少必需列: {col}' for col in missing_columns]
                }

            imported_count = 0
            errors = []
            skipped_count = 0

            # 逐行处理数据
            for index, row in df.iterrows():
                try:
                    # 获取基本信息
                    title = str(row['书名']).strip()
                    author = str(row['作者']).strip()
                    isbn = str(row['ISBN']).strip()

                    # 验证必填字段
                    if not title or title == 'nan':
                        errors.append(f'第{index+2}行: 书名不能为空')
                        continue

                    if not author or author == 'nan':
                        errors.append(f'第{index+2}行: 作者不能为空')
                        continue

                    if not isbn or isbn == 'nan':
                        errors.append(f'第{index+2}行: ISBN不能为空')
                        continue

                    # 检查ISBN是否已存在
                    if Book.objects.filter(isbn=isbn).exists():
                        skipped_count += 1
                        continue

                    # 获取可选字段
                    publisher = str(row.get('出版社', '')).strip() if pd.notna(row.get('出版社')) else ''
                    publication_date = None
                    if '出版日期' in row and pd.notna(row['出版日期']):
                        try:
                            publication_date = pd.to_datetime(row['出版日期']).date()
                        except:
                            pass

                    # 处理分类
                    category = None
                    if '分类' in row and pd.notna(row['分类']):
                        category_name = str(row['分类']).strip()
                        if category_name and category_name != 'nan':
                            category, created = Category.objects.get_or_create(
                                name=category_name,
                                defaults={'description': f'通过Excel导入创建的分类: {category_name}'}
                            )

                    # 获取数字字段
                    total_copies = int(row.get('总册数', 1)) if pd.notna(row.get('总册数')) else 1
                    available_copies = int(row.get('可借册数', total_copies)) if pd.notna(row.get('可借册数')) else total_copies

                    # 验证册数
                    if total_copies <= 0:
                        errors.append(f'第{index+2}行: 总册数必须大于0')
                        continue

                    if available_copies > total_copies:
                        available_copies = total_copies

                    # 获取其他字段
                    location = str(row.get('书架位置', '')).strip() if pd.notna(row.get('书架位置')) else ''
                    description = str(row.get('描述', '')).strip() if pd.notna(row.get('描述')) else ''

                    # 处理状态
                    status = 'available'
                    if '状态' in row and pd.notna(row['状态']):
                        status_map = {
                            '可借阅': 'available',
                            '已借出': 'borrowed',
                            '维护中': 'maintenance',
                            '丢失': 'lost'
                        }
                        status = status_map.get(str(row['状态']).strip(), 'available')

                    # 创建图书
                    book = Book.objects.create(
                        title=title,
                        author=author,
                        isbn=isbn,
                        publisher=publisher if publisher else None,
                        publication_date=publication_date,
                        category=category,
                        description=description if description else None,
                        total_copies=total_copies,
                        available_copies=available_copies,
                        location=location if location else None,
                        status=status
                    )

                    imported_count += 1

                except Exception as e:
                    errors.append(f'第{index+2}行: {str(e)}')
                    continue

            # 构建返回消息
            message = f'成功导入 {imported_count} 本图书'
            if skipped_count > 0:
                message += f'，跳过 {skipped_count} 本重复ISBN的图书'
            if errors:
                message += f'，{len(errors)} 个错误'

            return {
                'success': True,
                'message': message,
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'errors': errors
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'文件处理失败: {str(e)}',
                'imported_count': 0,
                'errors': [f'文件处理失败: {str(e)}']
            }

    @staticmethod
    def get_import_template():
        """
        生成图书导入模板
        """
        # 创建模板数据
        template_data = [
            {
                '书名': '示例图书1',
                '作者': '作者姓名',
                'ISBN': '9787000000001',
                '出版社': '出版社名称',
                '出版日期': '2023-01-01',
                '分类': '文学',
                '总册数': 5,
                '可借册数': 5,
                '书架位置': 'A1-001',
                '状态': '可借阅',
                '描述': '图书描述信息'
            },
            {
                '书名': '示例图书2',
                '作者': '作者姓名',
                'ISBN': '9787000000002',
                '出版社': '出版社名称',
                '出版日期': '2023-01-01',
                '分类': '科技',
                '总册数': 3,
                '可借册数': 3,
                '书架位置': 'B2-005',
                '状态': '可借阅',
                '描述': '图书描述信息'
            }
        ]

        # 创建DataFrame
        df = pd.DataFrame(template_data)

        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='图书导入模板', index=False)

            # 设置列宽
            worksheet = writer.sheets['图书导入模板']
            column_widths = {
                'A': 20,  # 书名
                'B': 15,  # 作者
                'C': 20,  # ISBN
                'D': 20,  # 出版社
                'E': 15,  # 出版日期
                'F': 15,  # 分类
                'G': 10,  # 总册数
                'H': 10,  # 可借册数
                'I': 15,  # 书架位置
                'J': 10,  # 状态
                'K': 30,  # 描述
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

        # 创建HTTP响应
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=图书导入模板.xlsx'

        return response