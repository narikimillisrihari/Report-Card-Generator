from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Student, ReportCard, Subject, StudentSubject
from .serializers import StudentSerializer, ReportCardSerializer
from django.template.loader import render_to_string
from xhtml2pdf import pisa


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

    def post(self, request):
        student_id = request.data.get('student_id')
        if not student_id:
            return Response({'error': 'Student ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get subjects and marks from StudentSubject
        student_subjects = StudentSubject.objects.filter(student=student)
        subject_data = []
        for ss in student_subjects:
            subject_data.append({
                'subject_name': ss.subject.name,
                'subject_code': ss.subject.code,
                'marks': ss.marks,
            })

        # Prepare context
        context = {
            'student': student,
            'subjects': subject_data,
        }

        return generate_pdf_from_html('report_card_template.html', context)


# Optional: Separate endpoint just to generate report card PDF
class GenerateReportCardView(APIView):
    def post(self, request):
        student_id = request.data.get("student_id")
        subjects_data = request.data.get("subjects", [])
        final_comments = request.data.get("final_comments", "")

        student = get_object_or_404(Student, id=student_id)

        # Create Subject and StudentSubject records
        subject_instances = []
        for subject in subjects_data:
            subject_obj, _ = Subject.objects.get_or_create(
                name=subject["name"]
            )
            subject_instances.append({
                'subject_name': subject_obj.name,
                'subject_code': subject_obj.code,
                'marks': subject["marks"],
            })

            # Link student and subject
            StudentSubject.objects.update_or_create(
                student=student,
                subject=subject_obj,
                defaults={'marks': subject["marks"]}
            )

        # Create ReportCard object
        report_card = ReportCard.objects.create(
            student=student,
            final_comments=final_comments
        )

        # Render PDF
        context = {
            "student": student,
            "subjects": subject_instances,
            "final_comments": final_comments,
        }

        return generate_pdf_from_html("report_card_template.html", context)