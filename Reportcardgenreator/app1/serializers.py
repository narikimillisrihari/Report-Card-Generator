from rest_framework import serializers
from .models import Student, Subject, ReportCard, StudentSubject

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class StudentSubjectSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer()

    class Meta:
        model = StudentSubject
        fields = ['subject', 'marks', 'grade', 'comments']

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class ReportCardSerializer(serializers.ModelSerializer):
    student = StudentSerializer()
    subjects = serializers.SerializerMethodField()

    class Meta:
        model = ReportCard
        fields = ['student', 'generated_at', 'pdf_url', 'final_comments', 'subjects']

    def get_subjects(self, obj):
        subjects = StudentSubject.objects.filter(student=obj.student)
        return StudentSubjectSerializer(subjects, many=True).data