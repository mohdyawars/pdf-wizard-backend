from django.urls import path
from pdf_tools.views import PDFExtractTextView, PDFExtractImagesView

urlpatterns = [
    path(
        "pdfs/extract-text/",
        PDFExtractTextView.as_view(),
        name="pdf-extract-text",
    ),
    path(
        "pdfs/extract-images/",
        PDFExtractImagesView.as_view(),
        name="pdf-extract-images",
    ),
]
