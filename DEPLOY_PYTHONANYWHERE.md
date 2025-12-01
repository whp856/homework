# PythonAnywhere 部署指南

## 🎯 目标：10分钟内让您的Django项目上线访问

### 第1步：注册PythonAnywhere账户（2分钟）
1. 访问 [www.pythonanywhere.com](https://www.pythonanywhere.com/)
2. 点击 "Create a Free Account"
3. 填写用户名、邮箱、密码
4. 验证邮箱

### 第2步：创建Web应用（3分钟）
1. 登录后点击左侧菜单 "Web"
2. 点击 "+ Add a new web app"
3. 选择 "Manual configuration"
4. 选择 "Python 3.9" 或 "Python 3.10"
5. 点击确认

### 第3步：上传您的项目（3分钟）

**方法1：使用Git（推荐）**
```bash
# 在PythonAnywhere的Bash控制台中运行：
cd /home/您的用户名
git clone https://github.com/您的用户名/您的仓库名.git
cd 您的仓库名
```

**方法2：文件上传**
1. 将项目打包成zip文件
2. 在Files页面上传zip文件
3. 在Bash中解压：
```bash
cd /home/您的用户名
unzip 您的项目名.zip
```

### 第4步：配置虚拟环境（2分钟）
```bash
# 创建虚拟环境
mkvirtualenv --python=python3 library_system

# 激活虚拟环境（如果没有自动激活）
workon library_system

# 安装依赖
pip install django pillow gunicorn
```

### 第5步：配置Web应用（2分钟）

在PythonAnywhere的 "Web" 页面设置：

1. **Code** 部分：
   - **Source code**: `/home/您的用户名/您的项目名`

2. **Virtualenv** 部分：
   - **Virtualenv path**: `/home/您的用户名/.virtualenvs/library_system`

3. **WSGI configuration file** 部分：
   - 点击 "wsgi.py" 链接
   - 修改文件内容为：

```python
import os
import sys

path = '/home/您的用户名/您的项目名'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'library_management.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 第6步：配置静态文件（1分钟）
在Web页面设置：
- **Static files** 部分：
  - **URL**: `/static/`
  - **Directory**: `/home/您的用户名/您的项目名/static/`

### 第7步：创建数据库和超级用户（2分钟）
```bash
# 进入项目目录
cd /home/您的用户名/您的项目名

# 应用数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 收集静态文件
python manage.py collectstatic
```

### 第8步：重启Web应用（1分钟）
1. 在 "Web" 页面点击 "Reload" 按钮
2. 等待几分钟让服务启动

### 第9步：访问您的网站！🎉

您的网站地址将是：`https://您的用户名.pythonanywhere.com`

## 🔧 常见问题解决

### 如果出现500错误：
1. 检查错误日志：在Web页面点击 "Error log"
2. 最常见的问题是路径错误或依赖缺失

### 如果静态文件不显示：
1. 确保已经运行 `python manage.py collectstatic`
2. 检查静态文件路径配置是否正确

### 如果数据库错误：
1. 确保已经运行 `python manage.py migrate`
2. 检查数据库权限

## 📱 管理员后台访问

部署成功后，您可以访问：
- **网站首页**：`https://您的用户名.pythonanywhere.com`
- **管理员后台**：`https://您的用户名.pythonanywhere.com/admin`

## 🔄 代码更新流程

当您更新GitHub代码后，在PythonAnywhere的Bash中运行：
```bash
cd /home/您的用户名/您的项目名
git pull origin main
python manage.py migrate  # 如果有数据库更改
```

然后在Web页面点击 "Reload" 重启服务。

## 💡 成本说明

- **免费版本**：足够学习展示使用
  - 网站访问：每天限制
  - 存储空间：512MB
  - 带宽：100MB/天

- **付费版本**：如果需要更大流量
  - 每月约$5起

## 🎯 部署成功标志

如果您能正常看到您的图书管理系统首页，就说明部署成功了！
- 可以注册新用户
- 可以登录系统
- 可以查看图书列表
- 管理员功能正常

恭喜！您的Django项目现在可以被全世界访问了！🎉