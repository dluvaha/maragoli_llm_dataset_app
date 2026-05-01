"""
Views for Maragoli LLM Dataset Collection App
Handles CRUD, Excel import/export, and dataset management
"""

import csv
import io
import json
import pandas as pd
from django.db import models as django_models
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator

from .models import MaragoliDataset, DatasetCategory, ImportHistory
from .forms import (
    DatasetForm, CategoryForm, SpreadsheetImportForm, BulkValidateForm,
    UserRegistrationForm, UserUpdateForm,
)


# ─── Dashboard ───────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """Main dashboard with statistics and recent datasets."""
    total_datasets = MaragoliDataset.objects.count()
    validated_count = MaragoliDataset.objects.filter(is_validated=True).count()
    category_count = DatasetCategory.objects.count()
    recent_imports = ImportHistory.objects.all()[:5]

    # Category distribution
    categories = DatasetCategory.objects.annotate(
        count=django_models.Count('datasets')
    ).order_by('-count')[:10]

    unvalidated_count = total_datasets - validated_count

    context = {
        'total_datasets': total_datasets,
        'validated_count': validated_count,
        'unvalidated_count': unvalidated_count,
        'category_count': category_count,
        'recent_imports': recent_imports,
        'categories': categories,
    }
    return render(request, 'datasets/dashboard.html', context)


# ─── Dataset CRUD ────────────────────────────────────────────────────────────────

@login_required
def dataset_list(request):
    """List all datasets with side-by-side Maragoli/English display."""
    datasets = MaragoliDataset.objects.select_related('category').all()

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        datasets = datasets.filter(
            django_models.Q(maragoli_text__icontains=search_query) |
            django_models.Q(english_text__icontains=search_query)
        )

    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        datasets = datasets.filter(category_id=category_filter)

    # Filter by validation status
    validation_filter = request.GET.get('validated', '')
    if validation_filter == 'yes':
        datasets = datasets.filter(is_validated=True)
    elif validation_filter == 'no':
        datasets = datasets.filter(is_validated=False)

    # Sort
    sort_by = request.GET.get('sort', 'id')
    if sort_by in ['id', '-id', 'maragoli_text', 'english_text', '-created_at', 'created_at',
                    'confidence_score', '-confidence_score', 'is_validated']:
        datasets = datasets.order_by(sort_by)

    # Pagination
    paginator = Paginator(datasets, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    categories = DatasetCategory.objects.all()

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'validation_filter': validation_filter,
        'sort_by': sort_by,
        'categories': categories,
        'total_count': paginator.count,
    }
    return render(request, 'datasets/dataset_list.html', context)


@login_required
def dataset_create(request):
    """Create a new Maragoli-English translation pair."""
    if request.method == 'POST':
        form = DatasetForm(request.POST)
        if form.is_valid():
            maragoli_text = form.cleaned_data['maragoli_text']
            english_text = form.cleaned_data['english_text']
            content_hash = MaragoliDataset.generate_hash(maragoli_text, english_text)

            if MaragoliDataset.objects.filter(content_hash=content_hash).exists():
                messages.warning(request, 'This translation pair already exists in the database!')
                return render(request, 'datasets/dataset_form.html', {'form': form, 'action': 'Create'})

            dataset = form.save(commit=False)
            dataset.content_hash = content_hash
            if dataset.is_validated:
                dataset.validated_by = request.user
            dataset.save()
            messages.success(request, 'Dataset entry created successfully!')
            return redirect('dataset_list')
    else:
        form = DatasetForm()

    return render(request, 'datasets/dataset_form.html', {'form': form, 'action': 'Create'})


@login_required
def dataset_update(request, pk):
    """Update an existing Maragoli-English translation pair."""
    dataset = get_object_or_404(MaragoliDataset, pk=pk)
    if request.method == 'POST':
        form = DatasetForm(request.POST, instance=dataset)
        if form.is_valid():
            updated = form.save(commit=False)
            # Sync validated_by with the checkbox state
            is_validated = 'is_validated' in request.POST
            updated.is_validated = is_validated
            updated.validated_by = request.user if is_validated else None
            updated.save()
            messages.success(request, 'Dataset updated successfully!')
            return redirect('dataset_list')
    else:
        form = DatasetForm(instance=dataset)

    return render(request, 'datasets/dataset_form.html', {
        'form': form,
        'action': 'Update',
        'dataset': dataset
    })


@login_required
@require_POST
def dataset_delete(request, pk):
    """Delete a dataset entry."""
    dataset = get_object_or_404(MaragoliDataset, pk=pk)
    dataset.delete()
    messages.success(request, 'Dataset deleted successfully!')
    return redirect('dataset_list')


@login_required
@require_POST
def dataset_bulk_delete(request):
    """Delete multiple dataset entries at once."""
    selected_ids = request.POST.getlist('selected_ids')
    if not selected_ids:
        messages.warning(request, 'No records selected for deletion.')
        return redirect('dataset_list')

    try:
        count = MaragoliDataset.objects.filter(id__in=selected_ids).delete()[0]
        messages.success(request, f'{count} dataset{"entry" if count == 1 else "entries"} deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting records: {str(e)}')

    return redirect('dataset_list')


@login_required
@require_POST
def dataset_bulk_validate(request):
    """Validate multiple dataset entries at once."""
    selected_ids = request.POST.getlist('selected_ids')
    if not selected_ids:
        messages.warning(request, 'No records selected for validation.')
        return redirect('dataset_list')

    try:
        count = MaragoliDataset.objects.filter(id__in=selected_ids).update(
            is_validated=True, validated_by=request.user
        )
        messages.success(request, f'{count} dataset{"entry" if count == 1 else "entries"} validated successfully!')
    except Exception as e:
        messages.error(request, f'Error validating records: {str(e)}')

    return redirect('dataset_list')


@login_required
@require_POST
def dataset_validate_toggle(request, pk):
    """Toggle validation status of a dataset."""
    dataset = get_object_or_404(MaragoliDataset, pk=pk)
    dataset.is_validated = not dataset.is_validated
    dataset.validated_by = request.user if dataset.is_validated else None
    dataset.save()
    status = 'validated' if dataset.is_validated else 'unvalidated'
    messages.success(request, f'Dataset {status} successfully!')
    return redirect('dataset_list')


# ─── Excel Import ────────────────────────────────────────────────────────────────

@login_required
def import_preview(request):
    """Upload spreadsheet file and preview data before import."""
    if request.method == 'POST':
        form = SpreadsheetImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['spreadsheet_file']
            filename = uploaded_file.name
            try:
                # Read file based on extension
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                if ext in ('csv',):
                    df = pd.read_csv(uploaded_file)
                elif ext in ('xlsx', 'xls'):
                    df = pd.read_excel(uploaded_file, engine='openpyxl' if ext == 'xlsx' else 'xlrd')
                elif ext in ('ods', 'fods'):
                    df = pd.read_excel(uploaded_file, engine='odf')
                else:
                    messages.error(request, f'Unsupported file format ".{ext}". Please use .xlsx, .xls, .ods, or .csv files.')
                    return redirect('import_preview')

                if df.empty:
                    messages.error(request, 'The Excel file is empty. Please upload a file with data rows.')
                    return redirect('import_preview')

                # ── Smart column detection with fuzzy matching ──
                # Build a map: normalised_name -> original column name
                original_columns = list(df.columns)
                col_map = {}  # normalised -> original

                for col in original_columns:
                    key = str(col).strip().lower().replace(' ', '_').replace('-', '_')
                    col_map[key] = str(col).strip()

                # Aliases for each expected column
                column_aliases = {
                    'maragoli_text': [
                        'maragoli_text', 'maragoli', 'maragolitext',
                        'lumaragoli', 'luyalogoli', 'maragoli_text_1',
                        'maragoli_text_2',
                    ],
                    'english_text': [
                        'english_text', 'english', 'englishtext',
                        'translation', 'english_translation', 'english_text_1',
                        'english_text_2',
                    ],
                    'category': ['category', 'categories', 'cat', 'topic', 'group'],
                    'source': ['source', 'sources', 'origin', 'src'],
                    'confidence_score': ['confidence_score', 'confidence', 'score', 'conf'],
                }

                # Resolve each expected column to the actual Excel column name
                resolved = {}  # expected -> original_column_name
                missing = []

                for expected, aliases in column_aliases.items():
                    found = None
                    # 1. Exact normalised match
                    if expected in col_map:
                        found = col_map[expected]
                    # 2. Alias match
                    if not found:
                        for alias in aliases:
                            if alias in col_map:
                                found = col_map[alias]
                                break
                    # 3. Partial / substring match (last resort)
                    if not found:
                        for norm_name, orig_name in col_map.items():
                            stripped = norm_name.replace('_', '')
                            if stripped == expected.replace('_', '') or stripped == expected.replace('_', ''):
                                found = orig_name
                                break

                    if found:
                        resolved[expected] = found
                    elif expected in ['maragoli_text', 'english_text']:
                        missing.append(expected)

                if missing:
                    found_cols = ', '.join(original_columns)
                    messages.error(
                        request,
                        f'Could not find columns for: <strong>{", ".join(missing)}</strong>. '
                        f'Columns found in your file: <strong>{found_cols}</strong>. '
                        f'Please ensure your file has <code>maragoli_text</code> and '
                        f'<code>english_text</code> columns.'
                    )
                    return redirect('import_preview')

                # Rename dataframe columns to our standard names
                rename_dict = {v: k for k, v in resolved.items()}
                df.rename(columns=rename_dict, inplace=True)

                # Clean data
                df = df.dropna(subset=['maragoli_text', 'english_text'], how='all')
                df['maragoli_text'] = df['maragoli_text'].astype(str).str.strip()
                df['english_text'] = df['english_text'].astype(str).str.strip()

                # Check for duplicates against database
                existing_hashes = set(
                    MaragoliDataset.objects.values_list('content_hash', flat=True)
                )

                preview_data = []
                duplicate_count = 0
                invalid_count = 0

                for idx, row in df.iterrows():
                    content_hash = MaragoliDataset.generate_hash(
                        row['maragoli_text'], row['english_text']
                    )
                    is_duplicate = content_hash in existing_hashes
                    is_valid = len(row['maragoli_text']) > 0 and len(row['english_text']) > 0

                    if not is_valid:
                        invalid_count += 1
                    if is_duplicate:
                        duplicate_count += 1

                    preview_data.append({
                        'row': idx + 2,
                        'maragoli_text': row['maragoli_text'],
                        'english_text': row['english_text'],
                        'category': str(row.get('category', '')) if pd.notna(row.get('category')) else '',
                        'source': str(row.get('source', '')) if pd.notna(row.get('source')) else '',
                        'is_duplicate': is_duplicate,
                        'is_valid': is_valid,
                        'content_hash': content_hash,
                    })

                # Store preview in session
                request.session['import_preview'] = preview_data
                request.session['import_validate_all'] = 'validate_all' in request.POST

                context = {
                    'preview_data': preview_data,
                    'total_rows': len(preview_data),
                    'duplicate_count': duplicate_count,
                    'invalid_count': invalid_count,
                    'importable_count': len(preview_data) - duplicate_count - invalid_count,
                    'filename': filename,
                    'validate_all': request.session.get('import_validate_all', False),
                }
                return render(request, 'datasets/import_preview.html', context)

            except Exception as e:
                messages.error(request, f'Error reading spreadsheet file: {str(e)}')
                return redirect('import_preview')
    else:
        form = SpreadsheetImportForm()

    return render(request, 'datasets/import_upload.html', {'form': form})


@login_required
@require_POST
def import_confirm(request):
    """Confirm and execute the bulk import."""
    preview_data = request.session.get('import_preview', [])
    filename = request.POST.get('filename', 'unknown.xlsx')
    validate_all = request.POST.get('validate_all', 'false') == 'true'

    if not preview_data:
        messages.error(request, 'No import data found. Please upload a file first.')
        return redirect('import_preview')

    imported_count = 0
    duplicate_count = 0
    invalid_count = 0

    try:
        with transaction.atomic():
            for item in preview_data:
                if item['is_duplicate'] or not item['is_valid']:
                    if item['is_duplicate']:
                        duplicate_count += 1
                    else:
                        invalid_count += 1
                    continue

                category = None
                if item.get('category'):
                    category, _ = DatasetCategory.objects.get_or_create(
                        name=str(item['category']).strip()
                    )

                entry = MaragoliDataset.objects.create(
                    maragoli_text=item['maragoli_text'],
                    english_text=item['english_text'],
                    category=category,
                    source=item.get('source', ''),
                    content_hash=item['content_hash'],
                )

                if validate_all:
                    entry.is_validated = True
                    entry.validated_by = request.user
                    entry.save()

                imported_count += 1

        ImportHistory.objects.create(
            filename=filename,
            total_rows=len(preview_data),
            imported_rows=imported_count,
            duplicate_rows=duplicate_count,
            invalid_rows=invalid_count,
            imported_by=request.user,
            notes=f"Imported {imported_count} new, {duplicate_count} duplicates, {invalid_count} invalid."
        )

        request.session.pop('import_preview', None)
        request.session.pop('import_validate_all', None)

        validation_note = ' All entries validated.' if validate_all else ''
        messages.success(request,
            f'Import complete! {imported_count} imported, '
            f'{duplicate_count} duplicates skipped, {invalid_count} invalid skipped.{validation_note}'
        )
    except Exception as e:
        messages.error(request, f'Import failed: {str(e)}')

    return redirect('dataset_list')


@login_required
def import_cancel(request):
    """Cancel a pending import."""
    request.session.pop('import_preview', None)
    messages.info(request, 'Import cancelled.')
    return redirect('import_preview')


# ─── Export (JSON / JSONL / CSV) ──────────────────────────────────────────────────

# Format metadata used by views and templates
EXPORT_FORMATS = {
    'standard':     {'ext': 'json',  'label': 'Standard Parallel Corpus (.json)',   'short': '.json'},
    'training':     {'ext': 'json',  'label': 'Instruction-Response (.json)',        'short': '.json'},
    'conversation': {'ext': 'json',  'label': 'Conversational (.json)',              'short': '.json'},
    'jsonl':        {'ext': 'jsonl', 'label': 'JSON Lines (.jsonl)',                'short': '.jsonl'},
    'csv':          {'ext': 'csv',   'label': 'CSV Tabular Data (.csv)',            'short': '.csv'},
}


def _build_export_queryset(category_id='', validated_only=False):
    """Shared queryset builder for export views."""
    datasets = MaragoliDataset.objects.select_related('category')
    if validated_only:
        datasets = datasets.filter(is_validated=True)
    if category_id:
        try:
            datasets = datasets.filter(category_id=int(category_id))
        except (ValueError, TypeError):
            pass
    return datasets.order_by('id')


def _row_dict(ds):
    """Return a flat dict for one dataset row (shared by JSONL and CSV)."""
    return {
        'maragoli': ds.maragoli_text,
        'english': ds.english_text,
        'category': ds.category.name if ds.category else 'general',
        'source': ds.source,
        'confidence': ds.confidence_score,
        'validated': bool(ds.is_validated),
    }


def _build_json_data(datasets, export_format):
    """Build the JSON-serialisable dict for the three .json formats."""
    dataset_list = list(datasets)

    if export_format == 'training':
        return {
            "metadata": {
                "language_pair": "maragoli-english",
                "total_entries": len(dataset_list),
                "purpose": "LLM fine-tuning for Maragoli language",
                "format": "instruction-response",
            },
            "data": [
                {
                    "instruction": f"Translate the following Maragoli text to English: {ds.maragoli_text}",
                    "input": "",
                    "output": ds.english_text,
                    "source": ds.source,
                    "category": ds.category.name if ds.category else "general",
                    "validated": bool(ds.is_validated),
                }
                for ds in dataset_list
            ]
        }
    elif export_format == 'conversation':
        return {
            "metadata": {
                "language_pair": "maragoli-english",
                "total_entries": len(dataset_list),
                "purpose": "Conversational AI training",
                "format": "messages",
            },
            "conversations": [
                {
                    "messages": [
                        {"role": "system", "content": "You are a Maragoli-English translator."},
                        {"role": "user", "content": ds.maragoli_text},
                        {"role": "assistant", "content": ds.english_text},
                    ],
                    "metadata": {
                        "source": ds.source,
                        "category": ds.category.name if ds.category else "general",
                        "validated": bool(ds.is_validated),
                    }
                }
                for ds in dataset_list
            ]
        }
    else:  # standard
        return {
            "metadata": {
                "language_pair": "maragoli-english",
                "total_entries": len(dataset_list),
                "purpose": "General LLM training dataset",
                "format": "parallel-corpus",
            },
            "translations": [_row_dict(ds) for ds in dataset_list]
        }


def _build_jsonl_content(datasets):
    """Build JSONL string: one JSON object per line."""
    lines = []
    for ds in datasets.iterator():
        obj = _row_dict(ds)
        lines.append(json.dumps(obj, ensure_ascii=False))
    return '\n'.join(lines) + '\n' if lines else ''


def _build_csv_content(datasets):
    """Build CSV string from datasets."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['maragoli', 'english', 'category', 'source', 'confidence', 'validated'])
    for ds in datasets.iterator():
        writer.writerow([
            ds.maragoli_text,
            ds.english_text,
            ds.category.name if ds.category else 'general',
            ds.source,
            ds.confidence_score,
            bool(ds.is_validated),
        ])
    return output.getvalue()


def _export_filename(export_format):
    """Return the download filename for a given format key."""
    fmt = EXPORT_FORMATS.get(export_format, EXPORT_FORMATS['standard'])
    return f'maragoli_llm_training_data_{export_format}.{fmt["ext"]}'


def _human_file_size(size_bytes):
    """Return a human-readable file size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


@login_required
def export_page(request):
    """Render the export page with format options, filters, and per-format summaries."""
    categories = DatasetCategory.objects.all().order_by('name')

    # Read filter values from GET params (persisted when user clicks download links)
    category_id = request.GET.get('category', '')
    validated_only = request.GET.get('validated_only', 'false') == 'true'

    total_datasets = MaragoliDataset.objects.count()
    validated_count = MaragoliDataset.objects.filter(is_validated=True).count()
    unvalidated_count = total_datasets - validated_count

    # Build per-format summaries server-side (no JS needed)
    format_summaries = []
    for fmt_key, fmt_meta in EXPORT_FORMATS.items():
        datasets = _build_export_queryset(category_id=category_id, validated_only=validated_only)
        dataset_list = list(datasets)

        if fmt_key == 'jsonl':
            raw = _build_jsonl_content(datasets)
        elif fmt_key == 'csv':
            raw = _build_csv_content(datasets)
        else:
            data = _build_json_data(datasets, fmt_key)
            raw = json.dumps(data, ensure_ascii=False, indent=2)

        content_bytes = raw.encode('utf-8')
        format_summaries.append({
            'key': fmt_key,
            'label': fmt_meta['label'],
            'ext': fmt_meta['ext'],
            'short': fmt_meta['short'],
            'total_entries': len(dataset_list),
            'validated_entries': sum(1 for ds in dataset_list if ds.is_validated),
            'file_size_bytes': len(content_bytes),
            'file_size_human': _human_file_size(len(content_bytes)),
            'filename': _export_filename(fmt_key),
        })

    context = {
        'categories': categories,
        'total_datasets': total_datasets,
        'validated_count': validated_count,
        'unvalidated_count': unvalidated_count,
        'format_summaries': format_summaries,
        'selected_category': category_id,
        'validated_only': validated_only,
    }
    return render(request, 'datasets/export_page.html', context)


@login_required
def export_summary_api(request):
    """API endpoint: return export summary (count, validated, file size) without downloading."""
    export_format = request.GET.get('format', 'standard')
    validated_only = request.GET.get('validated_only', 'false') == 'true'
    category_id = request.GET.get('category', '')

    datasets = _build_export_queryset(category_id=category_id, validated_only=validated_only)
    dataset_list = list(datasets)
    validated_in_export = sum(1 for ds in dataset_list if ds.is_validated)

    # Build content to measure accurate file size
    if export_format == 'jsonl':
        raw = _build_jsonl_content(datasets)
    elif export_format == 'csv':
        raw = _build_csv_content(datasets)
    else:
        data = _build_json_data(datasets, export_format)
        raw = json.dumps(data, ensure_ascii=False, indent=2)

    content_bytes = raw.encode('utf-8')
    filename = _export_filename(export_format)

    return JsonResponse({
        'total_entries': len(dataset_list),
        'validated_entries': validated_in_export,
        'unvalidated_entries': len(dataset_list) - validated_in_export,
        'file_size_bytes': len(content_bytes),
        'file_size_human': _human_file_size(len(content_bytes)),
        'format': export_format,
        'filename': filename,
        'file_ext': EXPORT_FORMATS.get(export_format, {}).get('ext', 'json'),
    })


@login_required
def export_download(request):
    """Download datasets in the chosen format (.json / .jsonl / .csv) with Save As dialog."""
    export_format = request.GET.get('format', 'standard')
    validated_only = request.GET.get('validated_only', 'false') == 'true'
    category_id = request.GET.get('category', '')

    datasets = _build_export_queryset(category_id=category_id, validated_only=validated_only)
    filename = _export_filename(export_format)

    # Build content based on format type
    if export_format == 'jsonl':
        content = _build_jsonl_content(datasets)
        content_bytes = content.encode('utf-8')
        response = HttpResponse(content_bytes, content_type='application/x-ndjson')
    elif export_format == 'csv':
        content = _build_csv_content(datasets)
        content_bytes = content.encode('utf-8-sig')  # BOM for Excel compatibility
        response = HttpResponse(content_bytes, content_type='text/csv')
    else:
        data = _build_json_data(datasets, export_format)
        content = json.dumps(data, ensure_ascii=False, indent=2)
        content_bytes = content.encode('utf-8')
        response = HttpResponse(content_bytes, content_type='application/json')

    # attachment triggers the browser "Save As" dialog so user chooses destination
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = str(len(content_bytes))
    return response


# ─── Categories Management ───────────────────────────────────────────────────────

@login_required
def category_list(request):
    """List all categories with dataset counts."""
    categories = DatasetCategory.objects.annotate(
        count=django_models.Count('datasets')
    ).order_by('-count')

    return render(request, 'datasets/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    """Create a new category."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm()

    return render(request, 'datasets/category_form.html', {'form': form, 'action': 'Create'})


@login_required
def category_update(request, pk):
    """Update an existing category."""
    category = get_object_or_404(DatasetCategory, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'datasets/category_form.html', {
        'form': form, 'action': 'Update', 'category': category
    })


@login_required
@require_POST
def category_delete(request, pk):
    """Delete a category."""
    category = get_object_or_404(DatasetCategory, pk=pk)
    category.delete()
    messages.success(request, 'Category deleted successfully!')
    return redirect('category_list')


# ─── Statistics API ──────────────────────────────────────────────────────────────

@login_required
def stats_api(request):
    """Return statistics as JSON for dashboard charts."""
    category_stats = list(
        DatasetCategory.objects.annotate(
            count=django_models.Count('datasets')
        ).values('name', 'count').order_by('-count')[:15]
    )

    total = MaragoliDataset.objects.count()
    validated = MaragoliDataset.objects.filter(is_validated=True).count()

    recent_imports = list(
        ImportHistory.objects.values('filename', 'total_rows', 'imported_rows', 'imported_at')
        .order_by('-imported_at')[:10]
    )

    return JsonResponse({
        'total_datasets': total,
        'validated_datasets': validated,
        'unvalidated_datasets': total - validated,
        'category_distribution': category_stats,
        'recent_imports': recent_imports,
    })


# ─── Authentication & User Management ──────────────────────────────────────────

class CustomLoginView(LoginView):
    """Custom login view using front-end template."""
    template_name = 'accounts/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login'
        return context


class CustomLogoutView(LogoutView):
    """Custom logout view that redirects to login page."""
    next_page = 'login'


def register(request):
    """Register a new user account from the front-end."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            # Log the user in automatically after registration
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            authenticated_user = authenticate(username=username, password=password)
            if authenticated_user:
                login(request, authenticated_user)
            messages.success(request, f'Account created successfully! Welcome, {user.first_name or user.username}.')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def user_list(request):
    """List all users with their activity statistics."""
    users = User.objects.annotate(
        dataset_count=django_models.Count('maragolidataset', distinct=True),
        validated_count=django_models.Count('maragolidataset', filter=django_models.Q(maragolidataset__is_validated=True), distinct=True),
        import_count=django_models.Count('importhistory', distinct=True),
    ).order_by('-date_joined')

    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            django_models.Q(username__icontains=search_query) |
            django_models.Q(first_name__icontains=search_query) |
            django_models.Q(last_name__icontains=search_query) |
            django_models.Q(email__icontains=search_query)
        )

    paginator = Paginator(users, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_users': paginator.count,
    }
    return render(request, 'accounts/user_list.html', context)


@login_required
def user_detail(request, pk):
    """View detailed information about a single user."""
    user_obj = get_object_or_404(User, pk=pk)

    validated_datasets = MaragoliDataset.objects.filter(validated_by=user_obj)
    import_history = ImportHistory.objects.filter(imported_by=user_obj).order_by('-imported_at')[:10]

    context = {
        'profile_user': user_obj,
        'validated_datasets': validated_datasets[:10],
        'validated_total': validated_datasets.count(),
        'import_history': import_history,
        'import_total': ImportHistory.objects.filter(imported_by=user_obj).count(),
    }
    return render(request, 'accounts/user_detail.html', context)


@login_required
def user_create(request):
    """Create a new user (available to any logged-in user)."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            messages.success(request, f'User "{user.username}" created successfully!')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'action': 'Create User',
        'title': 'Create New User',
    })


@login_required
def user_update(request, pk):
    """Update an existing user's profile."""
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user_obj.username}" updated successfully!')
            return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user_obj)

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'action': 'Update User',
        'title': f'Update User: {user_obj.username}',
        'profile_user': user_obj,
    })


@login_required
@require_POST
def user_delete(request, pk):
    """Delete a user account. Cannot delete yourself."""
    if request.user.pk == pk:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('user_list')

    user_obj = get_object_or_404(User, pk=pk)
    username = user_obj.username
    user_obj.delete()
    messages.success(request, f'User "{username}" deleted successfully!')
    return redirect('user_list')
