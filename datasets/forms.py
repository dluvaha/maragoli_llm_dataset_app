from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import MaragoliDataset, DatasetCategory


class DatasetForm(forms.ModelForm):
    """Form for creating/editing individual Maragoli-English translation pairs."""

    class Meta:
        model = MaragoliDataset
        fields = ['maragoli_text', 'english_text', 'category', 'source', 'confidence_score', 'is_validated']
        widgets = {
            'maragoli_text': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3',
                'placeholder': 'Enter text in Maragoli language...'
            }),
            'english_text': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3',
                'placeholder': 'Enter English translation...'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3',
            }),
            'source': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3',
                'placeholder': 'e.g., Community elder interview, Bible translation...'
            }),
            'confidence_score': forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3',
                'min': '0',
                'max': '1',
                'step': '0.1',
            }),
        }


class CategoryForm(forms.ModelForm):
    """Form for creating/editing dataset categories."""

    class Meta:
        model = DatasetCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3',
                'placeholder': 'e.g., Greetings, Proverbs, Daily Conversation...'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3',
                'placeholder': 'Describe what type of translations belong here...'
            }),
        }


class SpreadsheetImportForm(forms.Form):
    """Form for uploading spreadsheet files for bulk import."""
    spreadsheet_file = forms.FileField(
        label='Upload Spreadsheet File',
        help_text='Accepts .xlsx, .xls, and .ods files. File should have columns: maragoli_text, english_text (category and source are optional).',
        widget=forms.ClearableFileInput(attrs={
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer',
            'accept': '.xlsx,.xls,.ods,.fods,.csv'
        })
    )


class BulkValidateForm(forms.Form):
    """Form to confirm bulk import after preview."""
    confirmed = forms.BooleanField(
        required=True,
        initial=True,
        widget=forms.HiddenInput()
    )


# ─── User Management Forms ─────────────────────────────────────────────────────

input_class = 'w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3'


class UserRegistrationForm(UserCreationForm):
    """Front-end form for creating new users with additional profile fields."""

    first_name = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={'class': input_class, 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={'class': input_class, 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': input_class, 'placeholder': 'Email address'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': input_class, 'placeholder': 'Choose a username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': input_class, 'placeholder': 'Create a password'})
        self.fields['password2'].widget.attrs.update({'class': input_class, 'placeholder': 'Confirm password'})


class UserUpdateForm(forms.ModelForm):
    """Form for updating an existing user's profile (non-password fields)."""

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': input_class}),
            'first_name': forms.TextInput(attrs={'class': input_class}),
            'last_name': forms.TextInput(attrs={'class': input_class}),
            'email': forms.EmailInput(attrs={'class': input_class}),
        }
