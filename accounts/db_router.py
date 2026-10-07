"""账号库路由：与认证、用户、会话、后台相关的应用统一走 accounts SQLite。

这样即使主站默认库是 MongoDB(djongo)，登录与账号管理也使用标准 SQLite，
规避 djongo 对 Django auth 表的兼容问题。"""


class AccountsRouter:
    target_db = 'accounts'

    # 这些 app 的模型全部落在 accounts 库
    ROUTED_APPS = {
        'auth',          # 用户、组、权限
        'accounts',      # 本站账号应用
        'contenttypes',  # 内容类型
        'sessions',      # 会话
        'admin',         # 后台日志等
    }

    def _is_target(self, model):
        return model._meta.app_label in self.ROUTED_APPS

    def db_for_read(self, model, **hints):
        if self._is_target(model):
            return self.target_db
        return None

    def db_for_write(self, model, **hints):
        if self._is_target(model):
            return self.target_db
        return None

    def allow_relation(self, obj1, obj2, **hints):
        a = obj1._meta.app_label in self.ROUTED_APPS
        b = obj2._meta.app_label in self.ROUTED_APPS
        if a and b:
            return True
        if a or b:
            # 账号库与其它库之间不建立跨库关系
            return False
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.ROUTED_APPS:
            return db == self.target_db
        # 非账号应用不允许写入 accounts 库
        if db == self.target_db:
            return False
        return None
