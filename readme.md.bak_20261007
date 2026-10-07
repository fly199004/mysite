# 飞云老师个人网站（mysite）

基于 Django 3.2 的个人网站系统，部署在群晖 NAS 的 Docker 容器中。
网站定位：用于交流 IT 技能与 AI 知识，并聚合个人开发的各类在线工具。

- 访问地址：<https://www.liufeisheng.cn/>
- 容器端口：宿主机 **8084** → 容器内 **8000**
- 技术栈：Python 3.11 + Django 3.2 + MongoDB（主库）+ SQLite（账号库 / 课堂库）+ 阿里云 OSS（图床）

---

## 一、系统功能总览

全站由 4 个 Django 应用组成：

| 应用 | 路径前缀 | 说明 |
| --- | --- | --- |
| myapp | `/` | 主站：首页、文章阅读、个人介绍、外链导航 |
| photo | `/photo/` | 相册：照片浏览、标签筛选、上传，图片存阿里云 OSS |
| classroom | `/classroom/` | 课堂随机点名与积分排行榜（单页应用） |
| accounts | `/accounts/` | 全站账号体系：登录、改密、用户管理 |

另有 Django 自带后台：`/admin/`。

### 1. 主站 myapp

- **首页 `/`**：网站介绍 + 个人开发/推荐网站入口（个人博客、CRM、数据可视化、数字化人文、Open WebUI、知识图谱、课堂点名等）+ 常用网站链接 + NAS 入口。
- **文章阅读**：文章数据来自 MongoDB 的 `vanBlog` 库，正文为 Markdown，服务端渲染为 HTML，并自动生成章节目录（TOC），正文中的 Markdown 图片语法自动转换为 `<img>`。
  - `/articles/`、`/post/`：全部文章
  - `/reading/`：分类 reading（阅读类）
  - `/teach/`：分类 teach（教学类）
  - `/tech/`：分类 tech（技术类）
  - 支持按文章数字 ID 打开详情，如 `/tech/12/`
- **个人介绍 `/me/`（别名 `/aboutme/`）**
- **数据可视化页 `/datav/`**
- **数字化人文页 `/dh/`**
- 页面适配手机端：目录可收起为小图标，侧边栏在正文中后置显示。

### 2. 相册 photo（`/photo/`）

- 照片以**瀑布/分页列表**展示（每页 12 张），按上传时间倒序。
- 支持按**标签筛选**；详情页展示大图、标题与描述。
- **登录后可批量上传照片**（多文件选择）。
- 单张图片超过 3MB 时自动用 Pillow 压缩为 JPEG。
- 图片文件实际存储在**阿里云 OSS**，数据库只保存相对路径（`用户名/年份/文件名`）。
- 列表与详情通过 **OSS 签名 URL** 访问，有效期 1 小时；删除照片时同步删除 OSS 文件。
- 编辑权限：超级管理员、照片上传者，以及内置授权用户（fei、sisi、user1~3）可修改照片信息。

### 3. 课堂点名积分榜 classroom（`/classroom/`）

面向课堂教学的单页工具，核心功能：

- **多班级管理**：新建、重命名、删除、切换当前班级；班级与服务器当前选中状态会被记住。
- **随机滚动点名**：从当前班级名单中随机抽取学生。
- **积分系统**：对学生加分 / 减分，自动生成积分排行榜（状元、榜眼、探花等头衔）。
- **操作撤销**：积分操作带撤销栈，可一键撤销上一步。
- **名单导入**：上传 Excel（xlsx/xls）批量导入学生名单，可选择覆盖或追加，支持导入初始积分。
- **备份与恢复**：
  - 单班导出 / 恢复 JSON 备份；
  - 一次性导出 / 恢复全部班级；
  - 导出积分排名为 Excel。
- **其他**：全屏展示、演示数据、清空名单、搜索等。
- 权限策略：查询（GET）公开，任何写操作（新建班级、改分、导入、恢复等）必须登录。

### 4. 账号体系 accounts（`/accounts/`）

详见下一节。

---

## 二、账号与登录

### 登录入口

- 登录页：`/accounts/login/`
- 登出：`/accounts/logout/`（退出后回到首页）
- 全站登录策略由 `accounts/middleware.py` 统一控制：
  - **查询类请求（GET / HEAD / OPTIONS）公开可访问**；
  - **所有写操作（POST / PUT / PATCH / DELETE）必须登录**；
  - 普通页面未登录时跳转登录页（带 `next` 参数，登录后跳回原页面）；
  - AJAX / JSON 接口未登录时返回 HTTP 401 及 `{"login_required": true}`，前端据此跳转登录。

### 默认管理员账号

容器启动时会自动执行 `python manage.py ensure_admin`：

- 用户名：**fei**
- 密码：**fei**

该命令仅在账号不存在时创建；若账号已存在（例如已改过密码），不会覆盖。
**首次登录后请尽快通过 `/accounts/password/` 修改默认密码。**

### 账号能做什么

| 角色 | 权限 |
| --- | --- |
| 未登录访客 | 浏览首页、文章、相册、课堂名单与排行榜等所有公开内容 |
| 已登录普通账号 | 修改自己的密码；上传照片；课堂点名的全部写操作（点名积分、导入、备份恢复等） |
| 管理员（is_staff / 超级用户） | 以上全部，外加用户管理与 Django 后台 |

### 普通用户功能

- 修改自己的密码：`/accounts/password/`（修改成功后会话保持登录，不会被踢下线）。

### 管理员功能（`/accounts/manage/`）

仅 staff / 超级用户可访问，已登录但非管理员访问返回 403：

- **用户列表**：查看全部账号
- **新建账号**：设置用户名与初始密码，可勾选“允许登录后台管理”（is_staff）
- **启用 / 停用账号**（不能停用自己）
- **重置账号密码**
- **删除账号**（不能删除超级管理员，也不能删除自己）

Django 自带后台 `/admin/` 同样使用该账号体系。

---

## 三、数据库架构（三库分离）

为规避 djongo 与 Django 认证表的兼容问题，系统采用三库分离设计：

| 数据库 | 类型 | 文件 / 地址 | 存放内容 |
| --- | --- | --- | --- |
| default | MongoDB | `mongodb://172.17.0.1:27017/vanBlog` | 主站文章等业务数据（`vanBlog` 库） |
| accounts | SQLite | `accounts.sqlite` | auth 用户、组、会话、后台及 accounts 应用全部表 |
| classroom | SQLite | `classroom.sqlite` | 班级（`classroom_room`）、当前班级（`classroom_current`） |

- 通过 `accounts/db_router.py`、`classroom/db_router.py` 两个路由把对应模型定向到各自数据库。
- 容器通过 `extra_hosts: host.docker.internal:host-gateway` 及 `172.17.0.1` 访问宿主机上的 MongoDB。
- 设置环境变量 `USE_MONGO=true` 时使用 MongoDB；未设置时默认库回退为本地 `db.sqlite3`（便于本地开发）。

---

## 四、部署与运行

### 使用 docker compose（当前方式）

```bash
cd /volume1/docker/mysite   # NAS 上对应 \\FeiNas\docker\mysite
docker compose up -d --build
```

`docker-compose.yml` 启动命令会依次执行：

```bash
python manage.py migrate --database=accounts     # 迁移账号库
python manage.py migrate classroom --database=classroom  # 迁移课堂库
python manage.py ensure_admin                    # 确保管理员 fei 存在
python manage.py runserver 0.0.0.0:8000          # 启动服务
```

策略：`restart: always`，容器退出后自动重启。

### 必需的环境变量（.env）

阿里云 OSS 配置通过项目根目录 `.env` 注入：

```env
OSS_ACCESS_KEY_ID=你的AccessKeyId
OSS_ACCESS_KEY_SECRET=你的AccessKeySecret
OSS_BUCKET_NAME=你的Bucket名称
OSS_ENDPOINT=OSS地域域名（如 oss-cn-guangzhou.aliyuncs.com）
```

compose 中已设置 `USE_MONGO=true`。

### 静态文件

- 源码静态目录：`static/`
- 收集目录：`staticfiles/`（已挂载卷）
- 收集命令：`python manage.py collectstatic`

---

## 五、常用运维命令

```bash
# 查看容器日志
docker compose logs -f web

# 重启服务
docker compose restart web

# 重新执行数据库迁移
docker compose exec web python manage.py migrate --database=accounts
docker compose exec web python manage.py migrate classroom --database=classroom

# 手动确认 / 创建管理员（也可指定账号密码）
docker compose exec web python manage.py ensure_admin
docker compose exec web python manage.py ensure_admin --username fei --password 新密码

# 创建 Django 超级用户（进入 /admin 后台）
docker compose exec web python manage.py createsuperuser

# 备份 SQLite 库（在 NAS 上直接复制文件即可）
accounts.sqlite      # 账号库
classroom.sqlite     # 课堂点名库
```

> 注意：账号库与课堂库是独立 SQLite 文件，备份时两个文件都要复制；
> 文章数据在宿主机 MongoDB 的 `vanBlog` 库中，需通过 MongoDB 的备份机制处理。

---

## 六、目录结构

```
mysite/
├── manage.py
├── docker-compose.yml          # 容器编排（8084→8000）
├── Dockerfile                  # Python 3.11-slim
├── requirements.txt
├── accounts.sqlite             # 账号库（运行时生成）
├── classroom.sqlite            # 课堂点名库（运行时生成）
├── mysite/                     # 项目配置（settings/urls/wsgi）
├── myapp/                      # 主站应用
├── photo/                      # 相册应用（含 oss_utils.py）
├── classroom/                  # 课堂点名积分应用
├── accounts/                   # 账号应用（中间件/路由/管理命令）
├── static/                     # 静态资源源码
├── staticfiles/                # collectstatic 输出
└── templates（各应用内）        # 页面模板
```

---

## 附：旧版首页设计备忘（2026-01-07）

- 首页重新设计：常用链接放入 right-sidebar，文章列表下增加常用网站链接与 NAS 链接（nas.liufeisheng.cn）。
- 中间内容区不做个人基本介绍，改为说明建站目的（交流 IT 技能与 AI 知识），并展示个人开发或推荐的网站：
  - blog.liufeisheng.cn：个人博客
  - crm.liufeisheng.cn：自研英文 CRM 客户关系管理系统
  - https://www.liufeisheng.cn/datav/：数据可视化工具（上传 Excel/CSV 生成柱状图、折线图、饼图、环形图、雷达图等）
  - https://dh.liufeisheng.cn/：数字化人文技术
  - 8085 端口：Open WebUI（Docker 容器）
  - 8059 端口：交互式知识图谱
- 手机端 CSS 优化：缩小内容遮挡、目录滚动时收缩为小图标、left-sidebar 放到正文之后显示。
