"""
自定义代理视图，基于django-revproxy，添加路径重写功能
用于处理Next.js等应用的静态资源路径问题
"""
from revproxy.views import ProxyView
from django.http import HttpResponse
from django.conf import settings
import os
import re

# 从环境变量获取主机地址
PROXY_HOST = os.getenv('PROXY_HOST', 'host.docker.internal')

# 端口配置映射
PROXY_CONFIG = {
    'blog': {
        'port': 8081,
        'host': PROXY_HOST,
    },
    'crm': {
        'port': 8082,
        'host': PROXY_HOST,
    },
    'nas': {
        'port': 5000,
        'host': PROXY_HOST,
    },
    'test': {
        'port': 5050,
        'host': PROXY_HOST,
    },
    'open-webui': {
        'port': 8085,
        'host': PROXY_HOST,
    },
    'knowmap': {
        'port': 8087,
        'host': PROXY_HOST,
    },
    'datav': {
        'port': 8083,
        'host': PROXY_HOST,
    },
}


class CustomProxyView(ProxyView):
    """
    自定义代理视图，继承自django-revproxy的ProxyView
    添加了路径重写功能，用于处理静态资源路径
    """
    
    def __init__(self, service_name, **kwargs):
        """
        初始化代理视图
        
        Args:
            service_name: 服务名称（如'blog', 'crm'）
        """
        self.service_name = service_name
        if service_name not in PROXY_CONFIG:
            raise ValueError(f'Service "{service_name}" not found in PROXY_CONFIG')
        
        config = PROXY_CONFIG[service_name]
        host = config['host']
        port = config['port']
        
        # 构建upstream URL
        upstream = f'http://{host}:{port}'
        
        # 调用父类初始化
        super().__init__(upstream=upstream, **kwargs)
    
    def dispatch(self, request, path='', *args, **kwargs):
        """
        处理请求，添加路径重写功能
        """
        # 调用父类的dispatch方法
        response = super().dispatch(request, path, *args, **kwargs)
        
        # 如果是HTML内容，重写其中的静态资源路径
        if hasattr(response, 'get'):
            content_type = response.get('Content-Type', '').lower()
        else:
            content_type = response.headers.get('Content-Type', '').lower() if hasattr(response, 'headers') else ''
        
        if 'text/html' in content_type:
            try:
                # 获取响应内容
                if hasattr(response, 'content'):
                    content = response.content
                elif hasattr(response, 'streaming_content'):
                    # 如果是流式响应，需要先读取
                    content = b''.join(response.streaming_content)
                else:
                    return response
                
                content_str = content.decode('utf-8')
                
                # 重写静态资源路径
                content_str = self._rewrite_paths(content_str)
                
                # 更新响应内容
                if hasattr(response, 'content'):
                    response.content = content_str.encode('utf-8')
                    response['Content-Length'] = str(len(response.content))
                else:
                    # 如果是流式响应，创建新的响应
                    from django.http import HttpResponse
                    new_response = HttpResponse(content_str.encode('utf-8'))
                    for key, value in response.items():
                        if key.lower() != 'content-length':
                            new_response[key] = value
                    new_response['Content-Length'] = str(len(new_response.content))
                    new_response.status_code = response.status_code
                    response = new_response
            except (UnicodeDecodeError, AttributeError, Exception) as e:
                # 如果重写失败，保持原内容不变
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f'Content rewrite skipped for {self.service_name}: {str(e)}')
        
        return response
    
    def _rewrite_paths(self, content_str):
        """
        重写HTML内容中的路径，将绝对路径转换为代理路径
        
        Args:
            content_str: HTML内容字符串
            
        Returns:
            重写后的HTML内容字符串
        """
        service_name = self.service_name
        
        # 获取upstream的host和port
        upstream_url = self.upstream
        # 从upstream URL中提取host和port
        import re as re_module
        match = re_module.match(r'http://([^:]+):(\d+)', upstream_url)
        if match:
            upstream_host = match.group(1)
            upstream_port = match.group(2)
            
            # 重写所有指向upstream的绝对URL
            for host_to_try in [upstream_host, '127.0.0.1', 'localhost']:
                target_base = f'http://{host_to_try}:{upstream_port}'
                if target_base in content_str:
                    content_str = content_str.replace(
                        f'http://{host_to_try}:{upstream_port}/',
                        f'/{service_name}/'
                    )
                    # 使用正则表达式处理更复杂的情况
                    content_str = re_module.sub(
                        rf'http://{re_module.escape(host_to_try)}:{upstream_port}([^"\'>\s]*)',
                        rf'/{service_name}\1',
                        content_str
                    )
        
        # 修复相对路径函数
        def fix_relative_path(path, svc_name):
            # 如果是外部URL（http/https），保持原样
            if path.startswith('http://') or path.startswith('https://'):
                return path
            # 如果已经是绝对路径（以/开头），添加服务名前缀
            if path.startswith('/') and not path.startswith(f'/{svc_name}/'):
                # 包括所有静态资源路径：
                # - Next.js: /_next/, /_static/
                # - 通用: /static/, /assets/, /css/, /js/, /images/, /img/
                return f'/{svc_name}{path}'
            # 如果是相对路径，保持原样
            return path
        
        # 处理HTML属性中的绝对路径（如 href="/path" 或 src="/path"）
        def fix_path_in_attr(match):
            attr_name = match.group(1)  # href, src, action等
            path = match.group(2)  # 路径值
            fixed_path = fix_relative_path(path, service_name)
            return f'{attr_name}="{fixed_path}"'
        
        # 匹配HTML属性中的路径并修复
        content_str = re_module.sub(
            r'(href|src|action)=["\']([^"\']+)["\']',
            fix_path_in_attr,
            content_str
        )
        
        # 也处理CSS中的url()路径
        def fix_css_url(match):
            full_match = match.group(0)
            url_content = match.group(1) if match.lastindex >= 1 else ''
            url_path = url_content.strip('"\'').strip()
            # 如果是绝对路径，添加服务名前缀
            if url_path.startswith('/') and not url_path.startswith(f'/{service_name}/'):
                if not url_path.startswith('http'):
                    fixed_url = f'/{service_name}{url_path}'
                    quote_char = ''
                    if url_content.startswith('"') or url_content.startswith("'"):
                        quote_char = url_content[0]
                    return f'url({quote_char}{fixed_url}{quote_char})'
            return full_match
        
        # 匹配CSS中的url()函数
        content_str = re_module.sub(
            r'url\(["\']?([^"\'()]+)["\']?\)',
            fix_css_url,
            content_str,
            flags=re_module.IGNORECASE
        )
        
        return content_str
    
    def get_proxy_request_headers(self, request):
        """
        重写请求头，设置正确的Host头
        """
        headers = super().get_proxy_request_headers(request)
        
        # 设置Host头为127.0.0.1:port，避免目标服务的ALLOWED_HOSTS检查问题
        upstream_url = self.upstream
        import re as re_module
        match = re_module.match(r'http://([^:]+):(\d+)', upstream_url)
        if match:
            port = match.group(2)
            headers['Host'] = f'127.0.0.1:{port}'
        
        return headers

