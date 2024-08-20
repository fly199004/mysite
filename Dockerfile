# 使用官方Python镜像
FROM python:3.x

# 设置工作目录
WORKDIR /var/www/Flynn

# 复制项目的requirements.txt文件
COPY requirements.txt ./

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件到工作目录
COPY . .

# 运行Django服务器
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]