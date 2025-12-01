# 团队开发指南

## 🚀 快速开始

### 方式一：Docker 开发（推荐）
```bash
# 1. 克隆项目
git clone https://github.com/whp856/homework.git
cd homework

# 2. 启动开发环境
docker-compose up --build

# 3. 访问应用
# 前台: http://localhost:8000
# 后台: http://localhost:8000/admin/
```

### 方式二：本地开发
```bash
# 1. 克隆项目
git clone https://github.com/whp856/homework.git
cd homework

# 2. 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 5. 创建超级用户（可选）
python manage.py createsuperuser

# 6. 启动开发服务器
python manage.py runserver
```

## 📋 开发规范

### Git 工作流
1. **主分支**: `main` - 生产环境代码
2. **开发分支**: `develop` - 开发环境代码
3. **功能分支**: `feature/功能名称` - 新功能开发
4. **修复分支**: `bugfix/问题描述` - Bug修复

### 提交信息规范
```
类型(范围): 描述

feat: 新功能
fix: Bug修复
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建过程或辅助工具的变动
```

### 分支命名规范
- `feature/user-auth` - 用户认证功能
- `feature/book-search` - 图书搜索功能
- `bugfix/login-error` - 登录错误修复
- `hotfix/security-patch` - 安全补丁

## 🔧 开发环境配置

### 环境变量配置
1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 修改 `.env` 文件中的配置

### 数据库配置
- **开发环境**: 默认使用 SQLite
- **生产环境**: 推荐使用 PostgreSQL

## 🧪 测试
```bash
# 运行所有测试
python manage.py test

# 运行特定应用的测试
python manage.py test accounts
python manage.py test books
```

## 📚 代码审查流程

1. 创建 Pull Request
2. 至少需要一个团队成员审查
3. 通过所有自动化测试
4. 合并到目标分支

## 🚀 部署

### 开发环境部署
```bash
# 使用 Docker Compose
docker-compose -f docker-compose.dev.yml up
```

### 生产环境部署
详细部署说明请参考 `DEPLOY_PYTHONANYWHERE.md`

## 🤝 团队协作

### 角色分工
- **项目负责人**: 代码审查，发布管理
- **后端开发**: Django 应用开发
- **前端开发**: 模板和样式开发
- **测试工程师**: 测试用例编写

### 沟通工具
- **代码讨论**: GitHub Issues/Pull Requests
- **日常沟通**: 微信/钉钉群
- **文档协作**: GitHub Wiki

## 📝 开发注意事项

1. **代码质量**
   - 遵循 PEP 8 代码规范
   - 编写清晰的注释
   - 保持函数单一职责

2. **安全性**
   - 永远不要提交敏感信息
   - 使用 Django 的安全特性
   - 定期更新依赖包

3. **性能优化**
   - 避免 N+1 查询
   - 适当使用缓存
   - 优化数据库查询

## 🆘 获取帮助

- 项目文档: `README.md`
- Django 官方文档: https://docs.djangoproject.com/
- 团队联系: 创建 GitHub Issue

## 📄 许可证

本项目采用 MIT 许可证，详情请参考 LICENSE 文件。