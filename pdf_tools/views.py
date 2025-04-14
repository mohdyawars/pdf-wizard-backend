import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from pdf_tools.utils.s3_utils import get_file_from_s3
from pdf_tools.utils.utils import (
    extract_text_from_pdf,
    extract_images_from_pdf,
    split_pdf_to_pages,
    merge_pdfs,
    compress_pdf,
)
import uuid


class PDFExtractTextView(APIView):
    """ Extract text from a PDF file """

    def post(self, request, *args, **kwargs):
        file_key = request.data.get("fileKey")

        # Check if the file is present in the request
        if not file_key:
            return Response(
                {"error": "No file key provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            pdf_file = get_file_from_s3(file_key)

            result = extract_text_from_pdf(pdf_file)


            return Response({"data": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PDFExtractImagesView(APIView):
    """ Extract images from a PDF file """

    def post(self, request, *args, **kwargs):
        file_key = request.data.get("fileKey")

        # Check if the file is present in the request
        if not file_key:
            return Response(
                {"error": "No file key provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            pdf_file = get_file_from_s3(file_key)
            result = extract_images_from_pdf(pdf_file)

            if not result["images"]:
                return Response(
                    {"error": "PDF doesn't contain any image"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Cleanup extracted images after sending the response
            for img in result["images"]:
                image_path = img["url"].replace(
                    settings.MEDIA_URL, "")  # Remove /media/ prefix
                full_path = os.path.join(settings.MEDIA_ROOT, image_path)

                if default_storage.exists(full_path):
                    default_storage.delete(full_path)

            return Response({"data": result}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PDFMergeView(APIView):
    """
    Merge multiple PDF files into a single PDF file
    Input Format:
    {
        "pdfs": [
            {"file": "file1.pdf"},
            {"file": "file2.pdf"},
        ]
    }
    """

    def post(self, request, *args, **kwargs):
        pdf_files = request.FILES.getlist("pdfs")
        """ POST method to merge PDF files """

        # Check if the files are present in the request
        if not pdf_files:
            return Response(
                {"error": "No files uploaded!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the files are PDFs or not
        for pdf_file in pdf_files:
            if not pdf_file.name.endswith(".pdf"):
                return Response(
                    {"error": "Please upload PDF files"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Check if the file size is within the limit
        # for pdf_file in pdf_files:
        #     if pdf_file.size > int(MAX_PDF_SIZE):
        #         return Response(
        #             {"error": "File size exceeds the limit"},
        #             status=status.HTTP_400_BAD_REQUEST,
        #         )
        # for pdf_file in pdf_files:
        #     if pdf_file.size > int(MAX_PDF_SIZE):
        #         return Response(
        #             {"error": "File size exceeds the limit"},
        #             status=status.HTTP_400_BAD_REQUEST,
        #         )

        try:
            result = merge_pdfs(pdf_files)
            return Response({"data": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PDFSplitView(APIView):
    """Split a PDF file into multiple pages"""

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get("pdfFile")
        start_page = request.data.get("startPage")
        end_page = request.data.get("endPage")

        if not pdf_file:
            return Response(
                {"error": "No PDF file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        try:
            # output_dir = os.path.join(settings.MEDIA_ROOT)
            result = split_pdf_to_pages(pdf_file, "output_pages", int(start_page), int(end_page))
            return Response({"data": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PDFCompressView(APIView):
    """Compress a PDF file"""

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get("pdfFile")
        compression_level = request.data.get("compressionLevel", "low")

        if not pdf_file:
            return Response(
                {"error": "No PDF file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Save the uploaded PDF to a temporary location
            temp_filename = f"temp/{uuid.uuid4()}_{pdf_file.name}"
            temp_pdf_path = default_storage.save(temp_filename, ContentFile(pdf_file.read()))

            # Compress the PDF and get the URL
            compressed_url = compress_pdf(default_storage.path(temp_pdf_path), compression_level)

            # Clean up the temporary file
            default_storage.delete(temp_pdf_path)

            return Response({"data": compressed_url}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
