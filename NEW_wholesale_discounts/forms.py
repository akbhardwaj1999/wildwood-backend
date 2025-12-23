from django import forms
from django.core.exceptions import ValidationError
from .models import NEW_WholesaleRequest, NEW_WholesaleUser

class NEW_WholesaleRequestForm(forms.ModelForm):
    """NEW: Form for wholesale account requests"""
    
    class Meta:
        model = NEW_WholesaleRequest
        fields = [
            'business_name', 'business_type', 'tax_id', 'website',
            'expected_monthly_volume', 'reason', 'documents'
        ]
        widgets = {
            'business_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your business name'
            }),
            'business_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tax ID or EIN (optional)'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourwebsite.com (optional)'
            }),
            'expected_monthly_volume': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Expected monthly order volume'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Explain why you need wholesale access'
            }),
            'documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add empty choice for dropdown
        self.fields['business_type'].choices = [('', 'Select business type...')] + list(self.fields['business_type'].choices)
    
    def clean_documents(self):
        """Validate documents file"""
        file = self.cleaned_data.get('documents')
        
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size must be less than 10MB.')
            
            # Check file type
            allowed_types = [
                'application/pdf', 'image/jpeg', 'image/jpg', 'image/png',
                'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            if file.content_type not in allowed_types:
                raise ValidationError('Only PDF, JPG, PNG, DOC, and DOCX files are allowed.')
        
        return file
    
    def clean_expected_monthly_volume(self):
        """Validate expected monthly volume"""
        volume = self.cleaned_data.get('expected_monthly_volume')
        if volume is not None:
            try:
                # Convert to float for proper comparison
                volume_float = float(volume)
                if volume_float < 0:
                    raise ValidationError('Expected monthly volume cannot be negative.')
                return volume_float
            except (ValueError, TypeError):
                raise ValidationError('Please enter a valid number for expected monthly volume.')
        return volume

class NEW_WholesaleUserForm(forms.ModelForm):
    """NEW: Form for editing wholesale user profile (admin only)"""
    
    class Meta:
        model = NEW_WholesaleUser
        fields = [
            'is_wholesale', 'notes'
        ]
        widgets = {
            'is_wholesale': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Admin notes'
            })
        }

