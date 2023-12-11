from django import forms
from django.forms import ModelForm
from .models import FavoriteLocation


class ChangeForm(forms.Form):
    name = forms.CharField(label="Name", max_length=50)
    description = forms.CharField(label="Description", max_length=500)


class FavoriteForm(ModelForm):
    class Meta:
        model = FavoriteLocation
        fields = ["address", "name"]

        labels = {
            'address': '',
            'name': '',
        }

        widgets = {
            'address': forms.TextInput(attrs={'placeholder': 'Enter address'}),
            'name': forms.TextInput(attrs={'placeholder': 'Enter location name'}),
        }
