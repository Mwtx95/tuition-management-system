from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnalyticsView,
    ClassResultView,
    ClassRoomViewSet,
    ExamViewSet,
    PublishExamView,
    ReportCardPdfView,
    ResultBulkUploadView,
    ResultUploadView,
    StudentResultView,
    StudentViewSet,
    SubjectViewSet,
)

router = DefaultRouter()
router.register("classes", ClassRoomViewSet)
router.register("students", StudentViewSet)
router.register("subjects", SubjectViewSet)
router.register("exams", ExamViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("results/upload", ResultUploadView.as_view(), name="result-upload"),
    path("results/bulk-upload", ResultBulkUploadView.as_view(), name="result-bulk-upload"),
    path("results/student/<int:student_id>", StudentResultView.as_view(), name="student-results"),
    path("results/class/<int:class_id>", ClassResultView.as_view(), name="class-results"),
    path("exams/<int:exam_id>/publish", PublishExamView.as_view(), name="publish-exam"),
    path(
        "report-card/<int:student_id>/<int:exam_id>/pdf",
        ReportCardPdfView.as_view(),
        name="report-card",
    ),
    path("analytics/class/<int:class_id>", AnalyticsView.as_view(), name="analytics"),
]
