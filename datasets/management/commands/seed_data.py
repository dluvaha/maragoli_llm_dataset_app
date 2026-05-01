"""
Seed the database with sample Maragoli-English translation data.
Run: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from datasets.models import MaragoliDataset, DatasetCategory


class Command(BaseCommand):
    help = 'Seed the database with sample Maragoli-English translation pairs'

    def handle(self, *args, **options):
        # Create categories
        categories_data = {
            'Greetings': 'Common greetings and pleasantries in Maragoli',
            'Daily Life': 'Everyday conversations about daily activities',
            'Proverbs': 'Traditional Maragoli proverbs and sayings',
            'Nature': 'Terms related to nature, weather, and environment',
            'Family': 'Family relationships and terms',
            'Food': 'Food items, cooking, and eating',
            'Numbers': 'Counting and numerical expressions',
        }

        categories = {}
        for name, desc in categories_data.items():
            cat, created = DatasetCategory.objects.get_or_create(
                name=name,
                defaults={'description': desc}
            )
            categories[name] = cat
            if created:
                self.stdout.write(f'  Created category: {name}')

        # Sample translation pairs
        translations = [
            # Greetings
            ('Murembe', 'How are you?', 'Greetings', 'Community elder'),
            ('Murembe muno', 'How are you (very well)?', 'Greetings', 'Community elder'),
            ('Ndakhusura', 'I thank you', 'Greetings', 'Community elder'),
            ('Mwenda', 'Welcome', 'Greetings', 'Community gathering'),
            ('Sikhulu nende?', 'Good morning', 'Greetings', 'Community elder'),
            ('Enda mutinde', 'Go well / Goodbye', 'Greetings', 'Community gathering'),

            # Daily Life
            ('Ngoye ndikhusuva', 'I am going to the river', 'Daily Life', 'Field researcher'),
            ('Enda murayo', 'Go home', 'Daily Life', 'Community elder'),
            ('Ndi muno nende', 'I am fine', 'Daily Life', 'Community elder'),
            ('Inzu yange', 'My house', 'Daily Life', 'Field researcher'),
            ('Ndi yekhana', 'I am eating', 'Daily Life', 'Community elder'),
            ('Amatsi gabulire', 'The rains have come', 'Daily Life', 'Community elder'),

            # Proverbs
            ('Omulavu aakhulire tsimbuli tsiasire khu mutsimu', 'A person who has grown up with thorns cannot be pricked by a single thorn', 'Proverbs', 'Elder council'),
            ('Tsikhabalwa tsialole tsimbayi', 'What was not discussed during the day cannot be discussed at night', 'Proverbs', 'Elder council'),
            ('Omundu mukhongo atsikhalanga', 'A good person does not lack friends', 'Proverbs', 'Elder council'),

            # Nature
            ('Igulu riamabwerere', 'The sky is cloudy', 'Nature', 'Community elder'),
            ('Tsikhalaba tsiatsikhwire', 'The sun has set', 'Nature', 'Field researcher'),
            ('Itsangatsi', 'The moon', 'Nature', 'Community elder'),
            ('Olutsatsi', 'The sun', 'Nature', 'Community elder'),
            ('Amatsi ga matsikhulu', 'Heavy rain', 'Nature', 'Community elder'),
            ('Enyasi yetsanga', 'The wind is blowing', 'Nature', 'Field researcher'),

            # Family
            ('Mama', 'Mother', 'Family', 'Community elder'),
            ('Sosa', 'Father', 'Family', 'Community elder'),
            ('Mwana', 'Child', 'Family', 'Community elder'),
            ('Kholo', 'Grandparent', 'Family', 'Elder council'),
            ('Mukhasi', 'Wife / Woman', 'Family', 'Community elder'),
            ('Omusiani', 'Husband / Man', 'Family', 'Community elder'),
            ('Mwana witsa', 'Firstborn child', 'Family', 'Community elder'),
            ('In-law - omulamu', 'In-law', 'Family', 'Community elder'),

            # Food
            ('Obusuma', 'Ugali / Maize meal', 'Food', 'Community elder'),
            ('Tsingalo', 'Beans', 'Food', 'Community elder'),
            ('Endaka', 'Banana / Plantain', 'Food', 'Community elder'),
            ('Amasi', 'Milk', 'Food', 'Community elder'),
            ('Ebiyogo', 'Sweet potatoes', 'Food', 'Community elder'),
            ('Embirizi', 'Vegetables', 'Food', 'Field researcher'),
            ('Tsikukhu', 'Porridge', 'Food', 'Community elder'),

            # Numbers
            ('Imwe', 'One', 'Numbers', 'Community elder'),
            ('Ibili', 'Two', 'Numbers', 'Community elder'),
            ('Isatu', 'Three', 'Numbers', 'Community elder'),
            ('Inya', 'Four', 'Numbers', 'Community elder'),
            ('Itanu', 'Five', 'Numbers', 'Community elder'),
        ]

        created_count = 0
        duplicate_count = 0

        for maragoli, english, cat_name, source in translations:
            content_hash = MaragoliDataset.generate_hash(maragoli, english)
            if MaragoliDataset.objects.filter(content_hash=content_hash).exists():
                duplicate_count += 1
                continue

            MaragoliDataset.objects.create(
                maragoli_text=maragoli,
                english_text=english,
                category=categories.get(cat_name),
                source=source,
                confidence_score=0.9 if cat_name in ['Proverbs'] else 1.0,
                is_validated=cat_name in ['Greetings', 'Numbers'],
                content_hash=content_hash,
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nSeeding complete!')
        )
        self.stdout.write(f'  Created: {created_count} translation pairs')
        self.stdout.write(f'  Duplicates skipped: {duplicate_count}')
        self.stdout.write(f'  Categories: {len(categories)}')
