from django.core.management.base import BaseCommand

from core.models import Permission, Role, RolePermission


class Command(BaseCommand):
    help = "Seed default roles and permissions"

    def handle(self, *args, **options):
        permissions = {
            "upload_result": "Upload student results",
            "publish_result": "Publish exam results",
            "view_student_result": "View individual student result",
            "view_class_result": "View class result sheet",
            "crud_student": "Manage students",
            "crud_class": "Manage classes",
            "crud_subject": "Manage subjects",
            "manage_users": "Manage users",
            "view_analytics": "View analytics",
        }
        permission_objs = {}
        for code, description in permissions.items():
            permission_objs[code], _ = Permission.objects.get_or_create(
                code=code, defaults={"description": description}
            )
        roles = {
            "Admin": [
                "upload_result",
                "publish_result",
                "view_student_result",
                "view_class_result",
                "crud_student",
                "crud_class",
                "crud_subject",
                "manage_users",
                "view_analytics",
            ],
            "Teacher": ["upload_result", "view_student_result", "view_class_result"],
            "Exam Officer": [
                "publish_result",
                "view_student_result",
                "view_class_result",
                "view_analytics",
            ],
            "Parent": ["view_student_result"],
        }
        for role_name, permission_codes in roles.items():
            role, _ = Role.objects.get_or_create(name=role_name)
            for code in permission_codes:
                RolePermission.objects.get_or_create(
                    role=role, permission=permission_objs[code]
                )
        self.stdout.write(self.style.SUCCESS("Roles and permissions seeded."))
