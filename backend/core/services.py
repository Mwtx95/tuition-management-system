from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Avg, Sum

from .models import Result, ResultPublication, Student, Subject


def grade_for_marks(marks):
    score = Decimal(marks)
    if score >= Decimal("81"):
        return "A"
    if score >= Decimal("61"):
        return "B"
    if score >= Decimal("41"):
        return "C"
    if score >= Decimal("21"):
        return "D"
    return "F"


def remarks_for_grade(grade):
    return {
        "A": "KIPAWA",
        "B": "MICHIPUO",
        "C": "PASS",
        "D": "PASS",
        "F": "FAIL",
    }.get(grade, "")


def _format_decimal(value):
    if value is None:
        return ""
    return str(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def build_subject_headers(subjects):
    headers = []
    used = set()
    for subject in subjects:
        base = (subject.name or subject.code or "").strip() or f"Subject {subject.id}"
        header = base
        if header in used:
            header = f"{base} ({subject.id})"
        headers.append(header)
        used.add(header)
    return headers


def build_class_result_sheet(
    class_room,
    exam,
    include_marks=True,
    include_grades=True,
    include_totals=True,
):
    subjects = list(Subject.objects.filter(class_room=class_room).order_by("name"))
    subject_headers = build_subject_headers(subjects)
    subject_meta = [
        {"id": subject.id, "name": subject.name, "code": subject.code, "header": header}
        for subject, header in zip(subjects, subject_headers)
    ]

    students = list(Student.objects.filter(class_room=class_room).order_by("first_name", "last_name"))
    results = Result.objects.filter(exam=exam, student__class_room=class_room)
    result_map = {(result.student_id, result.subject_id): result for result in results}
    rankings = calculate_rankings(results)

    rows = []
    for student in students:
        total = Decimal("0")
        count = 0
        subject_rows = []
        for subject in subjects:
            result = result_map.get((student.id, subject.id))
            marks = result.marks if result else None
            grade = grade_for_marks(marks) if marks is not None else None
            if marks is not None:
                total += Decimal(marks)
                count += 1
            subject_rows.append(
                {
                    "subject_id": subject.id,
                    "marks": _format_decimal(marks) if include_marks and marks is not None else "",
                    "grade": grade if include_grades and grade is not None else "",
                }
            )
        average = (total / count) if count else None
        average_grade = grade_for_marks(average) if include_grades and average is not None else ""
        remarks = remarks_for_grade(average_grade) if average_grade else ""
        rows.append(
            {
                "student_id": student.id,
                "reg_no": student.reg_no or "",
                "full_name": f"{student.first_name} {student.last_name}",
                "gender": student.gender,
                "subjects": subject_rows,
                "total": _format_decimal(total) if include_totals and count else "",
                "average": _format_decimal(average) if include_totals and average is not None else "",
                "average_grade": average_grade,
                "remarks": remarks,
                "rank": rankings.get(student.id, ""),
            }
        )

    return {
        "subjects": subject_meta,
        "rows": rows,
    }


def calculate_student_totals(results):
    totals = defaultdict(lambda: {"total": Decimal("0"), "subjects": 0})
    for result in results:
        totals[result.student_id]["total"] += result.marks
        totals[result.student_id]["subjects"] += 1
    return totals


def calculate_rankings(results):
    totals = calculate_student_totals(results)
    ranked = sorted(
        totals.items(), key=lambda item: item[1]["total"], reverse=True
    )
    ranks = {}
    current_rank = 1
    for index, (student_id, data) in enumerate(ranked):
        if index > 0 and data["total"] < ranked[index - 1][1]["total"]:
            current_rank = index + 1
        ranks[student_id] = current_rank
    return ranks


def is_result_published(student, exam):
    if exam.is_published:
        return True
    return ResultPublication.objects.filter(student=student, exam=exam).exists()


def analytics_for_class(class_room, exam):
    results = Result.objects.filter(exam=exam, student__class_room=class_room)
    class_average = results.aggregate(average=Avg("marks"))["average"] or 0
    subject_averages = (
        results.values("subject__id", "subject__name")
        .annotate(average=Avg("marks"))
        .order_by("subject__name")
    )
    totals = results.values("student").annotate(total=Sum("marks")).order_by("-total")
    top_students = []
    for entry in totals[:5]:
        student = Student.objects.get(id=entry["student"])
        top_students.append(
            {
                "id": student.id,
                "name": f"{student.first_name} {student.last_name}",
                "total": entry["total"],
            }
        )
    grade_distribution = defaultdict(int)
    pass_count = 0
    fail_count = 0
    for result in results:
        grade = grade_for_marks(result.marks)
        grade_distribution[grade] += 1
        if grade == "F":
            fail_count += 1
        else:
            pass_count += 1
    return {
        "class_average": class_average,
        "subject_averages": list(subject_averages),
        "top_students": top_students,
        "pass_fail_rate": {"pass": pass_count, "fail": fail_count},
        "grade_distribution": grade_distribution,
    }
