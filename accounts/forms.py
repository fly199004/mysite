import django.forms as django_forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User


class StyledFormMixin:
    """统一控件样式。"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            cls = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (cls + ' acc-input').strip()
            if isinstance(field.widget, (django_forms.CheckboxInput,)):
                field.widget.attrs['class'] = 'acc-check'


class CreateUserForm(StyledFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'is_staff')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = '登录账号'
        self.fields['password1'].label = '密码'
        self.fields['password2'].label = '确认密码'
        self.fields['is_staff'].label = '允许登录后台管理'
        self.fields['is_staff'].help_text = '一般普通账号无需勾选。'


class AdminChangeUserForm(StyledFormMixin, UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'is_active', 'is_staff', 'is_superuser',
                  'groups', 'user_permissions')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 隐藏默认密码哈希字段，改密码用专门入口
        if 'password' in self.fields:
            self.fields['password'].help_text = (
                '如需修改密码，请使用列表中的“重置密码”功能。')
