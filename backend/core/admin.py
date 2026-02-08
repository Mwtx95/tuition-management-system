from django.contrib import admin
from .models import (
    ClassRoom,
    Exam,
    Permission,
    Result,
    Role,
    RolePermission,
    Student,
    Subject,
    UserRole,
)

admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(RolePermission)
admin.site.register(UserRole)
admin.site.register(ClassRoom)
admin.site.register(Student)
admin.site.register(Subject)
admin.site.register(Exam)
admin.site.register(Result)
