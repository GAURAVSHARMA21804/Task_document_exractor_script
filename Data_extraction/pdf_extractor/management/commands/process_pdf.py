from django.core.management.base import BaseCommand
from pdf_extractor.utils.pdf_extractor import extract_data_from_pdf  # Assuming the function to extract data is named extract_data_from_pdf

class Command(BaseCommand):
    help = 'Process a PDF and extract paragraphs'

    def add_arguments(self, parser):
        # Add a positional argument for the PDF file path
        parser.add_argument('pdf_name', type=str, help='The name of the PDF file to process')

    def handle(self, *args, **kwargs):
        pdf_name = kwargs['pdf_name']
        # Call the function to process the PDF
        extract_data_from_pdf(pdf_name)
        self.stdout.write(self.style.SUCCESS(f'Successfully processed PDF: {pdf_name}'))
