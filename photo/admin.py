from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from .models import Photo, Tag

SPECIAL_USERS = {'fei', 'user1', 'user2', 'user3'}  # 可以查看所有照片的用户

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    ordering = ('-date_joined',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.username in SPECIAL_USERS:
            return qs
        return qs.filter(id=request.user.id)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created')
    search_fields = ('name',)

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created', 'get_tags_display')
    list_filter = ('user', 'created', 'tags')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags',)

    def get_tags_display(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    get_tags_display.short_description = '标签'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.username in SPECIAL_USERS:
            return qs
        return qs.filter(user=request.user)
    
    def save_model(self, request, obj, form, change):
        if not change:  # 如果是新建照片
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        return request.user.username in SPECIAL_USERS or obj.user == request.user
    
    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        return request.user.username in SPECIAL_USERS or obj.user == request.user
    
    def has_view_permission(self, request, obj=None):
        if obj is None:
            return True
        return request.user.username in SPECIAL_USERS or obj.user == request.user

# 重新注册 User 和 Photo 模型
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# 创建特殊用户组
def create_special_group():
    try:
        special_group, created = Group.objects.get_or_create(name='SpecialUsers')
        if created:
            print("Created SpecialUsers group")
        
        # 确保特殊用户在这个组中
        for username in SPECIAL_USERS:
            try:
                user = User.objects.get(username=username)
                user.groups.add(special_group)
                user.is_staff = True  # 确保可以访问管理界面
                user.save()
                print(f"Added {username} to SpecialUsers group")
            except User.DoesNotExist:
                print(f"User {username} does not exist")
    except Exception as e:
        print(f"Error creating special group: {e}")

# 在 Django 启动时创建特殊用户组
admin.site.ready = create_special_group