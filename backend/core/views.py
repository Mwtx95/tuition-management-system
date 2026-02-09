import csv
from decimal import Decimal
from io import BytesIO, StringIO

from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Sum
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
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
from .services import (
    analytics_for_class,
    build_class_result_sheet,
    build_subject_headers,
    calculate_rankings,
    grade_for_marks,
)


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


class ClassResultSheetView(APIView):
    permission_classes = [HasPermission]
    required_permission = "view_class_result"

    def get(self, request, class_id):
        exam_id = request.query_params.get("exam_id")
        if not exam_id:
            return Response({"detail": "exam_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        class_room = get_object_or_404(ClassRoom, id=class_id)
        exam = get_object_or_404(Exam, id=exam_id, class_room=class_room)
        sheet = build_class_result_sheet(class_room, exam, include_marks=True)
        return Response(sheet)


class ClassResultCsvTemplateView(APIView):
    permission_classes = [HasPermission]
    required_permission = "view_class_result"

    def get(self, request, class_id):
        exam_id = request.query_params.get("exam_id")
        if not exam_id:
            return Response({"detail": "exam_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        class_room = get_object_or_404(ClassRoom, id=class_id)
        exam = get_object_or_404(Exam, id=exam_id, class_room=class_room)

        sheet = build_class_result_sheet(class_room, exam, include_marks=False)
        output = StringIO()
        writer = csv.writer(output)
        headers = ["Student ID", "Full Name", "Gender"]
        for subject in sheet["subjects"]:
            headers.append(subject["header"])
            headers.append(f"{subject['header']} Grade")
        headers += ["Total", "Avg", "Avg Grade", "Remarks"]
        writer.writerow(headers)
        for row in sheet["rows"]:
            row_data = [row["student_id"], row["full_name"], row["gender"]]
            for _ in sheet["subjects"]:
                row_data += ["", ""]
            row_data += ["", "", "", ""]
            writer.writerow(row_data)

        filename = f"class_{class_id}_exam_{exam_id}_results_template.csv"
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ClassResultCsvImportView(APIView):
    permission_classes = [HasPermission]
    required_permission = "upload_result"

    def post(self, request, class_id):
        exam_id = request.query_params.get("exam_id") or request.data.get("exam_id")
        if not exam_id:
            return Response({"detail": "exam_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        class_room = get_object_or_404(ClassRoom, id=class_id)
        exam = get_object_or_404(Exam, id=exam_id, class_room=class_room)
        if exam.is_published:
            return Response(
                {"detail": "Cannot edit results after exam is published."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subjects = list(Subject.objects.filter(class_room=class_room).order_by("name"))
        subject_headers = build_subject_headers(subjects)
        subject_by_header = dict(zip(subject_headers, subjects))

        content = upload.read().decode("utf-8-sig")
        reader = csv.DictReader(StringIO(content))
        if not reader.fieldnames:
            return Response({"detail": "CSV header row is required."}, status=status.HTTP_400_BAD_REQUEST)

        student_id_header = None
        for candidate in ("Student ID", "student_id", "student id", "ID"):
            if candidate in reader.fieldnames:
                student_id_header = candidate
                break
        if not student_id_header:
            return Response(
                {"detail": "Missing 'Student ID' column in CSV."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        missing_subject_headers = [
            header for header in subject_headers if header not in reader.fieldnames
        ]
        if missing_subject_headers:
            return Response(
                {"detail": "Missing subject columns in CSV.", "missing": missing_subject_headers},
                status=status.HTTP_400_BAD_REQUEST,
            )

        errors = []
        operations = []
        for index, row in enumerate(reader, start=2):
            raw_student_id = (row.get(student_id_header) or "").strip()
            if not raw_student_id:
                errors.append({"row": index, "error": "Student ID is required."})
                continue
            try:
                student_id = int(raw_student_id)
            except ValueError:
                errors.append({"row": index, "error": f"Invalid Student ID '{raw_student_id}'."})
                continue
            student = Student.objects.filter(id=student_id, class_room=class_room).first()
            if not student:
                errors.append({"row": index, "error": f"Student ID {student_id} not found in class."})
                continue

            for header, subject in subject_by_header.items():
                raw_marks = (row.get(header) or "").strip()
                if raw_marks == "":
                    continue
                try:
                    marks = Decimal(raw_marks)
                except Exception:
                    errors.append({"row": index, "error": f"Invalid marks '{raw_marks}' for {header}."})
                    continue
                if marks < 0 or marks > 100:
                    errors.append({"row": index, "error": f"Marks out of range for {header}."})
                    continue
                operations.append((student, subject, marks))

        if errors:
            return Response({"detail": "Validation errors in CSV.", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        created = 0
        updated = 0
        with transaction.atomic():
            for student, subject, marks in operations:
                result, was_created = Result.objects.update_or_create(
                    student=student,
                    subject=subject,
                    exam=exam,
                    defaults={
                        "marks": marks,
                        "grade": grade_for_marks(marks),
                        "uploaded_by": request.user,
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        return Response({"created": created, "updated": updated, "total": created + updated})


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
            pdf.drawString(320, y, grade_for_marks(result.marks))
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
