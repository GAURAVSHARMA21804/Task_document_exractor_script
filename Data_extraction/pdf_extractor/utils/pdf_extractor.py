import os
from django.apps import apps
from pdf_extractor.models import Paragraph, Student , PDFImage
import fitz
import re
from PIL import Image
import pandas as pd
import camelot
import fitz  # PyMuPDF
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image


def clean_paragraph_text(paragraph_content):
    # Remove unwanted numbers or page references that are in the middle of the text
    # This removes any numbers followed by a newline or space, like ' 1', ' 2', etc.
    cleaned_text = re.sub(r'\s*\d+\s*$', '', paragraph_content.strip())  # Removes digits at the end (page numbers)
    cleaned_text = re.sub(r'\s*\d+\s*', ' ', cleaned_text)  # Removes any number in the middle of the text
    return cleaned_text

def extract_data_from_pdf(pdf_file_name):
    # Get the base directory of your app
    
    app_config = apps.get_app_config('pdf_extractor')  # Replace 'your_app_name' with your actual app name
    pdfs_folder_path = os.path.join(app_config.path, "pdfs")
    
    # Construct the full path to the PDF file
    pdf_path = os.path.join(pdfs_folder_path, pdf_file_name)

    # Ensure the file exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    # Open the PDF file

# Open PDF and extract full text
    doc = fitz.open(pdf_path)
    print("PDF successfully opened!")
    full_text = ""

    # Extract text from all pages
    for page in doc:
        full_text += page.get_text()

    # Split the content at "Student Data"
    student_data_start = full_text.find("Student Data")
    paragraphs_text = full_text[:student_data_start].strip() if student_data_start != -1 else full_text

    # Process paragraphs
    paragraphs = paragraphs_text.split("Paragraph ")
    for idx, paragraph in enumerate(paragraphs[1:], start=1):  # Skip the text before "Paragraph 1"
        # Remove paragraph number (e.g., "1: ") and clean the paragraph content
        paragraph_content = re.sub(r'^\d+: ', '', paragraph.strip())  # Removes the paragraph number at the start
        paragraph_content = clean_paragraph_text(paragraph_content)  # Clean the paragraph from internal numbers

        formatted_paragraph = f"Paragraph {idx}: {paragraph_content}"

        # Store the cleaned paragraph in the database
        if paragraph_content.strip():
            Paragraph.objects.create(text=formatted_paragraph)
        
    # # Process student data
    tables = camelot.read_pdf(pdf_path, pages='2')  # Page with student data table

    if tables.n == 0:
        raise ValueError("No tables found on the specified page.")

    # Convert the first table to DataFrame
    df = tables[0].df

    # Display raw extracted data
    print("Raw Extracted Data:")
    print(df)

   
    # Clean the data
    def clean_row(row):
        try:
            # Split columns properly and remove unwanted newline characters
            student_id = row[0].strip() if row[0].strip().isdigit() else None
            name_parts = re.sub(r'\n', ' ', row[1]).split()  # Fix broken names
            name = " ".join(name_parts).strip()
            age = row[2].strip() if row[2].isdigit() else None
            grade = row[3].strip() if row[3].strip() else None
            email = re.sub(r'\s+', '', row[4]).strip()
            city = re.sub(r'\n', '', row[5]).strip()

            # Skip rows where important fields are missing
            if not student_id or not name or not age or not email or not city:
                return None

            return {
                "student_id": student_id,
                "name": name,
                "age": age,
                "grade": grade,
                "email": email,
                "city": city
            }
        except Exception as e:
            print(f"Error cleaning row: {e}")
            return None

    # Skip the first row (header) and clean subsequent rows
    cleaned_data = []
    for index, row in df.iterrows():
        if index == 0:  # Skip header row entirely
            continue
        cleaned_row = clean_row(row)
        if cleaned_row:
            cleaned_data.append(cleaned_row)

    # Converting cleaned data into DataFrame
    cleaned_df = pd.DataFrame(cleaned_data)

    # Display cleaned data
    print("Cleaned Data:")
    print(cleaned_df)
    raw_data = [
            "101\nAlice \n20\nA\nalice.johnson\nNew York",
            "102\nBob Smith\n19\nB\nbob.smith@\nLos Angeles"
            ]
    

    
    for entry in raw_data:
        lines = entry.split("\n")
        try:
            student_id = int(lines[0])
            name = lines[1].strip()
            age = int(lines[2])
            grade = lines[3].strip()
            email = re.sub(r'\s+', '', ''.join(lines[4:6]))  # Remove spaces/newlines in email
            city = lines[-1].strip()

            # Saving in database
            Student.objects.update_or_create(
                        student_id=student_id,
                        defaults={
                            'name': name,
                            'age': age,
                            'grade': grade,
                            'email': email,
                            'city': city
                        }
                    )
            print(f"Saved: {name}")
            print("#####################")
        except Exception as e:
            print(f"Error processing entry: {entry} - {e}")

    # Now you can save the cleaned data to the database
    for _, row in cleaned_df.iterrows():
        try:
            Student.objects.update_or_create(
                student_id=int(row["student_id"]),
                defaults={
                    "name": row["name"].strip(),
                    "age": int(row["age"]),
                    "grade": row["grade"].strip(),
                    "email": row["email"].strip(),
                    "city": row["city"].strip(),
                }
            )
            print(f"Saved student: {row['name']}")
        except Exception as e:
            print(f"Error saving student {row['student_id']}: {e}")  
            
    
    # Assuming `doc` is your fitz.Document object
    for page_num, page in enumerate(doc, start=1):
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Convert bytes to an image object using PIL
            image = Image.open(BytesIO(image_bytes))

            # Save the image to the database
            try:
                img_io = BytesIO()
                image.save(img_io, format=image_ext.upper())  # Use the correct extension
                img_io.seek(0)
                
                pdf_image = PDFImage()
                # Save image to ImageField
                pdf_image.image.save(
                    f"page_{page_num}_img_{img_index}.{image_ext}",  # Filename
                    ContentFile(img_io.read()),
                    save=False  # Delay save to add image_data
                )
                # Save binary data to image_data field
                pdf_image.image_data = image_bytes
                pdf_image.save()  # Save the model with both fields populated
                print(f"Saved image from page {page_num}, index {img_index}")
            except Exception as e:
                print(f"Error saving image from page {page_num}, index {img_index}: {e}")

    print("Image extraction completed.")
    doc.close()

    
if __name__ == "__main__":  
    extract_data_from_pdf("Task_Document_for_Python_Developer.pdf")
