import pymupdf
import os
import uuid

from datetime import datetime

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings


def gen_temp_file_path(prefix, extension):
    """
    Generate a temporary file path with the given prefix and extension
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"temp/{prefix}_{timestamp}_{unique_id}.{extension}"


def cleanup_temp_file(filepath):
    """Delete a temporary file if it exists"""
    try:
        if default_storage.exists(filepath):
            default_storage.delete(filepath)
    except Exception as e:
        print(f"Error cleaning up temporary_file {filepath}: {str(e)}")


def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file"""
    try:
        doc = pymupdf.open(stream=pdf_file.read(), filetype="pdf")
        text_content = {}

        for page_num in range(len(doc)):
            page = doc[page_num]
            text_content[f"page_{page_num + 1}"] = page.get_text()

        doc.close()
        return {
            "status": "success",
            "pages": len(text_content),
            "content": text_content,
        }
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def extract_images_from_pdf(pdf_file):
    """Extract images from a PDF file"""
    try:
        doc = pymupdf.open(stream=pdf_file.read(), filetype="pdf")
        images = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)

                if base_image:
                    filename = (
                        f"images/page{page_num + 1}_img{img_index + 1}_"
                        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
                        f"{str(uuid.uuid4())[:8]}.{base_image['ext']}"
                    )

                    saved_path = default_storage.save(
                        filename, ContentFile(base_image["image"]))

                    image_url = f"{settings.MEDIA_URL}{saved_path}".lstrip("/")

                    image_data = {
                        "page": page_num + 1,
                        "index": img_index + 1,
                        "width": base_image["width"],
                        "height": base_image["height"],
                        "format": base_image["ext"],
                        "url": image_url,
                    }
                    images.append(image_data)

        doc.close()
        print("MEDIA_ROOT:", settings.MEDIA_ROOT)
        print("Storage exists:", default_storage.exists(saved_path))
        return {
            "status": "success",
            "total_images": len(images),
            "images": images,
        }
    except Exception as e:
        raise Exception(f"Error extracting images: {str(e)}")


def merge_pdfs(pdf_files):
    """Merge multiple PDF files into a single PDF file"""
    try:
        if not pdf_files:
            raise ValueError("No PDF files provided for merging.")

        # Save the first uploaded PDF to a temporary file
        first_pdf = pdf_files[0]
        first_pdf_path = default_storage.save(
            gen_temp_file_path(first_pdf.name, "pdf"), first_pdf
        )
        merged_pdf = pymupdf.open(default_storage.path(first_pdf_path))

        # Process remaining PDFs
        for pdf_file in pdf_files[1:]:
            temp_pdf_path = default_storage.save(
                gen_temp_file_path(pdf_file.name, "pdf"), pdf_file
            )
            new_pdf = pymupdf.open(default_storage.path(temp_pdf_path))
            merged_pdf.insert_pdf(new_pdf)

        # ✅ Save the merged PDF in `MEDIA_ROOT`
        output_filename = (
            f"merged_pdf_{datetime.now().strftime('%y%m%d_%h%m%s')}.pdf"
        )
        output_file_path = os.path.join(settings.MEDIA_ROOT, output_filename)

        print(f"DEBUG: Saving merged PDF to {
              output_file_path}")  # Log file path

        merged_pdf.save(output_file_path)
        merged_pdf.close()

        # ✅ Return the correct media URL
        media_url = f"{settings.MEDIA_URL}{output_filename}"
        return media_url  # ✅ Now returning the correct URL

    except Exception as e:
        raise Exception(f"Error merging PDFs: {str(e)}")
