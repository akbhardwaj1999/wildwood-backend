import datetime

from django import forms

from galleryItem.models import Review, GalleryItem, Variant
from galleryItem.utils import yesterday


class RanksForm(forms.Form):
    years_to_display = range(datetime.datetime.now().year - 10,
                             datetime.datetime.now().year + 10)
    date = forms.DateField(initial=yesterday, widget=forms.SelectDateWidget(years=years_to_display))


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'content', 'keep_anonymous']
        widgets = {
            'rating': forms.RadioSelect(),
        }


class ImportReviewsForm(forms.Form):
    file = forms.FileField()


# For admin
class GalleryItemAdminModelForm(forms.ModelForm):
    class Meta:
        model = GalleryItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(GalleryItemAdminModelForm, self).__init__(*args, **kwargs)
        self.fields['default_variant'].queryset = Variant.objects.filter(product=self.instance)
