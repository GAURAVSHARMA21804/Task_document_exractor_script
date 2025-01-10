import os
from django.apps import apps
from pdf_extractor.models import Paragraph, Student , PDFImage , ExtractedTable
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
    # Removing unwanted numbers or page references that are in the middle of the text
    # This removes any numbers followed by a newline or space, like ' 1', ' 2', etc.
    cleaned_text = re.sub(r'\s*\d+\s*$', '', paragraph_content.strip())  # Removing digits at the end (page numbers)
    cleaned_text = re.sub(r'\s*\d+\s*', ' ', cleaned_text)  # Removing any number in the middle of the text
    return cleaned_text

def extract_data_from_pdf(pdf_file_name):
    
    
    app_config = apps.get_app_config('pdf_extractor')  
    pdfs_folder_path = os.path.join(app_config.path, "pdfs")
    
    
    pdf_path = os.path.join(pdfs_folder_path, pdf_file_name)

    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    

# Opening PDF and extract full text
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
        
    # # Processing student data
    # tables = camelot.read_pdf(pdf_path, pages='2')  

    # if tables.n == 0:
    #     raise ValueError("No tables found on the specified page.")

    
    # df = tables[0].df

    # print("Raw Extracted Data:")
    # print(df)

   
    # # Cleaning the data
    # def clean_row(row):
    #     try:
    #         # Split columns properly and remove unwanted newline characters
    #         student_id = row[0].strip() if row[0].strip().isdigit() else None
    #         name_parts = re.sub(r'\n', ' ', row[1]).split()  
    #         name = " ".join(name_parts).strip()
    #         age = row[2].strip() if row[2].isdigit() else None
    #         grade = row[3].strip() if row[3].strip() else None
    #         email = re.sub(r'\s+', '', row[4]).strip()
    #         city = re.sub(r'\n', '', row[5]).strip()

            
    #         if not student_id or not name or not age or not email or not city:
    #             return None

    #         return {
    #             "student_id": student_id,
    #             "name": name,
    #             "age": age,
    #             "grade": grade,
    #             "email": email,
    #             "city": city
    #         }
    #     except Exception as e:
    #         print(f"Error cleaning row: {e}")
    #         return None

    
    # cleaned_data = []
    # for index, row in df.iterrows():
    #     if index == 0:  
    #         continue
    #     cleaned_row = clean_row(row)
    #     if cleaned_row:
    #         cleaned_data.append(cleaned_row)

    # # Converting cleaned data into DataFrame
    # cleaned_df = pd.DataFrame(cleaned_data)

    # # Display cleaned data
    # print("Cleaned Data:")
    # print(cleaned_df)
    # raw_data = [
    #         "101\nAlice \n20\nA\nalice.johnson\nNew York",
    #         "102\nBob Smith\n19\nB\nbob.smith@\nLos Angeles"
    #         ]
    

    
    # for entry in raw_data:
    #     lines = entry.split("\n")
    #     try:
    #         student_id = int(lines[0])
    #         name = lines[1].strip()
    #         age = int(lines[2])
    #         grade = lines[3].strip()
    #         email = re.sub(r'\s+', '', ''.join(lines[4:6]))  # Remove spaces/newlines in email
    #         city = lines[-1].strip()

    #         # Saving in database
    #         Student.objects.update_or_create(
    #                     student_id=student_id,
    #                     defaults={
    #                         'name': name,
    #                         'age': age,
    #                         'grade': grade,
    #                         'email': email,
    #                         'city': city
    #                     }
    #                 )
    #         print(f"Saved: {name}")
    #         print("#####################")
    #     except Exception as e:
    #         print(f"Error processing entry: {entry} - {e}")

    
    # for _, row in cleaned_df.iterrows():
    #     try:
    #         Student.objects.update_or_create(
    #             student_id=int(row["student_id"]),
    #             defaults={
    #                 "name": row["name"].strip(),
    #                 "age": int(row["age"]),
    #                 "grade": row["grade"].strip(),
    #                 "email": row["email"].strip(),
    #                 "city": row["city"].strip(),
    #             }
    #         )
    #         print(f"Saved student: {row['name']}")
    #     except Exception as e:
    #         print(f"Error saving student {row['student_id']}: {e}")  
            
      
    
    # Extract tables from the PDF
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')  # Use lattice flavor for PDFs with table borders

    if len(tables) == 0:
        raise ValueError("No tables found in the PDF.")


    def clean_data(df): 
        
        
        column_names = df.iloc[0, 0].split('\n')  # This assumes the first cell contains concatenated headers
        df.columns = column_names
        
        # Removing the first row which contains the merged header
        df = df.drop(0).reset_index(drop=True)
        
        # Cleaning the data by removing newline characters from strings and trimming spaces
        df = df.applymap(lambda x: x.replace('\n', ' ').strip() if isinstance(x, str) else x)
        
        # Droping rows where all values are NaN
        df = df.dropna(how='all')
        
        # Droping any empty columns
        df = df.dropna(axis=1, how='all')
        
        # Convert numeric columns to appropriate types
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        
        # Reset index after cleaning
        df.reset_index(drop=True, inplace=True)
        print(df)

        return df


    # Iterate through each table and store it in the database
    for table_index, table in enumerate(tables):
        # Converting the table into a Pandas DataFrame
        df = table.df

        # Cleaning the DataFrame
        cleaned_df = clean_data(df)

        # Convert the cleaned DataFrame into a list of dictionaries (one dictionary per row)
        table_data = cleaned_df.to_dict(orient='records')

        
        print(table_data)  
        # Store the cleaned data in the database
        ExtractedTable.objects.create(
            table_name=f"Table {table_index + 1}",
            data=table_data  # Store the data as JSON
        )

    print("Data extraction and storage complete.")        
        
    for page_num, page in enumerate(doc, start=1):
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            
            image = Image.open(BytesIO(image_bytes))

            # Saving the image to the database
            try:
                img_io = BytesIO()
                image.save(img_io, format=image_ext.upper())  
                img_io.seek(0)
                
                pdf_image = PDFImage()
                
                pdf_image.image.save(
                    f"page_{page_num}_img_{img_index}.{image_ext}",  
                    ContentFile(img_io.read()),
                    save=False  
                )
                
                pdf_image.image_data = image_bytes
                pdf_image.save()  
                print(f"Saved image from page {page_num}, index {img_index}")
            except Exception as e:
                print(f"Error saving image from page {page_num}, index {img_index}: {e}")

    print("Image extraction completed.")
    doc.close()

    
if __name__ == "__main__":  
    extract_data_from_pdf("Task_Document_for_Python_Developer.pdf")
