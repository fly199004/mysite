from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import os
from .models import Photo, Tag
from mysite import settings
from .oss_utils import OssStorage
from PIL import Image
from io import BytesIO
import sys

# Create your views here.


@login_required
def photo_list(request):
    # 获取标签过滤参数
    tag_id = request.GET.get('tag')
    
    # 基础查询集
    photos = Photo.objects.all()
    
    # 如果指定了标签，进行过滤
    if tag_id:
        photos = photos.filter(tags__id=tag_id)
    
    # 按时间倒序排序
    photos = photos.order_by('-created')
    
    # 获取所有标签供筛选使用
    all_tags = Tag.objects.all()
    
    # 创建分页器
    paginator = Paginator(photos, 12)
    page = request.GET.get('page', 1)
    photos = paginator.get_page(page)
    
    # 为每张照片生成签名URL
    for photo in photos:
        photo.image_url = photo.get_signed_url()
    
    return render(request, 'photo_list.html', {
        'photos': photos,
        'page_obj': photos,
        'all_tags': all_tags,
        'current_tag': tag_id
    })

@login_required
def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    
    # 检查用户权限
    if not request.user.is_superuser and request.user.username not in ['fei', 'sisi','user1', 'user2', 'user3'] and photo.user != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': '您没有权限编辑此照片'})
        return redirect('photo:photo_list')
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 更新照片信息
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        
        try:
            photo.title = title
            photo.description = description
            photo.save()
            
            return JsonResponse({
                'success': True,
                'title': photo.title,
                'description': photo.description
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    # 生成签名URL
    oss_storage = OssStorage()
    photo.signed_url = oss_storage.get_signed_url(photo.image.name)
    
    return render(request, 'photo_detail.html', {'photo': photo})

def compress_image(image_file, max_size_mb=3):
    # 打开图片
    img = Image.open(image_file)
    
    # 如果是RGBA模式，转换为RGB
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # 初始质量
    quality = 95
    output = BytesIO()
    
    # 保存图片，检查大小
    img.save(output, format='JPEG', quality=quality)
    while output.tell() > max_size_mb * 1024 * 1024 and quality > 5:
        output = BytesIO()
        quality -= 5
        img.save(output, format='JPEG', quality=quality)
    
    # 重置文件指针位置
    output.seek(0)
    return output

@login_required
@csrf_exempt
def upload_photos(request):
    if request.method == 'POST':
        files = request.FILES.getlist('photos')
        results = []
        
        for file in files:
            try:
                print(f"Processing file: {file.name}")
                title = os.path.splitext(file.name)[0]
                
                if file.size > 3 * 1024 * 1024:
                    print(f"Compressing file: {file.name}")
                    compressed = compress_image(file)
                    file = compressed
                
                # 创建照片对象
                photo = Photo(
                    title=title,
                    image=file,
                    user=request.user
                )
                
                print(f"Saving photo to database: {title}")
                photo.save()
                print(f"Photo saved successfully: {photo.id}")
                
                results.append({
                    'name': file.name,
                    'success': True
                })
            except Exception as e:
                print(f"Error saving photo {file.name}: {str(e)}", file=sys.stderr)
                results.append({
                    'name': file.name,
                    'success': False,
                    'error': str(e)
                })
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'results': results})
        return redirect('photo:photo_list')
        
    return render(request, 'photo_upload.html')


def test(request):
    return render(request, 'test.html')

