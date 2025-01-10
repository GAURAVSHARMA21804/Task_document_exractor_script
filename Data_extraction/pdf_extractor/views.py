from django.shortcuts import render
from .models import Paragraph, Student, PDFImage,ExtractedTable

# View to display paragraphs and student data and image data
def display_data(request):
    
    paragraphs = Paragraph.objects.all()

    students = Student.objects.all()
    table_data =ExtractedTable.objects.all()
    
    context = {
        'paragraphs': paragraphs,
        'students': students,
        'images': PDFImage.objects.all(),
        'table_data':table_data
    }
    return render(request, 'pdf_extractor/display_data.html', context)

