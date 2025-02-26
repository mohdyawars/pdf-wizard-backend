import os

from django.conf import settings
from django.core.files.storage import default_storage

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from pdf_tools.utils import (
    extract_text_from_pdf,
    extract_images_from_pdf,
    cleanup_temp_file,
    merge_pdfs,
)

MAX_PDF_SIZE = settings.MAX_PDF_SIZE


class PDFExtractTextView(APIView):
    """ Extract text from a PDF file """

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get("pdf")

        # Check if the file is present in the request
        if not pdf_file:
            return Response(
                {"error": "No file uploaded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the file is a PDF or not
        if not pdf_file.name.endswith(".pdf"):
            return Response(
                {"error": "Please upload a PDF file"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the file size is within the limit
        if pdf_file.size > int(MAX_PDF_SIZE):
            return Response(
                {"error": "File size exceeds the limit"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
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
        pdf_file = request.FILES.get("pdf")

        # Check if the file is present in the request
        if not pdf_file:
            return Response(
                {"error": "No file uploaded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the file is a PDF or not
        if not pdf_file.name.endswith(".pdf"):
            return Response(
                {"error": "Please upload a PDF file"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the file size is within the limit
        if pdf_file.size > int(MAX_PDF_SIZE):
            return Response(
                {"error": "File size exceeds the limit"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = extract_images_from_pdf(pdf_file)

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
            ...
        ]
    }
    """

    def post(self, request, *args, **kwargs):
        """ POST method to merge PDF files """
        pdf_files = request.FILES.getlist("pdfs")

        # Check if the files are present in the request
        if not pdf_files:
            return Response(
                {"error": "No files uploaded"},
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
        for pdf_file in pdf_files:
            if pdf_file.size > int(MAX_PDF_SIZE):
                return Response(
                    {"error": "File size exceeds the limit"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            result = merge_pdfs(pdf_files)
            return Response({"data": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
