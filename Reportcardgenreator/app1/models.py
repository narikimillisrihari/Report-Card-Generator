from django.db import models

# Create your models here
class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True)
    student_class = models.CharField(max_length=20)
    section = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)

class ReportCard(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    pdf_url = models.FileField(upload_to='reportcards/', null=True, blank=True)
    final_comments = models.TextField(blank=True, null=True)

class StudentSubject(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    marks = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2)
    comments = models.TextField(blank=True, null=True)