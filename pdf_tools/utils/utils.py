import fitz
import pymupdf
import os
import uuid
import ghostscript

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


def split_pdf_to_pages(pdf_file, output_subdir='output_pages', start_page=1, end_page=None):
    """Split a PDF file into multiple pages"""
    try:
        # This is the actual directory where files will be saved
        output_dir = os.path.join(settings.MEDIA_ROOT, output_subdir)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        doc = pymupdf.open(stream=pdf_file.read(), filetype="pdf")
        if end_page is None:
            end_page = doc.page_count

        pages = []
        for page_num in range(start_page - 1, end_page):
            single_page = pymupdf.open()
            single_page.insert_pdf(doc, from_page=page_num, to_page=page_num)
            unique_id = str(uuid.uuid4())[:8]

            filename = f"page_{page_num + 1}_{unique_id}.pdf"
            output_path = os.path.join(output_dir, filename)
            print(f"DEBUG: Saving page {page_num + 1} to {output_path}")
            single_page.save(output_path)
            single_page.close()

            # Relative path for URL
            relative_path = os.path.join(output_subdir, filename)

            page_info = {
                "page_number": page_num + 1,
                "filename": filename,
                "path": output_path,
                "url": f"{settings.MEDIA_URL}{relative_path}",
            }
            pages.append(page_info)

        doc.close()
        return {
            "status": "success",
            "total_pages": len(pages),
            "pages": pages,
        }
    except Exception as e:
        raise Exception(f"Error splitting PDF: {str(e)}")


def compress_pdf(input_path, compression_level):
    """
    Compress a PDF file using Ghostscript.
    
    Args:
        input_path (str): Path to the input PDF file.
        compression_level (str): Compression level ('low', 'mid', 'high').
    
    Returns:
        str: URL of the compressed PDF file.
    """
    # Define Ghostscript compression settings for each level
    compression_settings = {
        'low': '/screen',
        'mid': '/ebook',
        'high': '/prepress'
    }

    # Get the Ghostscript setting for the specified compression level
    gs_compression = compression_settings.get(compression_level, '/screen')

    # Define the directory and output path for the compressed PDF
    compressed_dir = os.path.join(settings.MEDIA_ROOT, 'compressed_pdfs')
    if not os.path.exists(compressed_dir):
        os.makedirs(compressed_dir)

    output_filename = f"compressed_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()}.pdf"
    output_path = os.path.join(compressed_dir, output_filename)

    # Ghostscript command arguments
    args = [
        "ps2pdf",  # Ghostscript command
        "-sDEVICE=pdfwrite",
        f"-dPDFSETTINGS={gs_compression}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path
    ]

    # Run the Ghostscript command
    try:
        # Convert the arguments to the format expected by Ghostscript
        args = [str(arg).encode('utf-8') for arg in args]
        ghostscript.Ghostscript(*args)
        print(f"PDF compressed successfully: {output_path}")

        print(f"Output Filename: {output_filename}")
        print(f"Output Path: {output_path}")
        print(f"File size: {os.path.getsize(output_path)} bytes")

        # Return the URL of the compressed PDF and size of the compressed PDF
        return {
            "url": f"{settings.MEDIA_URL}compressed_pdfs/{output_filename}".lstrip("/"),
            "size": os.path.getsize(output_path)
        }
    except ghostscript.GhostscriptError as e:
        raise Exception(f"Error compressing PDF: {str(e)}")
