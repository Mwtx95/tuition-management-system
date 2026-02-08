from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.db.models import Avg, Sum
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ClassRoom, Exam, Result, Student, Subject
from .permissions import HasPermission
from .serializers import (
    BulkResultUploadSerializer,
    ClassRoomSerializer,
    ExamSerializer,
    ResultSerializer,
    StudentSerializer,
    SubjectSerializer,
    UserSerializer,
)
from .services import analytics_for_class, calculate_rankings, grade_for_marks


class CurrentUserView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ClassRoomViewSet(viewsets.ModelViewSet):
    queryset = ClassRoom.objects.all()
    serializer_class = ClassRoomSerializer
    required_permission = "crud_class"
    permission_classes = [HasPermission]
    search_fields = ["name"]


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    required_permission = "crud_student"
    permission_classes = [HasPermission]
    search_fields = ["first_name", "last_name"]


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    required_permission = "crud_subject"
    permission_classes = [HasPermission]
    search_fields = ["name", "code"]


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    required_permission = "publish_result"
    permission_classes = [HasPermission]
    search_fields = ["name", "term", "year"]


class ResultUploadView(APIView):
    permission_classes = [HasPermission]
    required_permission = "upload_result"

    def post(self, request):
        serializer = ResultSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ResultBulkUploadView(APIView):
    permission_classes = [HasPermission]
    required_permission = "upload_result"

    def post(self, request):
        serializer = BulkResultUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = []
        for item in serializer.validated_data["results"]:
            exam = Exam.objects.get(id=item["exam"])
            if exam.is_published:
                return Response(
                    {"detail": "Cannot edit results after exam is published."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            result = Result.objects.create(
                student_id=item["student"],
                subject_id=item["subject"],
                exam_id=item["exam"],
                marks=item["marks"],
                grade=grade_for_marks(item["marks"]),
                uploaded_by=request.user,
            )
            created.append(ResultSerializer(result).data)
        return Response({"results": created}, status=status.HTTP_201_CREATED)


class StudentResultView(APIView):
    permission_classes = [HasPermission]
    required_permission = "view_student_result"

    def get(self, request, student_id):
        exam_id = request.query_params.get("exam_id")
        results = Result.objects.filter(student_id=student_id)
        if exam_id:
            results = results.filter(exam_id=exam_id)
        serializer = ResultSerializer(results, many=True)
        return Response(serializer.data)


class ClassResultView(APIView):
    permission_classes = [HasPermission]
    required_permission = "view_class_result"

    def get(self, request, class_id):
        exam_id = request.query_params.get("exam_id")
        results = Result.objects.filter(student__class_room_id=class_id)
        if exam_id:
            results = results.filter(exam_id=exam_id)
        totals = results.values("student").annotate(total=Sum("marks"), average=Avg("marks"))
        rankings = calculate_rankings(results)
        return Response({"results": ResultSerializer(results, many=True).data, "totals": list(totals), "rankings": rankings})


class PublishExamView(APIView):
    permission_classes = [HasPermission]
    required_permission = "publish_result"

    def post(self, request, exam_id):
        exam = Exam.objects.get(id=exam_id)
        exam.publish(request.user)
        return Response(ExamSerializer(exam).data)


class ReportCardPdfView(APIView):
    permission_classes = [HasPermission]
    required_permission = "view_student_result"

    def get(self, request, student_id, exam_id):
        student = Student.objects.get(id=student_id)
        exam = Exam.objects.get(id=exam_id)
        results = Result.objects.filter(student=student, exam=exam)
        total = results.aggregate(total=Sum("marks"))["total"] or Decimal("0")
        average = results.aggregate(avg=Avg("marks"))["avg"] or Decimal("0")
        rankings = calculate_rankings(
            Result.objects.filter(student__class_room=student.class_room, exam=exam)
        )
        rank = rankings.get(student.id, "N/A")

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(40, 750, settings.TUITION_NAME)
        pdf.setFont("Helvetica", 12)
        pdf.drawString(40, 730, f"Report Card: {exam.name} {exam.term} {exam.year}")
        pdf.drawString(40, 710, f"Student: {student.first_name} {student.last_name}")
        pdf.drawString(40, 690, f"Class: {student.class_room.name}")

        y = 660
        pdf.drawString(40, y, "Subject")
        pdf.drawString(250, y, "Marks")
        pdf.drawString(320, y, "Grade")
        y -= 20
        for result in results:
            pdf.drawString(40, y, result.subject.name)
            pdf.drawString(250, y, str(result.marks))
            pdf.drawString(320, y, result.grade)
            y -= 20
            if y < 120:
                pdf.showPage()
                y = 750

        pdf.drawString(40, y - 20, f"Total: {total}")
        pdf.drawString(40, y - 40, f"Average: {average:.2f}")
        pdf.drawString(40, y - 60, f"Rank: {rank}")

        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="report_card.pdf")


class AnalyticsView(APIView):
    permission_classes = [HasPermission]
    required_permission = "view_analytics"

    def get(self, request, class_id):
        exam_id = request.query_params.get("exam_id")
        if not exam_id:
            return Response({"detail": "exam_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        exam = Exam.objects.get(id=exam_id)
        class_room = ClassRoom.objects.get(id=class_id)
        return Response(analytics_for_class(class_room, exam))
