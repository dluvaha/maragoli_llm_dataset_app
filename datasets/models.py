"""
Maragoli LLM Dataset Collection App - Data Models
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify
import hashlib


class DatasetCategory(models.Model):
    """Categories for organizing Maragoli-English translation pairs."""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Dataset Categories'

    def __str__(self):
        return self.name

    def dataset_count(self):
        return self.datasets.count()


class MaragoliDataset(models.Model):
    """
    Core model: A Maragoli text paired with its English translation.
    Used for training the Maragoli Large Language Model.
    """

    # Text content
    maragoli_text = models.TextField(
        help_text="Original text in Maragoli language"
    )
    english_text = models.TextField(
        help_text="English translation of the Maragoli text"
    )

    # Organization
    category = models.ForeignKey(
        DatasetCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='datasets'
    )

    # Metadata
    source = models.CharField(
        max_length=500,
        blank=True,
        help_text="Where this translation pair was sourced from"
    )
    confidence_score = models.FloatField(
        default=1.0,
        help_text="Confidence level of the translation (0.0 to 1.0)"
    )
    is_validated = models.BooleanField(
        default=False,
        help_text="Whether this pair has been reviewed and validated"
    )
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Hash for duplicate detection
    content_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        editable=False
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Maragoli Dataset'
        verbose_name_plural = 'Maragoli Datasets'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_validated']),
            models.Index(fields=['content_hash']),
        ]

    def __str__(self):
        return f"{self.maragoli_text[:50]}... -> {self.english_text[:50]}..."

    def save(self, *args, **kwargs):
        # Generate content hash for duplicate detection
        hash_content = f"{self.maragoli_text.strip().lower()}|{self.english_text.strip().lower()}"
        self.content_hash = hashlib.sha256(hash_content.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    @classmethod
    def generate_hash(cls, maragoli_text: str, english_text: str) -> str:
        """Generate content hash without saving."""
        hash_content = f"{maragoli_text.strip().lower()}|{english_text.strip().lower()}"
        return hashlib.sha256(hash_content.encode('utf-8')).hexdigest()

    def to_training_format(self) -> dict:
        """Convert to JSON format suitable for LLM training."""
        return {
            "maragoli": self.maragoli_text,
            "english": self.english_text,
            "category": self.category.name if self.category else "general",
            "source": self.source,
            "confidence": self.confidence_score,
            "validated": self.is_validated
        }


class ImportHistory(models.Model):
    """Track Excel file imports for audit trail."""
    filename = models.CharField(max_length=500)
    total_rows = models.IntegerField(default=0)
    imported_rows = models.IntegerField(default=0)
    duplicate_rows = models.IntegerField(default=0)
    invalid_rows = models.IntegerField(default=0)
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    imported_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-imported_at']

    def __str__(self):
        return f"{self.filename} - {self.imported_rows}/{self.total_rows} imported"
