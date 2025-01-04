from django.db import models

# Create your models here.
from django.db import models

class Paragraph(models.Model):
    text = models.TextField()

    def __str__(self):
        return f"Paragraph {self.id}"


class Student(models.Model):
    student_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    grade = models.CharField(max_length=2)
    email = models.EmailField(unique=True)
    city = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class PDFImage(models.Model):
    image = models.ImageField(upload_to='pdf_images/')
    image_data = models.BinaryField(null=True, blank=True)

    def __str__(self):
        return f"Image for {self.id}"

