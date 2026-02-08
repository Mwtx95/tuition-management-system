from django.contrib.auth import get_user_model
from rest_framework import serializers

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
from .services import grade_for_marks
from .permissions import get_user_permission_codes

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name"]


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "code", "description"]


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ["id", "user", "role"]


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ["id", "role", "permission"]


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "roles", "permissions"]

    def get_roles(self, obj):
        return list(UserRole.objects.filter(user=obj).values_list("role__name", flat=True))

    def get_permissions(self, obj):
        return list(get_user_permission_codes(obj))


class ClassRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassRoom
        fields = ["id", "name", "class_teacher"]


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "id",
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "class_room",
            "parent",
        ]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "code", "class_room", "teacher"]


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = [
            "id",
            "name",
            "term",
            "year",
            "class_room",
            "is_published",
            "published_by",
            "published_at",
        ]
        read_only_fields = ["is_published", "published_by", "published_at"]


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = [
            "id",
            "student",
            "subject",
            "exam",
            "marks",
            "grade",
            "uploaded_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["grade", "uploaded_by", "created_at", "updated_at"]

    def validate(self, attrs):
        exam = attrs.get("exam")
        if exam and exam.is_published:
            raise serializers.ValidationError("Cannot edit results after exam is published.")
        return attrs

    def create(self, validated_data):
        validated_data["grade"] = grade_for_marks(validated_data["marks"])
        validated_data["uploaded_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if instance.exam.is_published:
            raise serializers.ValidationError("Cannot edit results after exam is published.")
        if "marks" in validated_data:
            validated_data["grade"] = grade_for_marks(validated_data["marks"])
        return super().update(instance, validated_data)


class BulkResultItemSerializer(serializers.Serializer):
    student = serializers.IntegerField()
    subject = serializers.IntegerField()
    exam = serializers.IntegerField()
    marks = serializers.DecimalField(max_digits=5, decimal_places=2)


class BulkResultUploadSerializer(serializers.Serializer):
    results = BulkResultItemSerializer(many=True)
