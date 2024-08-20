# 个人网站设计

1. 放置博客信息
2. 放置个人信息页
   1. 个人主页仅修改了html，其他可以保持不变
3. 放crm系统
4. 更新博客信息及个人信息页面，布局、版式更改
   1. 博客将不同的页面分开，相互无法查看（IT教学、IT笔记、生活日记）
   2. 增加照片页面，仅个人或给予账号的可以查看



可以做的方式

- [ ] 让现有van-blog单独成一个体系，进行小修改
  - [ ] 页面着色修改
  - [ ] 各分栏内容隔开，相互不可见
  - [ ] 阅读栏,reading
  - [ ] IT记录栏,it
  - [ ] 教学栏，teching
  - [ ] 日常生活栏，life
- [ ] 单独设计首页，然后将van-blog链接进去，网址链接均保持不变
  - [ ] 重新设计个人网站
  - [ ] 疑问，域名访问如何解决？
    - 考虑用blog.liufeisheng.cn这个域名
    - 然后www.liufeisheng.cn首页，链接进去
  - [ ] 增加照片、视频页面



## 目前想法

- 用django设计网站，docker容器封闭，放进服务器使用
- 使用一级域名www.liufeisheng.cn
- 将van-blog、crm系统之类链接进去，原链接保持不变
- 参考https://www.kuangstudy.com/course建立课程、项目
  - [ ] 个人介绍原先的保留不变，新增 www.liufeisheng.cn/me链接，内容一致，但放到django项目中



## 整体框架思路

要在Windows上使用Django开发个人网站，并最终在Ubuntu系统上通过Docker进行封闭部署，你可以按照以下步骤进行：

### 1. 在Windows系统上进行Django开发
1. **安装依赖工具**
   - 确保安装了Python（推荐使用最新版本）。
   - 安装`pip`包管理工具。
   - 使用`pip`安装`virtualenv`，以便在虚拟环境中隔离你的项目依赖。

2. **创建虚拟环境并安装Django**
   ```bash
   python -m venv page_env
   page_env\Scripts\activate
   pip install django
   ```
   激活虚拟环境后，使用`pip`安装Django。

3. **创建Django项目**
   ```bash
   django-admin startproject mysite
   cd mysite
   python manage.py startapp myapp
   ```

4. **使用VSCode进行开发**
   
   - 打开VSCode并加载你的Django项目目录。
   - 安装VSCode的Python扩展，以获得语法高亮、代码提示等功能。
   - 配置`.vscode`文件夹中的`settings.json`文件，使VSCode可以正确识别和使用虚拟环境。
   
5. **在Windows上进行测试运行**
   ```bash
   python manage.py runserver
   ```
   确保在Windows环境中可以成功运行Django项目。

### 2. Docker化并部署到Ubuntu系统
1. **编写Dockerfile**
   在Django项目的根目录下创建一个`Dockerfile`，内容如下：
   
   ```dockerfile
   # 使用官方Python镜像
   FROM python:3.x
   
   # 设置工作目录
   WORKDIR /usr/src/app
   
   # 复制项目的requirements.txt文件
   COPY requirements.txt ./
   
   # 安装项目依赖
   RUN pip install --no-cache-dir -r requirements.txt
   
   # 复制项目文件到工作目录
   COPY . .
   
   # 运行Django服务器
   CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
   ```
   
2. **编写`requirements.txt`文件**
   使用以下命令生成依赖文件：
   ```bash
   pip freeze > requirements.txt
   ```

3. **编写`docker-compose.yml`文件**（可选）
   如果需要使用数据库等服务，可以编写`docker-compose.yml`文件。

4. **在Ubuntu系统上构建和运行Docker容器**
   
   - 将你的Django项目代码上传到Ubuntu系统。
   - 使用以下命令构建并运行Docker容器：
     ```bash
     docker build -t mydjangoapp .
     docker run -d -p 8000:8000 mydjangoapp
     ```
   
5. **配置Nginx和Docker（可选）**
   如果需要使用Nginx作为反向代理，还需要编写Nginx配置文件并将其与Docker容器集成。

### 3. 代码上传和同步
1. **使用Git进行版本控制和上传**
   - 在本地Windows系统上使用Git管理代码，并将代码推送到GitHub、GitLab等远程代码仓库。
   - 在Ubuntu系统上通过Git拉取代码并进行Docker构建和部署。



## 网站基本设置

### 静态文件设计

### 1. 设计Django项目的静态目录

在Django项目中，通常会有一个专门的目录用于存放静态文件（如CSS、JavaScript、图像等）。为了设计一个静态目录，可以按以下步骤操作：

1. **创建静态目录结构**
   在Django项目的根目录下创建一个名为`static`的文件夹。可以按如下结构进行组织：
   ```
   mysite/
   ├── manage.py
   ├── mysite/
   │   ├── settings.py
   │   ├── urls.py
   │   └── ...
   ├── myapp/
   │   ├── views.py
   │   └── ...
   └── static/
       ├── css/
       ├── js/
       └── images/
   ```
   - `css/` 用于存放所有的CSS文件。
   - `js/` 用于存放所有的JavaScript文件。
   - `images/` 用于存放所有的图像文件。

2. **在Django设置中配置静态目录**
   打开`settings.py`文件，添加或修改以下配置：
   ```python
   STATIC_URL = '/static/'
   STATICFILES_DIRS = [
       BASE_DIR / "static",
   ]
   ```
   这样，Django将能够正确地识别和使用你定义的静态目录。

### 2. 设计一个简洁的首页

接下来，设计一个简单的首页模板，介绍网站的基本信息。假设你的网站主要介绍个人信息和一些项目经历，可以按以下步骤进行：

1. **创建一个HTML模板文件**
   在`myapp/templates/myapp/`目录下创建一个名为`index.html`的文件。目录结构应如下：
   ```
   mysite/
   ├── myapp/
   │   ├── templates/
   │   │   └── myapp/
   │   │       └── index.html
   └── ...
   ```

2. **编写HTML代码**
   `index.html`文件可以设计为如下的简单介绍页面：
   
   编辑个人主页，注意在要前面加{% load static %} 加载静态文件
   
   ```html
   {% load static %}
   <!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Welcome to My Personal Website</title>
       <link rel="stylesheet" href="{% static 'css/style.css' %}">
   </head>
   <body>
       <header>
           <h1>Welcome to My Personal Website</h1>
           <p>Explore my projects and learn more about me.</p>
       </header>
       <section>
           <h2>About Me</h2>
           <p>This is a brief introduction about myself. You can include your background, education, and current work here.</p>
       </section>
       <section>
           <h2>My Projects</h2>
           <p>Here is a list of my projects. Each project can have a brief description and a link to more details.</p>
       </section>
       <footer>
           <p>&copy; 2024 My Personal Website. All rights reserved.</p>
       </footer>
   </body>
   </html>
   ```
   
3. **创建对应的CSS文件**
   在`static/css/`目录下创建一个名为`style.css`的文件，编写一些基本样式：
   ```css
   body {
       font-family: Arial, sans-serif;
       margin: 0;
       padding: 0;
       background-color: #f4f4f4;
   }
   
   header {
       background-color: #333;
       color: #fff;
       padding: 20px;
       text-align: center;
   }
   
   section {
       padding: 20px;
       margin: 10px;
       background-color: #fff;
       border-radius: 5px;
       box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
   }
   
   footer {
       text-align: center;
       padding: 10px;
       background-color: #333;
       color: #fff;
   }
   ```

4. **配置视图和路由**
   最后，在`views.py`文件中创建一个视图函数来渲染首页，并在`urls.py`中配置路由：
   ```python
   # views.py
   from django.shortcuts import render
   
   def index(request):
       return render(request, 'myapp/index.html')
   
   # urls.py
   from django.urls import path
   from . import views
   
   urlpatterns = [
       path('', views.index, name='index'),
   ]
   ```

通过以上步骤，你将拥有一个基本的静态目录结构，并且首页设计也已完成。你可以根据需要进一步扩展和美化网站。



确保`myapp`已经在`settings.py`中的`INSTALLED_APPS`列表里注册。如果没有注册，Django将无法识别和使用该应用。

```
pythonCopy codeINSTALLED_APPS = [
    ...
    'myapp',  # 确保 myapp 在这里
]
```

### `myapp/urls.py` 的作用

`myapp/urls.py` 是你在`myapp`应用内的路由配置文件。它专门处理由`mysite/urls.py`分发过来的请求。通过这种方式，你可以将不同的应用模块化管理。通常你会在`myapp/urls.py`中定义与这个应用相关的URL和视图对应关系。例如：

```
from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index,name='index')
]
```

1. **HTML 与 CSS 基本设计基础：** 学习网页的基本结构和样式布局，掌握响应式设计技巧。
2. **JavaScript 动态网页设计：** 通过 JavaScript 实现网页的动态交互功能，提升用户体验。
3. **前端开发框架：** 使用 jQuery、Vue 等前端框架，开发模块化和高效的前端应用。
4. **数据库管理：** 学习数据库的基本操作与管理，为网站提供数据支持。
5. **Linux 操作系统与服务器配置：** 了解 Linux 系统的基本操作，以及服务器的配置与管理。
6. **Web 安全：** 掌握常见的 Web 安全漏洞与防护措施，确保网站的安全性。
7. **Docker 容器技术：** 通过 Docker 容器化技术，实现应用的快速部署与管理。
8. **Git 版本管理：** 学习 Git 的使用方法，进行项目的版本控制与协作开发。



## 上传至Ubuntu的Docker容器部署

网站大致设计好之后 ，通过git上传至服务器，然后放到Docker容器中实现