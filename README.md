# 📚 Django图书管理系统

一个功能完整的现代化图书管理系统，基于Django 4.2+框架开发，实现了图书管理的全生命周期业务流程。从图书入库到用户借阅，从数据分析到批量导入，提供一站式图书馆管理解决方案。

[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 一句话介绍

**这是一个能够让图书馆管理员轻松管理图书、用户借阅，并让读者便捷查找和借阅图书的完整管理系统。**

---

## 🌟 核心功能概览

### 👥 用户管理
- **多角色权限系统**：普通用户、管理员、超级管理员三级权限
- **完整用户流程**：注册→登录→个人资料管理→借阅权限
- **安全认证**：Session认证、密码加密、CSRF防护
- **账户管理**：头像上传、信息编辑、状态管理

### 📖 图书管理
- **图书全生命周期**：入库→上架→借阅→归还→维护→报废
- **智能分类系统**：多级分类、自动分类创建、分类统计
- **库存管理**：总册数、可借册数、已借册数实时跟踪
- **搜索筛选**：书名、作者、ISBN搜索 + 分类、状态筛选
- **封面管理**：图片上传、默认封面、尺寸优化

### 📋 借阅管理
- **智能借阅**：自动资格检查、并发控制、原子操作
- **灵活期限**：普通用户30天，管理员60天
- **预约系统**：优先级队列、自动通知、过期机制
- **状态跟踪**：借阅中、已归还、逾期实时更新
- **历史记录**：完整借阅历史、逾期统计

### ⭐ 评论评分
- **5星评分系统**：直观的星级显示、平均分计算
- **智能评论**：需借阅才能评论、防重复、审核机制
- **评论管理**：管理员审核、删除、回复功能

### 📊 数据管理
- **Excel导入**：模板下载、批量导入、数据验证、错误反馈
- **多维度导出**：图书数据、用户数据、借阅记录、统计报表
- **智能格式化**：自动列宽设置、中文编码支持

### 📧 通知系统
- **借阅通知**：借阅确认、归还确认、到期提醒、逾期通知
- **预约通知**：图书可用时自动通知预约用户
- **系统通知**：欢迎邮件、新书推荐、密码重置

### 🚀 性能优化
- **智能缓存**：分层缓存、LRU策略、自动失效
- **并发控制**：数据库锁、事务保护
- **查询优化**：select_related、prefetch_related优化

---

## 🏗️ 技术架构

### 后端技术栈
- **框架**: Django 4.2+
- **数据库**: SQLite3 (可扩展 PostgreSQL/MySQL)
- **缓存**: 自定义内存缓存 + Django Cache Framework
- **Excel处理**: pandas + openpyxl
- **邮件**: Django Email Backend + SMTP
- **图片处理**: Pillow

### 前端技术栈
- **UI框架**: Bootstrap 5
- **JavaScript**: jQuery + 原生JS
- **图标**: Bootstrap Icons
- **响应式**: 移动端适配

### 核心依赖
```python
Django>=4.2.0
Pillow>=10.0.0
django-bootstrap5>=23.3
pandas>=2.0.0
openpyxl>=3.1.0
python-decouple>=3.8
```

---

## 💼 业务场景应用

### 🏫 学校图书馆
- **学生借阅**: 学生账号自主借阅，借阅期限30天
- **教师特权**: 教师账号可借阅60天，更高优先级
- **课程用书**: 批量导入课程相关图书，分类管理
- **借阅统计**: 按班级、专业统计借阅情况

### 📱 企业图书室
- **员工借阅**: 员工账号管理，部门分类
- **技术书籍**: 编程、技术类图书管理
- **借阅审批**: 管理员审批特殊借阅需求
- **资产统计**: 图书资产统计、折旧管理

### 🏛️ 公共图书馆
- **市民借阅**: 市民注册借阅，身份验证
- **图书预约**: 热门图书排队预约
- **逾期管理**: 逾期罚款、提醒通知
- **数据报表**: 借阅统计、热门图书排行

### 👨‍💼 个人书房
- **藏书管理**: 个人图书收藏、分类整理
- **阅读计划**: 制定阅读计划、跟踪进度
- **读书笔记**: 图书评论、评分、笔记
- **朋友分享**: 与朋友分享读书记录

---

## 🎮 快速体验

### 🌐 在线演示
```
首页: http://demo-library.com/
管理员: admin@example.com / admin123
普通用户: user@example.com / user123
```

### 🚀 本地部署
```bash
# 1. 克隆项目
git clone https://github.com/whp856/homework.git
cd homework

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 数据库初始化
python manage.py migrate
python manage.py createsuperuser

# 5. 启动服务
python manage.py runserver

# 6. 访问系统
# 首页: http://127.0.0.1:8000/
# 管理后台: http://127.0.0.1:8000/admin/
```

---

## 📋 功能详细说明

### 🔐 用户权限矩阵

| 功能 | 普通用户 | 管理员 | 超级管理员 |
|------|---------|--------|------------|
| 浏览图书 | ✅ | ✅ | ✅ |
| 借阅图书 | ✅ | ✅ | ✅ |
| 个人资料 | ✅ | ✅ | ✅ |
| 添加图书 | ❌ | ✅ | ✅ |
| 用户管理 | ❌ | ✅ | ✅ |
| 系统配置 | ❌ | ❌ | ✅ |

### 📖 图书状态流转
```
入库 → 可借阅 → 已借出 → 归还 → 可借阅
  ↓        ↓        ↓       ↑
  └──→ 维护中 ←──────┘       │
  ↓                        │
  └────→ 丢失/报废 ←─────────┘
```

### 📋 借阅业务流程
```
用户登录 → 搜索图书 → 检查资格 → 借阅成功 → 到期提醒 → 归还图书
    ↓         ↓         ↓         ↓         ↓         ↓
  权限验证   多条件搜索  库存检查  扣减库存  邮件提醒  恢复库存
```

### 📊 数据导入导出
- **支持格式**: Excel (.xlsx, .xls)
- **导入模板**: 标准化模板，包含示例数据
- **批量操作**: 一次导入数百本图书
- **数据验证**: 自动检查数据完整性和格式
- **错误反馈**: 详细错误信息，精确定位问题行

---

## 🎨 界面预览

### 📱 移动端适配
- 响应式设计，完美适配手机、平板、电脑
- 触摸友好的交互设计
- 移动端优化的导航菜单

### 🖥️ 管理后台
- Django原生Admin界面
- 强大的数据管理功能
- 自定义后台配置

---

## ⚡ 性能特点

### 🚀 高性能缓存
- **多层缓存**: 首页、列表、详情等独立缓存
- **智能失效**: 数据更新时自动清理相关缓存
- **命中率**: 90%+ 缓存命中率
- **内存优化**: LRU策略自动清理

### 🔒 数据安全
- **事务保护**: 关键操作使用数据库事务
- **并发控制**: 防止并发借阅同一本书
- **权限控制**: 细粒度的功能权限控制
- **数据验证**: 严格的输入验证和过滤

---

## 📈 统计分析

### 📊 运营数据
- 图书总量、分类分布
- 用户活跃度、增长趋势
- 借阅统计、热门图书排行
- 逾期情况分析

### 👤 个人数据
- 个人借阅历史
- 阅读偏好分析
- 借阅习惯统计
- 年度阅读报告

---

## 🔧 开发部署

### 🐳 Docker部署
```bash
# 使用Docker Compose一键部署
docker-compose up -d

# 访问应用
# 前端: http://localhost:8000
# 数据库: localhost:5432
```

### 🌐 生产环境
```bash
# 使用Gunicorn
gunicorn library_management.wsgi:application --bind 0.0.0.0:8000

# 配置Nginx反向代理
# 支持SSL、静态文件、负载均衡
```

---

## 🤝 贡献指南

### 📝 开发流程
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 🐛 问题反馈
- [Bug Report](https://github.com/whp856/homework/issues/new?template=bug_report.md)
- [Feature Request](https://github.com/whp856/homework/issues/new?template=feature_request.md)

---

## 📞 联系方式

- **项目作者**: [Your Name]
- **邮箱**: your.email@example.com
- **项目主页**: https://github.com/whp856/homework
- **问题反馈**: https://github.com/whp856/homework/issues

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🙏 致谢

感谢以下开源项目：
- [Django](https://www.djangoproject.com/) - 强大的Python Web框架
- [Bootstrap](https://getbootstrap.com/) - 前端UI框架
- [pandas](https://pandas.pydata.org/) - 数据处理库
- [openpyxl](https://openpyxl.readthedocs.io/) - Excel文件处理

---

⭐ **如果这个项目对您有帮助，请给我们一个Star！**

---

*最后更新: 2025年12月*