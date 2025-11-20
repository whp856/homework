# Django图书管理系统

这是一个完整的Django图书管理系统，包含用户注册登录、权限分离和多表CRUD操作功能。

## 功能特性

### 核心功能
- ✅ **用户注册和登录**：完整的用户认证系统
- ✅ **权限分离**：管理员和普通用户不同权限
- ✅ **5张数据库表**：用户、图书、分类、借阅记录、评论
- ✅ **完整CRUD操作**：所有表都支持增删改查

### 具体功能模块

#### 1. 用户管理 (accounts)
- 用户注册、登录、退出
- 个人资料管理
- 管理员用户管理功能

#### 2. 图书管理 (books)
- 图书列表、详情、搜索
- 管理员图书CRUD操作
- 图书封面图片支持

#### 3. 分类管理 (categories)
- 分类列表、详情
- 管理员分类CRUD操作

#### 4. 借阅管理 (borrowing)
- 图书借阅、归还
- 借阅记录管理
- 逾期检查

#### 5. 评论系统 (reviews)
- 图书评论和评分
- 评论管理
- 评论审核功能

## 数据库表结构

### 1. CustomUser (用户表)
- username, email, password
- role (admin/user)
- phone, address, birth_date

### 2. Book (图书表)
- title, author, isbn, publisher
- category (外键)
- total_copies, available_copies
- cover_image, status

### 3. Category (分类表)
- name, description
- 创建时间、更新时间

### 4. BorrowRecord (借阅记录表)
- user, book (外键)
- borrow_date, due_date, return_date
- status (borrowed/returned/overdue)

### 5. Review (评论表)
- user, book (外键)
- rating (1-5星)
- comment, is_approved

## 安装和部署

### 1. 环境要求
- Python 3.8+
- Django 4.0+
- SQLite3 (默认)

### 2. 安装步骤

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install django pillow

# 3. 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 4. 创建超级用户
python manage.py createsuperuser

# 5. 运行开发服务器
python manage.py runserver
```

### 3. 访问系统
- 前台首页：http://127.0.0.1:8000/
- 管理后台：http://127.0.0.1:8000/admin/

## 使用说明

### 普通用户功能
1. 注册新账户
2. 登录系统
3. 浏览图书列表
4. 搜索图书
5. 借阅图书
6. 归还图书
7. 发表评论
8. 管理个人资料

### 管理员功能
1. 用户管理（启用/禁用用户）
2. 图书管理（添加/编辑/删除图书）
3. 分类管理（添加/编辑/删除分类）
4. 借阅记录管理
5. 评论审核管理
6. 系统统计信息

## 页面路由

### 用户相关
- `/accounts/register/` - 用户注册
- `/accounts/login/` - 用户登录
- `/accounts/profile/` - 个人资料
- `/accounts/users/` - 用户列表（管理员）

### 图书相关
- `/` - 首页
- `/books/list/` - 图书列表
- `/books/<id>/` - 图书详情
- `/books/create/` - 添加图书（管理员）

### 分类相关
- `/categories/` - 分类列表
- `/categories/<id>/` - 分类详情
- `/categories/create/` - 创建分类（管理员）

### 借阅相关
- `/borrowing/my-records/` - 我的借阅
- `/borrowing/records/` - 借阅记录（管理员）

### 评论相关
- `/reviews/book/<id>/` - 图书评论
- `/reviews/my-reviews/` - 我的评论

## 技术栈
- **后端**：Django 4.0+
- **前端**：Bootstrap 5, HTML5, CSS3
- **数据库**：SQLite3（可扩展到PostgreSQL/MySQL）
- **图标**：Bootstrap Icons

## 开发特性
- 响应式设计，支持移动端
- 用户友好的界面
- 完整的错误处理
- 数据验证
- 安全的权限控制

## 扩展建议
1. 添加图书推荐系统
2. 集成支付系统
3. 添加邮件通知功能
4. 实现图书预约功能
5. 添加数据导出功能
6. 集成第三方登录

## 许可证
MIT License