from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.utils import timezone


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("role", "permission")


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "role")


class ClassRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.name


class Student(models.Model):
    GENDER_CHOICES = (("M", "Male"), ("F", "Female"))

    reg_no = models.CharField(max_length=20, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    address = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    def _reg_no_prefix():
        prefix = getattr(settings, "REG_NO_PREFIX", "BTC")
        year_suffix = timezone.now().year % 100
        return f"{prefix}/{year_suffix:02d}/"

    @classmethod
    def _next_reg_no(cls):
        prefix = cls._reg_no_prefix()
        last_student = (
            cls.objects.filter(reg_no__startswith=prefix).order_by("-reg_no").first()
        )
        if not last_student or not last_student.reg_no:
            next_seq = 1
        else:
            try:
                next_seq = int(last_student.reg_no.split("/")[-1]) + 1
            except (ValueError, IndexError):
                next_seq = 1
        return f"{prefix}{next_seq:03d}"

    def save(self, *args, **kwargs):
        if self.reg_no:
            return super().save(*args, **kwargs)
        for _ in range(5):
            try:
                with transaction.atomic():
                    self.reg_no = self._next_reg_no()
                    return super().save(*args, **kwargs)
            except IntegrityError:
                self.reg_no = None
                continue
        raise IntegrityError("Unable to generate unique registration number.")


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        unique_together = ("code", "class_room")

    def __str__(self):
        return f"{self.name} ({self.code})"


class Exam(models.Model):
    name = models.CharField(max_length=100)
    term = models.CharField(max_length=50)
    year = models.IntegerField()
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    is_published = models.BooleanField(default=False)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    published_at = models.DateTimeField(null=True, blank=True)

    def publish(self, user):
        self.is_published = True
        self.published_by = user
        self.published_at = timezone.now()
        self.save(update_fields=["is_published", "published_by", "published_at"])

    def __str__(self):
        return f"{self.name} {self.term} {self.year}"


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    marks = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "subject", "exam")

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.exam}"


class ResultPublication(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "exam")

    def publish(self, user):
        self.published_by = user
        self.published_at = timezone.now()
        self.save(update_fields=["published_by", "published_at"])
