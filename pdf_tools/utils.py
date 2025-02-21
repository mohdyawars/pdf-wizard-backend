import base64
import pymupdf
import uuid

from datetime import datetime

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


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
                    # Generate filename
                    filename = f"page{page_num + 1}_img{img_index + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}.{base_image['ext']}"
                    # Full path within media directory
                    file_path = f"pdf_images/{filename}"

                    # Save the image
                    default_storage.save(file_path, ContentFile(base_image["image"]))

                    image_data = {
                        "page": page_num + 1,
                        "index": img_index + 1,
                        "width": base_image["width"],
                        "height": base_image["height"],
                        "format": base_image["ext"],
                        "url": f"/media/{file_path}",
                    }
                    images.append(image_data)

        doc.close()
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

        # Save the first uploaded PDF to a temporary file and open it
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

        # Generate the final merged PDF file
        output_file = gen_temp_file_path("merged_pdf", "pdf")
        merged_pdf.save(default_storage.path(output_file))
        merged_pdf.close()

        return output_file

    except Exception as e:
        raise Exception(f"Error merging PDFs: {str(e)}")
