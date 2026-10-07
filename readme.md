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
| myapp | `/` | 主站：首页、文章阅读、个人介绍、外链导航、在线实用工具 |
| photo | `/photo/` | 相册：照片浏览、标签筛选、上传，图片存阿里云 OSS |
| classroom | `/classroom/` | 课堂随机点名与积分排行榜（单页应用） |
| accounts | `/accounts/` | 全站账号体系：登录、改密、用户管理、登录态接口 |

另有 Django 自带后台：`/admin/`。

### 1. 主站 myapp

- **首页 `/`**：网站介绍 + 「个人开发在线实用工具」入口 + 「个人开发的网站与推荐工具」入口 + 常用网站链接 + NAS 入口。
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

### 2. 个人开发在线实用工具（`/tools/`）

三个工具均为单页应用，挂在 myapp 下，复用全站账号体系。

#### 2.1 通用知识图谱生成器 `/tools/knowmap/`

- 粘贴任意学科的大纲即可生成**交互式知识网络图**，不限学科领域（适用于课程梳理、读书笔记、知识体系搭建等）。
- 大纲解析兼容多种写法：
  - Markdown 标题层级：`#`、`##`、`###`…
  - 数字章节：`1.`、`1)`、`一、`…
  - 列表符号配合缩进：`-`、`*`、`+`，缩进越深层级越细。
- 布局方式：层级自上而下、层级从左到右、力导向自由网络。
- 交互：节点可拖拽、画布可缩放平移、悬停提示。
- 导出：一键导出当前图谱为 PNG 图片；可自定义根节点名称，内置「数据结构」示例。
- 版权声明：本工具为《交互式知识图谱可视化系统》，已获国家版权局**计算机软件著作权登记，登记号 2026SR0460334**；页面顶部版权条与首页卡片均有标注。
- 图谱库使用本地静态资源 `vis-network`（`static/lib/vis-network.min.js`），不依赖外部 CDN。

#### 2.2 二维码标签生成器 `/tools/label/`

- 离线可用的二维码标签制作工具：自定义文字与二维码内容、尺寸和排版。
- 一键「生成标签 PDF」，所有操作在浏览器本地完成，数据不上传。
- 页面内嵌 jsPDF、JSZip 等库，适合物料贴标、资产编号等场景。

#### 2.3 飞云轩提词器 `/tools/prompter/`

- 简洁的浏览器提词器：滚动速度与字号调节、全屏、镜像翻转、语速停顿标记。
- 支持开始/暂停/继续、重置、改稿，手机与电脑均可使用，适合短视频口播与课程录制。

> 三个在线工具统一采用「**未登录免费使用 5 次，登录后不限次**」策略，详见第二节第 4 小节。

### 3. 相册 photo（`/photo/`）

- 照片以**瀑布/分页列表**展示（每页 12 张），按上传时间倒序。
- 支持按**标签筛选**；详情页展示大图、标题与描述。
- **登录后可批量上传照片**（多文件选择）。
- 单张图片超过 3MB 时自动用 Pillow 压缩为 JPEG。
- 图片文件实际存储在**阿里云 OSS**，数据库只保存相对路径（`用户名/年份/文件名`）。
- 列表与详情通过 **OSS 签名 URL** 访问，有效期 1 小时；删除照片时同步删除 OSS 文件。
- 编辑权限：超级管理员、照片上传者，以及内置授权用户（fei、sisi、user1~3）可修改照片信息。

### 4. 课堂点名积分榜 classroom（`/classroom/`）

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

### 5. 账号体系 accounts（`/accounts/`）

详见下一节。

---

## 二、账号与登录

### 1. 登录入口

- 登录页：`/accounts/login/`
- 登出：`/accounts/logout/`（退出后回到首页）
- 修改密码：`/accounts/password/`
- 全站登录策略由 `accounts/middleware.py` 统一控制：
  - **查询类请求（GET / HEAD / OPTIONS）公开可访问**；
  - **所有写操作（POST / PUT / PATCH / DELETE）必须登录**；
  - 普通页面未登录时跳转登录页（带 `next` 参数，登录后跳回原页面）；
  - AJAX / JSON 接口未登录时返回 HTTP 401 及 `{"login_required": true}`，前端据此跳转登录。

### 2. 默认管理员账号

容器启动时会自动执行 `python manage.py ensure_admin`：

- 用户名：**fei**
- 密码：**fei**

该命令仅在账号不存在时创建；若账号已存在（例如已改过密码），不会覆盖。
**首次登录后请尽快通过 `/accounts/password/` 修改默认密码。**

### 3. 账号能做什么

| 角色 | 权限 |
| --- | --- |
| 未登录访客 | 浏览首页、文章、相册、课堂名单与排行榜；三个在线工具各免费使用 5 次 |
| 已登录普通账号 | 修改自己的密码；上传照片；课堂点名的全部写操作；三个在线工具不限次使用 |
| 管理员（is_staff / 超级用户） | 以上全部，外加用户管理与 Django 后台 |

### 4. 在线工具的「5 次免费」门控

知识图谱、二维码标签、飞云轩提词器三个工具共用同一套前端门控机制：

- 每个工具的使用次数独立保存在浏览器 `localStorage`，键名分别为：
  - `tool_usage_knowmap`
  - `tool_usage_labelgen`
  - `tool_usage_prompter`
- **未登录**：前 5 次操作正常放行并累计次数；第 6 次起弹出登录提示框，需登录后才能继续。
- **已登录**：不计数、不拦截，显示「已登录 · 使用不限次」。
- 计数的触发动作：
  - 知识图谱：点击「生成图谱」；
  - 标签生成器：点击「生成标签 PDF」；
  - 提词器：仅在「开启新一轮」（按钮文本为「开始」）时计数，暂停 / 继续不计数。
- 登录态由页面启动时请求登录态接口获得（见下），门控脚本在 `document` 捕获阶段先于原业务逻辑拦截动作，放行时业务正常执行，拦截时 `stopPropagation + preventDefault`。

### 5. 登录态查询接口

- 地址：`/accounts/api/me/`（GET，免登录）
- 返回示例：

```json
{ "authenticated": false, "username": "", "is_staff": false }
```

- 已登录时 `authenticated` 为 `true`，并返回 `username` 与 `is_staff`。三个在线工具据此决定是否计数拦截。

### 6. 普通用户功能

- 修改自己的密码：`/accounts/password/`（修改成功后会话保持登录，不会被踢下线）。

### 7. 管理员功能（`/accounts/manage/`）

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
- 在线工具的使用次数保存在用户浏览器 `localStorage`，不写入上述数据库。

---

## 四、部署与运行

### 使用 docker compose（当前方式）

```bash
cd /volume1/docker/mysite   # NAS 上对应 \\FeiNas\docker\mysite
docker compose up -d --build
```

`docker-compose.yml` 启动命令会依次执行：

```bash
python manage.py migrate --database=accounts        # 迁移账号库
python manage.py migrate classroom --database=classroom   # 迁移课堂库
python manage.py ensure_admin                       # 确保管理员 fei 存在
python manage.py runserver 0.0.0.0:8000             # 启动服务
```

策略：`restart: always`，容器退出后自动重启。

> 提示：runserver 的自动重载依赖文件变更检测。通过 SMB 更新代码后若路由/视图未立即生效，可在容器内 `touch` 对应文件，或执行 `docker compose restart web`。

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

- 源码静态目录：`static/`（含 `static/lib/vis-network.min.js`）
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
├── myapp/                      # 主站应用（含在线工具视图/路由）
│   └── templates/tools/        # knowmap.html / label_generator.html / prompter.html
├── photo/                      # 相册应用（含 oss_utils.py）
├── classroom/                  # 课堂点名积分应用
├── accounts/                   # 账号应用（中间件/路由/管理命令，api_me 接口）
├── static/                     # 静态资源源码（lib/vis-network.min.js）
├── staticfiles/                # collectstatic 输出
└── templates（各应用内）         # 页面模板
```

在线工具相关路由（myapp/urls.py）：

```
/tools/knowmap/   name='tool_knowmap'
/tools/label/     name='tool_label'
/tools/prompter/  name='tool_prompter'
```

---

## 七、在线工具 URL 一览

| 工具 | 地址 | 门控 |
| --- | --- | --- |
| 通用知识图谱生成器 | `/tools/knowmap/` | 未登录 5 次，登录无限；软著登记号 2026SR0460334 |
| 二维码标签生成器 | `/tools/label/` | 未登录 5 次，登录无限 |
| 飞云轩提词器 | `/tools/prompter/` | 未登录 5 次，登录无限 |
| 课堂点名积分榜 | `/classroom/` | 查看公开，写操作需登录 |

---

## 附：更新备忘

- 2026-10-07：新增「个人开发在线实用工具」区，接入通用知识图谱生成器、二维码标签生成器、飞云轩提词器三个单页工具；统一加入「未登录 5 次、登录后无限」门控；新增登录态接口 `/accounts/api/me/`。
- 知识图谱工具相关软件《交互式知识图谱可视化系统》获计算机软件著作权登记，登记号 2026SR0460334。
- 门控注入注意：二维码工具原始 jsPDF 代码内嵌有字符串形式的 `</body>`，注入脚本须定位**最后一个**真正的 `</body>`，否则会插进 jsPDF 脚本块导致页面脚本提前闭合、正文乱码。
