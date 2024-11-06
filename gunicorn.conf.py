import multiprocessing

bind = "0.0.0.0:8000"  # 绑定的IP和端口
workers = multiprocessing.cpu_count() * 2 + 1  # 根据CPU核心数设定工作进程数
loglevel = 'info'  # 日志级别
errorlog = '/usr/local/mysite/logs/gunicorn-error.log'  # 错误日志文件
accesslog = '/usr/local/mysite/logs/gunicorn-access.log'  # 访问日志文件
