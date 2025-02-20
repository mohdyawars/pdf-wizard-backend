from django.conf import settings

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from pdf_tools.utils import (
    extract_text_from_pdf,
    extract_images_from_pdf,
    cleanup_temp_file,
)

MAX_PDF_SIZE = settings.MAX_PDF_SIZE


class PDFExtractTextView(APIView):
    """Extract text from a PDF file"""

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
    """Extract images from a PDF file"""

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
            # Schedule cleanup after response is sent
            for img in result["images"]:
                cleanup_temp_file(img["media/pdf_images"])
            return Response({"data": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
