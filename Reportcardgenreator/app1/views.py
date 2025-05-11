import datetime
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Student, ReportCard, Subject, StudentSubject
from .serializers import StudentSerializer, ReportCardSerializer
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer


# Util function to generate PDF from HTML
def generate_pdf_from_html(template_src, context_dict):
    html = render_to_string(template_src, context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reportcard.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response


# API to create a new student
class StudentCreateView(APIView):
    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            student = serializer.save()
            return Response({"status": "success", "student_id": student.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# API to get latest report card or generate one
class ReportCardDetailView(APIView):
    def get(self, request, student_id):
        try:
            report = ReportCard.objects.filter(student__id=student_id).latest('generated_at')
            serializer = ReportCardSerializer(report)
            return Response(serializer.data)
        except ReportCard.DoesNotExist:
            return Response({"error": "Report card not found."}, status=404)

    def post(self, request, student_id):
        # Get the student from the URL
        student = get_object_or_404(Student, id=student_id)

        subjects_data = request.data.get("subjects", [])
        if not subjects_data:
            return Response({"error": "No subject data provided."}, status=status.HTTP_400_BAD_REQUEST)

        final_comments = request.data.get("final_comments", "")
        subject_data = []

        for subject in subjects_data:
            name = subject.get("name")
            marks = subject.get("marks")

            if not name or marks is None:
                return Response({"error": "Each subject must have a name and marks."}, status=status.HTTP_400_BAD_REQUEST)

            subject_obj, _ = Subject.objects.get_or_create(name=name)

            StudentSubject.objects.update_or_create(
                student=student,
                subject=subject_obj,
                defaults={
                    'marks': marks,
                    'grade': '',         # Fill this if grading logic is added
                    'comments': ''
                }
            )

            subject_data.append({
                'subject_name': subject_obj.name,
                'subject_code': subject_obj.code,
                'marks': marks
            })

        ReportCard.objects.create(
            student=student,
            final_comments=final_comments,
            generated_at=datetime.datetime.now()
        )

        return Response({
            "message": "Report card data saved successfully.",
            "student": {
                "id": student.id,
                "name": student.name,
                "roll_number": student.roll_number,
                "class": student.student_class,
                "section": student.section
            },
            "subjects": subject_data,
            "final_comments": final_comments
        }, status=status.HTTP_201_CREATED)

class GenerateReportCardView(APIView):
    def post(self, request):
        student_id = request.data.get("student_id")
        final_comments = request.data.get("final_comments", "")

        if not student_id:
            return Response({"error": "Student ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get the student
        student = get_object_or_404(Student, id=student_id)

        # Get all related subjects and marks from StudentSubject
        student_subjects = StudentSubject.objects.filter(student=student)

        if not student_subjects.exists():
            return Response({"error": "No subject data found for this student"}, status=status.HTTP_404_NOT_FOUND)

        # Prepare subject data
        subject_instances = []
        for ss in student_subjects:
            subject_instances.append({
                "subject_name": ss.subject.name,
                "subject_code": ss.subject.code,
                "marks": ss.marks
            })

        # Create a new ReportCard record
        ReportCard.objects.create(
            student=student,
            final_comments=final_comments
        )

        # Context for PDF
        context = {
            "student": student,
            "subjects": subject_instances,
            "final_comments": final_comments
        }

        # Generate and return the PDF
        return generate_pdf_from_html("report_card_template.html", context)