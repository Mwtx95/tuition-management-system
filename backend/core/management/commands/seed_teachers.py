from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Role, UserRole


class Command(BaseCommand):
    help = "Seed default teacher users"

    def handle(self, *args, **options):
        User = get_user_model()
        password = "Lumumba@2020"

        teachers = [
            {"username": "mwalim_math", "first_name": "Mathematics", "last_name": "Teacher"},
            {"username": "mwalim_eng", "first_name": "English", "last_name": "Teacher"},
            {"username": "mwalim_kisw", "first_name": "Kiswahili", "last_name": "Teacher"},
            {"username": "mwalim_arab", "first_name": "Arabic", "last_name": "Teacher"},
            {"username": "mwalim_dini", "first_name": "Dini", "last_name": "Teacher"},
            {"username": "mwalim_scie", "first_name": "Science and Technology", "last_name": "Teacher"},
            {"username": "mwalim_ss", "first_name": "Social Studies", "last_name": "Teacher"},
            {"username": "mwalim_ca", "first_name": "Creative Arts", "last_name": "Teacher"},
        ]

        teacher_role, _ = Role.objects.get_or_create(name="Teacher")

        for teacher_data in teachers:
            user, created = User.objects.get_or_create(
                username=teacher_data["username"],
                defaults={
                    "first_name": teacher_data["first_name"],
                    "last_name": teacher_data["last_name"],
                    "email": f"{teacher_data['username']}@example.com",
                }
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created teacher user '{user.username}' with password '{password}'"
                    )
                )
            else:
                # Update existing user
                user.first_name = teacher_data["first_name"]
                user.last_name = teacher_data["last_name"]
                user.email = f"{teacher_data['username']}@example.com"
                user.set_password(password)
                user.save()
                self.stdout.write(
                    f"Updated teacher user '{user.username}' with password '{password}'"
                )

            # Assign role
            user_role, role_created = UserRole.objects.get_or_create(
                user=user, role=teacher_role
            )
            if role_created:
                self.stdout.write(
                    f"Assigned 'Teacher' role to '{user.username}'"
                )

        self.stdout.write(
            self.style.SUCCESS("Teacher seeding completed.")
        )