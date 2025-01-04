from django.shortcuts import render
from .models import Paragraph, Student, PDFImage

# View to display paragraphs and student data
def display_data(request):
    # Fetch all paragraphs from the database
    paragraphs = Paragraph.objects.all()

    # Fetch all students from the database
    students = Student.objects.all()
    
    image = PDFImage.objects.all()
    # Pass both data sets to the template
    image = PDFImage.objects.all()

# Print out the URL of each image (for debugging)
    for img in image:
       print(img.image.url)
    context = {
        'paragraphs': paragraphs,
        'students': students,
        'images': PDFImage.objects.all(),
    }
    return render(request, 'pdf_extractor/display_data.html', context)

