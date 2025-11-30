from django.contrib.auth import get_user_model
from django import forms
from django.core.validators import RegexValidator

from cart.models import OrderItem
from galleryItem.models import Variant, SpecialPrice

User = get_user_model()


class AddToCartForm(forms.ModelForm):
    quantity = forms.IntegerField(min_value=1)
    special_price = forms.ModelChoiceField(widget=forms.CheckboxSelectMultiple, required=False, queryset=None)

    class Meta:
        model = OrderItem
        fields = ['quantity', 'special_price']

    def __init__(self, *args, **kwargs):
        self.variant_id = kwargs.pop('variant_id')
        kwargs.update(initial={'quantity': '1'})

        queryset = Variant.objects.get(id=self.variant_id).product.specialprice_set.all()
        self.base_fields['special_price'].queryset = queryset

        super().__init__(*args, **kwargs)

    def clean(self):
        variant = Variant.objects.get(id=self.variant_id)
        quantity = self.cleaned_data['quantity']
        special_price = self.data.get('special_price')

        if special_price:

            self.cleaned_data['special_price'] = SpecialPrice.objects.get(id=special_price)
            self.errors.pop('special_price')

        if variant.quantity < quantity:
            raise forms.ValidationError(
                f"The maximum stock available is {variant.quantity}")
        return self.cleaned_data


class AddressForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        super().__init__(*args, **kwargs)

    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    shipping_first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    shipping_last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    shipping_email_address = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Email Address'}))
    shipping_phone_number = forms.CharField(validators=[phone_regex], max_length=16, widget=forms.TextInput(attrs={'placeholder': 'Phone number'}))
    shipping_company_name = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Company Name'}))
    shipping_address_line_1 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Address line 1'}))
    shipping_address_line_2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Address line 2'}))
    shipping_zip_code = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Zip Code'}))
    shipping_city = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'City'}))
    shipping_state = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'State'}))
    shipping_country = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Country'}))

    is_billing_address_same = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'data-billing': True}))

    billing_first_name = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    billing_last_name = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    billing_email_address = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Email Address'}))
    billing_phone_number = forms.CharField(required=False, validators=[phone_regex], max_length=16, widget=forms.TextInput(attrs={'placeholder': 'Phone number'}))
    billing_company_name = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Company Name'}))
    billing_address_line_1 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Address line 1'}))
    billing_address_line_2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Address line 2'}))
    billing_zip_code = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Zip Code'}))
    billing_city = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'City'}))
    billing_state = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'State'}))
    billing_country = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Country'}))

    def clean(self):
        data = self.cleaned_data

        if not data.get('shipping_city', None):
            self.add_error("shipping_city", "Please fill in this field")
        if not data.get('shipping_state', None):
            self.add_error("shipping_state", "Please fill in this field")
        if not data.get('shipping_country', None):
            self.add_error("shipping_country", "Please fill in this field")

        if not data.get('is_billing_address_same'):
            if not data.get('billing_first_name', None):
                self.add_error("billing_first_name",
                               "Please fill in this field")
            if not data.get('billing_last_name', None):
                self.add_error("billing_last_name",
                               "Please fill in this field")
            if not data.get('billing_email_address', None):
                self.add_error("billing_email_address",
                               "Please fill in this field")
            if not data.get('billing_phone_number', None):
                self.add_error("billing_phone_number",
                               "Please fill in this field")
            if not data.get('billing_address_line_1', None):
                self.add_error("billing_address_line_1",
                               "Please fill in this field")
            if not data.get('billing_zip_code', None):
                self.add_error("billing_zip_code",
                               "Please fill in this field")
            if not data.get('billing_city', None):
                self.add_error("billing_city", "Please fill in this field")
            if not data.get('billing_state', None):
                self.add_error("billing_state", "Please fill in this field")
            if not data.get('billing_country', None):
                self.add_error("billing_country", "Please fill in this field")
