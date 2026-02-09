from django.core.management.base import BaseCommand

from core.models import ClassRoom, Subject


class Command(BaseCommand):
    help = "Seed default subjects for all class rooms"

    def handle(self, *args, **options):
        subjects = [
            {"name": "Mathematics", "code": "MATH"},
            {"name": "English", "code": "ENG"},
            {"name": "Kiswahili", "code": "KISW"},
            {"name": "Arabic", "code": "ARAB"},
            {"name": "Dini", "code": "DINI"},
            {"name": "Science and Technology", "code": "SCIT"},
            {"name": "Social Studies", "code": "SOSC"},
            {"name": "Creative Arts", "code": "CART"},
        ]

        class_rooms = ClassRoom.objects.all()
        if not class_rooms:
            self.stdout.write(
                self.style.WARNING("No class rooms found. Please create class rooms first.")
            )
            return

        for class_room in class_rooms:
            for subject_data in subjects:
                subject, created = Subject.objects.get_or_create(
                    name=subject_data["name"],
                    code=subject_data["code"],
                    class_room=class_room,
                    defaults={}
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created subject '{subject.name}' for class '{class_room.name}'"
                        )
                    )
                else:
                    self.stdout.write(
                        f"Subject '{subject.name}' already exists for class '{class_room.name}'"
                    )

        self.stdout.write(
            self.style.SUCCESS("Subject seeding completed.")
        )