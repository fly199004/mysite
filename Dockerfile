# 使用官方Python镜像,使用的是Ubuntu系统的python版本
FROM python:3.10.12

# 设置环境变量
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=1

# 设置工作目录
WORKDIR /usr/local/mysite

# 复制项目的requirements.txt文件
COPY requirements.txt ./

# 安装项目依赖
RUN python3 -m pip install --no-cache-dir --default-timeout=100 --no-build-isolation -r requirements.txt
COPY . .

EXPOSE 82

# 运行Django服务器
CMD ["python3", "manage.py", "runserver", "0.0.0.0:82"]
