from django.db import models


class PDFMetadata(models.Model):
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="Size in bytes")
    num_pages = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    text_extracted = models.BooleanField(default=False)
    images_extracted = models.PositiveIntegerField(default=0)
    merged_pdf = models.BooleanField(default=False)

    def __str__(self):
        return self.file_name
