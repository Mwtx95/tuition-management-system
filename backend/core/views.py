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
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ClassRoom, Exam, Result, ResultPublication, Student, Subject
from .permissions import HasPermission, get_user_permission_codes
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
    calculate_rankings,
    grade_for_marks,
    is_result_published,
    remarks_for_grade,
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
    search_fields = ["first_name", "last_name", "reg_no"]

    def get_queryset(self):
        queryset = super().get_queryset()
        class_room = self.request.query_params.get("class_room")
        if class_room:
            queryset = queryset.filter(class_room_id=class_room)
        reg_no = self.request.query_params.get("reg_no")
        if reg_no:
            queryset = queryset.filter(reg_no=reg_no)
        return queryset


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    required_permission = "crud_subject"
    permission_classes = [HasPermission]
    search_fields = ["name", "code"]

    def get_queryset(self):
        queryset = super().get_queryset()
        class_room = self.request.query_params.get("class_room")
        if class_room:
            queryset = queryset.filter(class_room_id=class_room)
        teacher = self.request.query_params.get("teacher")
        if teacher:
            queryset = queryset.filter(teacher_id=teacher)
        return queryset


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
        created_count = 0
        updated_count = 0
        for item in serializer.validated_data["results"]:
            exam = Exam.objects.get(id=item["exam"])
            student = Student.objects.get(id=item["student"])
            subject = Subject.objects.get(id=item["subject"])
            if student.class_room_id != exam.class_room_id or subject.class_room_id != exam.class_room_id:
                return Response(
                    {"detail": "Student, subject, and exam must belong to the same class."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if is_result_published(student, exam):
                return Response(
                    {"detail": "Cannot edit results after exam is published."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            result, was_created = Result.objects.update_or_create(
                student=student,
                subject=subject,
                exam=exam,
                defaults={
                    "marks": item["marks"],
                    "grade": grade_for_marks(item["marks"]),
                    "uploaded_by": request.user,
                },
            )
            if was_created:
                created_count += 1
            else:
                updated_count += 1
            created.append(ResultSerializer(result).data)
        return Response(
            {
                "results": created,
                "created": created_count,
                "updated": updated_count,
                "total": created_count + updated_count,
            },
            status=status.HTTP_201_CREATED,
        )


class StudentResultView(APIView):
    permission_classes = [HasPermission]
    required_permission = "view_student_result"

    def get(self, request, student_id):
        exam_id = request.query_params.get("exam_id")
        student = get_object_or_404(Student, id=student_id)
        permissions = get_user_permission_codes(request.user)
        is_privileged = request.user.is_superuser or any(
            code in permissions
            for code in ("publish_result", "manage_users", "view_class_result", "upload_result")
        )

        if not is_privileged and student.parent_id != request.user.id:
            return Response({"detail": "Not allowed to view this student."}, status=status.HTTP_403_FORBIDDEN)

        if not exam_id and not is_privileged:
            return Response({"detail": "exam_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        results = Result.objects.filter(student=student)
        if exam_id:
            exam = get_object_or_404(Exam, id=exam_id)
            if not is_privileged and not is_result_published(student, exam):
                return Response({"detail": "Results not published."}, status=status.HTTP_403_FORBIDDEN)
            results = results.filter(exam=exam)

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
        sheet = build_class_result_sheet(
            class_room,
            exam,
            include_marks=True,
            include_grades=True,
            include_totals=True,
        )
        return Response(sheet)


class PublicClassResultSheetView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, class_id):
        exam_id = request.query_params.get("exam_id")
        if not exam_id:
            return Response({"detail": "exam_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        class_room = get_object_or_404(ClassRoom, id=class_id)
        exam = get_object_or_404(Exam, id=exam_id, class_room=class_room)
        if not exam.is_published:
            return Response({"detail": "Results not published."}, status=status.HTTP_403_FORBIDDEN)
        sheet = build_class_result_sheet(
            class_room,
            exam,
            include_marks=False,
            include_grades=True,
            include_totals=False,
        )
        return Response(sheet)


class SubjectResultSheetView(APIView):
    permission_classes = [HasPermission]
    required_permission = "upload_result"

    def _ensure_subject_access(self, request, subject):
        if subject.teacher_id and subject.teacher_id != request.user.id:
            permissions = get_user_permission_codes(request.user)
            if not (
                request.user.is_superuser
                or "publish_result" in permissions
                or "manage_users" in permissions
            ):
                return False
        return True

    def get(self, request, subject_id):
        exam_id = request.query_params.get("exam_id")
        if not exam_id:
            return Response({"detail": "exam_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        subject = get_object_or_404(Subject, id=subject_id)
        if not self._ensure_subject_access(request, subject):
            return Response({"detail": "Not allowed to access this subject."}, status=status.HTTP_403_FORBIDDEN)
        exam = get_object_or_404(Exam, id=exam_id, class_room=subject.class_room)

        students = Student.objects.filter(class_room=subject.class_room).order_by(
            "first_name", "last_name"
        )
        results = Result.objects.filter(exam=exam, subject=subject)
        result_map = {result.student_id: result for result in results}
        rows = []
        for student in students:
            result = result_map.get(student.id)
            rows.append(
                {
                    "student_id": student.id,
                    "reg_no": student.reg_no or "",
                    "full_name": f"{student.first_name} {student.last_name}".strip(),
                    "gender": student.gender,
                    "marks": str(result.marks) if result else "",
                }
            )

        return Response(
            {
                "subject": {
                    "id": subject.id,
                    "name": subject.name,
                    "code": subject.code,
                    "class_room": subject.class_room_id,
                },
                "exam": {"id": exam.id, "name": exam.name, "term": exam.term, "year": exam.year},
                "rows": rows,
            }
        )

    def post(self, request, subject_id):
        exam_id = request.query_params.get("exam_id") or request.data.get("exam_id")
        if not exam_id:
            return Response({"detail": "exam_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        subject = get_object_or_404(Subject, id=subject_id)
        if not self._ensure_subject_access(request, subject):
            return Response({"detail": "Not allowed to access this subject."}, status=status.HTTP_403_FORBIDDEN)
        exam = get_object_or_404(Exam, id=exam_id, class_room=subject.class_room)
        if exam.is_published:
            return Response(
                {"detail": "Cannot edit results after exam is published."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rows = request.data.get("rows", [])
        if not isinstance(rows, list):
            return Response({"detail": "Rows must be a list."}, status=status.HTTP_400_BAD_REQUEST)

        errors = []
        operations = []
        for index, row in enumerate(rows, start=1):
            student = None
            student_id = row.get("student_id")
            reg_no = (row.get("reg_no") or "").strip()
            if student_id:
                student = Student.objects.filter(id=student_id, class_room=subject.class_room).first()
            elif reg_no:
                student = Student.objects.filter(reg_no=reg_no, class_room=subject.class_room).first()
            if not student:
                errors.append({"row": index, "error": "Student not found in class."})
                continue

            if is_result_published(student, exam):
                errors.append({"row": index, "error": "Results already published for this student."})
                continue

            raw_marks = str(row.get("marks", "")).strip()
            if raw_marks == "":
                continue
            try:
                marks = Decimal(raw_marks)
            except Exception:
                errors.append({"row": index, "error": f"Invalid marks '{raw_marks}'."})
                continue
            if marks < 0 or marks > 100:
                errors.append({"row": index, "error": "Marks out of range."})
                continue
            operations.append((student, marks))

        if errors:
            return Response({"detail": "Validation errors.", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        created = 0
        updated = 0
        with transaction.atomic():
            for student, marks in operations:
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


class ClassResultCsvTemplateView(APIView):
    permission_classes = [HasPermission]
    required_permission = "view_class_result"

    def get(self, request, class_id):
        exam_id = request.query_params.get("exam_id")
        if not exam_id:
            return Response({"detail": "exam_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        class_room = get_object_or_404(ClassRoom, id=class_id)
        exam = get_object_or_404(Exam, id=exam_id, class_room=class_room)

        sheet = build_class_result_sheet(
            class_room,
            exam,
            include_marks=False,
            include_grades=False,
            include_totals=False,
        )
        output = StringIO()
        writer = csv.writer(output)
        headers = ["Reg no", "Name", "Gender"]
        for subject in sheet["subjects"]:
            mark_header = subject["header"]
            grade_header = (subject["code"] or subject["name"] or mark_header).upper()
            headers.append(mark_header)
            headers.append(grade_header)
        headers += ["Total", "av", "Remarks"]
        writer.writerow(headers)
        for row in sheet["rows"]:
            row_data = [row["reg_no"], row["full_name"], row["gender"]]
            for _ in sheet["subjects"]:
                row_data += ["", ""]
            row_data += ["", "", ""]
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

        content = upload.read().decode("utf-8-sig")
        reader = csv.DictReader(StringIO(content))
        if not reader.fieldnames:
            return Response({"detail": "CSV header row is required."}, status=status.HTTP_400_BAD_REQUEST)

        def normalize(value):
            return "".join(str(value).strip().lower().split())

        normalized_headers = {}
        for header in reader.fieldnames:
            key = normalize(header)
            normalized_headers.setdefault(key, []).append(header)

        def find_header(candidates):
            for candidate in candidates:
                key = normalize(candidate)
                if key in normalized_headers:
                    return normalized_headers[key][0]
            return None

        reg_no_header = find_header(["Reg no", "Reg No", "RegNo", "Registration No", "Reg #"])
        student_id_header = find_header(["Student ID", "student_id", "student id", "ID"])
        if not reg_no_header and not student_id_header:
            return Response(
                {"detail": "Missing 'Reg no' or 'Student ID' column in CSV."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subject_marks_map = {}
        missing_subjects = []
        for subject in subjects:
            name_key = normalize(subject.name)
            code_key = normalize(subject.code or "")
            mark_header = None
            if name_key in normalized_headers:
                mark_header = normalized_headers[name_key][0]
            elif code_key in normalized_headers:
                mark_header = normalized_headers[code_key][0]
            if not mark_header:
                missing_subjects.append(subject.name)
            else:
                subject_marks_map[mark_header] = subject

        if missing_subjects:
            return Response(
                {"detail": "Missing subject columns in CSV.", "missing": missing_subjects},
                status=status.HTTP_400_BAD_REQUEST,
            )

        errors = []
        operations = []
        for index, row in enumerate(reader, start=2):
            student = None
            if reg_no_header:
                reg_no = (row.get(reg_no_header) or "").strip()
                if reg_no:
                    student = Student.objects.filter(reg_no=reg_no, class_room=class_room).first()
                    if not student:
                        errors.append({"row": index, "error": f"Reg no '{reg_no}' not found in class."})
                        continue
            if not student and student_id_header:
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

            if not student:
                errors.append({"row": index, "error": "Student identifier is required."})
                continue

            if is_result_published(student, exam):
                errors.append({"row": index, "error": "Results already published for this student."})
                continue

            for header, subject in subject_marks_map.items():
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


class PublishStudentResultView(APIView):
    permission_classes = [HasPermission]
    required_permission = "publish_result"

    def post(self, request, exam_id, student_id):
        exam = get_object_or_404(Exam, id=exam_id)
        student = get_object_or_404(Student, id=student_id, class_room=exam.class_room)
        publication, _ = ResultPublication.objects.get_or_create(student=student, exam=exam)
        publication.publish(request.user)
        return Response(
            {
                "student_id": student.id,
                "exam_id": exam.id,
                "published_by": publication.published_by_id,
                "published_at": publication.published_at,
            }
        )


class ReportCardPdfView(APIView):
    permission_classes = [HasPermission]
    required_permission = "view_student_result"

    def get(self, request, student_id, exam_id):
        student = Student.objects.get(id=student_id)
        exam = Exam.objects.get(id=exam_id)
        permissions = get_user_permission_codes(request.user)
        is_privileged = request.user.is_superuser or any(
            code in permissions
            for code in ("publish_result", "manage_users", "view_class_result", "upload_result")
        )
        if not is_privileged and student.parent_id != request.user.id:
            return Response({"detail": "Not allowed to view this student."}, status=status.HTTP_403_FORBIDDEN)
        if not is_privileged and not is_result_published(student, exam):
            return Response({"detail": "Results not published."}, status=status.HTTP_403_FORBIDDEN)
        results = Result.objects.filter(student=student, exam=exam)
        total = results.aggregate(total=Sum("marks"))["total"] or Decimal("0")
        average = results.aggregate(avg=Avg("marks"))["avg"] or Decimal("0")
        average_grade = grade_for_marks(average) if results.exists() else ""
        remarks = remarks_for_grade(average_grade) if average_grade else ""
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
        pdf.drawString(40, y - 60, f"Avg Grade: {average_grade}")
        pdf.drawString(40, y - 80, f"Remarks: {remarks}")
        pdf.drawString(40, y - 100, f"Rank: {rank}")

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
