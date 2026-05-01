"""
migrate_sqlite_to_postgres.py

Run this script to export all data from your SQLite database
into a JSON fixture file. Then load it into PostgreSQL using:

    python manage.py loaddata sqlite_data.json

Usage (Command Prompt / bash):
    python manage.py shell < migrate_sqlite_to_postgres.py

Usage (PowerShell):
    Get-Content migrate_sqlite_to_postgres.py | python manage.py shell

This creates:  sqlite_data.json  (in your project root)
"""

import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def export_all():
    from datasets.models import MaragoliDataset, DatasetCategory, ImportHistory
    from django.contrib.auth.models import User

    data = []

    # 1. Categories (must come before datasets due to FK)
    for cat in DatasetCategory.objects.all():
        data.append({
            "model": "datasets.datasetcategory",
            "pk": cat.pk,
            "fields": {
                "name": cat.name,
                "description": cat.description,
                "slug": cat.slug,
                "created_at": cat.created_at.isoformat(),
                "updated_at": cat.updated_at.isoformat(),
            }
        })

    # 2. Users (needed for validated_by FK)
    for user in User.objects.all():
        data.append({
            "model": "auth.user",
            "pk": user.pk,
            "fields": {
                "password": user.password,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "is_superuser": user.is_superuser,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_active": user.is_active,
                "date_joined": user.date_joined.isoformat(),
            }
        })

    # 3. Datasets
    for ds in MaragoliDataset.objects.select_related('category', 'validated_by').all():
        data.append({
            "model": "datasets.maragolidataset",
            "pk": ds.pk,
            "fields": {
                "maragoli_text": ds.maragoli_text,
                "english_text": ds.english_text,
                "category": ds.category_id,
                "source": ds.source,
                "confidence_score": ds.confidence_score,
                "is_validated": ds.is_validated,
                "validated_by": ds.validated_by_id,
                "content_hash": ds.content_hash,
                "created_at": ds.created_at.isoformat(),
                "updated_at": ds.updated_at.isoformat(),
            }
        })

    # 4. Import History
    for imp in ImportHistory.objects.all():
        data.append({
            "model": "datasets.importhistory",
            "pk": imp.pk,
            "fields": {
                "filename": imp.filename,
                "total_rows": imp.total_rows,
                "imported_rows": imp.imported_rows,
                "duplicate_rows": imp.duplicate_rows,
                "imported_by": imp.imported_by_id,
                "imported_at": imp.imported_at.isoformat(),
                "notes": imp.notes,
            }
        })

    output_path = BASE_DIR / "sqlite_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(data)} objects to {output_path}")
    print(f"  - Categories: {DatasetCategory.objects.count()}")
    print(f"  - Datasets: {MaragoliDataset.objects.count()}")
    print(f"  - Users: {User.objects.count()}")
    print(f"  - Import History: {ImportHistory.objects.count()}")
    print(f"\nNext steps:")
    print(f"  1. Set PostgreSQL environment variables")
    print(f"  2. python manage.py migrate")
    print(f"  3. python manage.py loaddata sqlite_data.json")

export_all()
