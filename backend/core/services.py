from collections import defaultdict
from decimal import Decimal

from django.db.models import Avg, Sum

from .models import Result, Student, Subject


def grade_for_marks(marks):
    score = Decimal(marks)
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "F"


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
    for result in results:
        grade_distribution[result.grade] += 1
    pass_count = results.exclude(grade="F").count()
    fail_count = results.filter(grade="F").count()
    return {
        "class_average": class_average,
        "subject_averages": list(subject_averages),
        "top_students": top_students,
        "pass_fail_rate": {"pass": pass_count, "fail": fail_count},
        "grade_distribution": grade_distribution,
    }
