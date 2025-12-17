from django import forms
from django.core.exceptions import ValidationError
from .models import NEW_TaxExemption, NEW_TaxRate

class NEW_TaxExemptionRequestForm(forms.ModelForm):
    """NEW: Form for tax exemption requests"""
    
    class Meta:
        model = NEW_TaxExemption
        fields = ['exemption_type', 'certificate_number', 'certificate_file']
        widgets = {
            'exemption_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'certificate_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter certificate number'
            }),
            'certificate_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['exemption_type'].choices = [
            ('', 'Select exemption type...'),
            ('resale', 'Resale Certificate'),
            ('nonprofit', 'Non-Profit Organization'),
            ('government', 'Government Entity'),
            ('other', 'Other')
        ]
    
    def clean_certificate_file(self):
        """Validate certificate file"""
        file = self.cleaned_data.get('certificate_file')
        
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError('File size must be less than 5MB.')
            
            # Check file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            if file.content_type not in allowed_types:
                raise ValidationError('Only PDF, JPG, and PNG files are allowed.')
        
        return file
    
    def clean_certificate_number(self):
        """Validate certificate number"""
        cert_number = self.cleaned_data.get('certificate_number')
        exemption_type = self.cleaned_data.get('exemption_type')
        
        if exemption_type in ['resale', 'nonprofit', 'government'] and not cert_number:
            raise ValidationError('Certificate number is required for this exemption type.')
        
        return cert_number

class NEW_TaxRateForm(forms.ModelForm):
    """NEW: Form for creating/editing tax rates"""
    
    class Meta:
        model = NEW_TaxRate
        fields = ['state', 'county', 'city', 'rate', 'tax_type', 'effective_date', 'expiry_date', 'is_active']
        widgets = {
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 2,
                'placeholder': 'e.g., CA, NY, TX'
            }),
            'county': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'County name (optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City name (optional)'
            }),
            'rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0',
                'max': '1',
                'placeholder': '0.0875 for 8.75%'
            }),
            'tax_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tax_type'].choices = [
            ('sales', 'Sales Tax'),
            ('use', 'Use Tax'),
            ('excise', 'Excise Tax'),
            ('other', 'Other')
        ]
    
    def clean_state(self):
        """Validate state code"""
        state = self.cleaned_data.get('state')
        if state:
            return state.upper()
        return state
    
    def clean_rate(self):
        """Validate tax rate"""
        rate = self.cleaned_data.get('rate')
        if rate is not None:
            if rate < 0:
                raise ValidationError('Tax rate cannot be negative.')
            if rate > 1:
                raise ValidationError('Tax rate cannot exceed 100% (1.0).')
        return rate
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        effective_date = cleaned_data.get('effective_date')
        expiry_date = cleaned_data.get('expiry_date')
        
        if effective_date and expiry_date and expiry_date <= effective_date:
            raise ValidationError('Expiry date must be after effective date.')
        
        return cleaned_data
