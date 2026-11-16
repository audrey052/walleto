from django import forms

from core.forms import AmountField

from .models import Wallet

DUPLICATE_NAME = "You already have a wallet with this name."


class WalletForm(forms.ModelForm):
    initial_balance = AmountField(
        label="Starting balance",
        required=False,
        help_text="How much is in this wallet today. Leave empty for Rp0.",
        widget=forms.TextInput(attrs={"placeholder": "e.g. 2.500.000"}),
    )

    class Meta:
        model = Wallet
        fields = ["name", "type", "initial_balance"]
        labels = {"name": "Name", "type": "Type"}
        error_messages = {"name": {"required": "Enter a name for this wallet."}}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. BCA, GoPay, Cash", "autocomplete": "off"}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        # Set the owner before validation so model constraints are checked too.
        self.instance.user = user
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} input".strip()

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if not name:
            raise forms.ValidationError("Enter a name for this wallet.")
        clashes = Wallet.objects.for_user(self.user).active().filter(name__iexact=name)
        if self.instance.pk:
            clashes = clashes.exclude(pk=self.instance.pk)
        if clashes.exists():
            raise forms.ValidationError(DUPLICATE_NAME)
        return name

