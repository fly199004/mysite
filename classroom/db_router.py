"""数据库路由：classroom 应用的所有模型只走独立的 classroom SQLite。"""


class ClassroomRouter:
    target_db = 'classroom'
    app_label = 'classroom'

    def _is_target(self, model):
        return model._meta.app_label == self.app_label

    def db_for_read(self, model, **hints):
        if self._is_target(model):
            return self.target_db
        return None

    def db_for_write(self, model, **hints):
        if self._is_target(model):
            return self.target_db
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if self._is_target(obj1) and self._is_target(obj2):
            return True
        if self._is_target(obj1) or self._is_target(obj2):
            return False
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label:
            return db == self.target_db
        if db == self.target_db:
            return False
        return None
