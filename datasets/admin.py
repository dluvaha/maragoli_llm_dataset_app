from django.contrib import admin
from .models import MaragoliDataset, DatasetCategory, ImportHistory


@admin.register(MaragoliDataset)
class MaragoliDatasetAdmin(admin.ModelAdmin):
    list_display = ['id', 'maragoli_text_short', 'english_text_short', 'category', 'is_validated', 'confidence_score', 'created_at']
    list_display_links = ['id', 'maragoli_text_short']
    list_filter = ['is_validated', 'category', 'created_at', 'confidence_score']
    search_fields = ['maragoli_text', 'english_text', 'category__name', 'source']
    readonly_fields = ['content_hash', 'created_at', 'updated_at', 'validated_by']
    list_per_page = 20
    ordering = ['id']
    date_hierarchy = 'created_at'
    list_editable = ['is_validated', 'confidence_score']
    actions = ['validate_selected', 'unvalidate_selected']

    fieldsets = (
        (None, {
            'fields': ('maragoli_text', 'english_text', 'category'),
            'description': 'Enter the Maragoli text and its English translation pair.'
        }),
        ('Metadata', {
            'fields': ('source', 'confidence_score', 'is_validated', 'validated_by'),
            'classes': ('wide',),
        }),
        ('System Info', {
            'fields': ('content_hash', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(boolean=True, description='Validated')
    def is_validated(self, obj):
        return obj.is_validated
    is_validated.boolean = True

    def maragoli_text_short(self, obj):
        return obj.maragoli_text[:80] + '...' if len(obj.maragoli_text) > 80 else obj.maragoli_text
    maragoli_text_short.short_description = 'Maragoli Text'

    def english_text_short(self, obj):
        return obj.english_text[:80] + '...' if len(obj.english_text) > 80 else obj.english_text
    english_text_short.short_description = 'English Text'

    @admin.action(description='Mark selected as validated')
    def validate_selected(self, request, queryset):
        count = queryset.update(is_validated=True)
        self.message_user(request, f'{count} entries marked as validated.')

    @admin.action(description='Mark selected as unvalidated')
    def unvalidate_selected(self, request, queryset):
        count = queryset.update(is_validated=False)
        self.message_user(request, f'{count} entries marked as unvalidated.')


@admin.register(DatasetCategory)
class DatasetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'dataset_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_per_page = 20
    ordering = ['name']
    fieldsets = (
        (None, {
            'fields': ('name', 'slug'),
        }),
        ('Details', {
            'fields': ('description',),
            'classes': ('wide',),
        }),
    )


@admin.register(ImportHistory)
class ImportHistoryAdmin(admin.ModelAdmin):
    list_display = ['filename', 'total_rows', 'imported_rows', 'duplicate_rows', 'invalid_rows', 'imported_by', 'imported_at']
    list_filter = ['imported_at', 'imported_by']
    search_fields = ['filename', 'notes']
    readonly_fields = ['imported_at']
    list_per_page = 20
    ordering = ['-imported_at']
    date_hierarchy = 'imported_at'
    fieldsets = (
        (None, {
            'fields': ('filename', 'imported_by'),
        }),
        ('Import Stats', {
            'fields': ('total_rows', 'imported_rows', 'duplicate_rows', 'invalid_rows'),
        }),
        ('Details', {
            'fields': ('notes', 'imported_at'),
            'classes': ('wide',),
        }),
    )
