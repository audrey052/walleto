"""Form fields shared by every money form."""

import re

from django import forms

AMOUNT_ERROR = "Enter an amount in Rupiah, for example 2.500.000."
MAX_AMOUNT = 10**15  # one quadrillion Rupiah; anything above is a typing mistake


class AmountField(forms.CharField):
    """Whole Rupiah typed the way people write it (wallets spec, "Rupiah amount input").

    Accepts "2.500.000", "Rp 1,250,000", "2500000" and "Rp2.500.000".
    Rejects words, decimals ("2,5") and anything that isn't a whole number.
    Returns an int. When the field is not required, empty means 0.
    """

    default_error_messages = {
        "invalid": AMOUNT_ERROR,
        "negative": "Amount cannot be negative.",
        "too_large": "That amount is too large.",
    }

    def __init__(self, *, allow_negative=False, **kwargs):
        self.allow_negative = allow_negative
        # No max_length: CharField's length validator would run on the int result.
        super().__init__(**kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs.update({"inputmode": "numeric", "autocomplete": "off"})
        if not self.allow_negative:
            # static/js/app.js adds the dot separators while typing (2000000 -> 2.000.000).
            attrs["data-money"] = ""
        return attrs

    def to_python(self, value):
        text = super().to_python(value).strip()
        if text in self.empty_values:
            return None if self.required else 0
        if len(text) > 30:
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")

        negative = text.startswith(("-", "−"))
        if negative:
            text = text[1:].lstrip()
        text = re.sub(r"^rp\.?\s*", "", text, flags=re.IGNORECASE)

        # Separators must group digits in threes: 2.500.000, 1,250,000, 1 250 000.
        if not re.fullmatch(r"\d{1,3}([.,\s]\d{3})*|\d+", text):
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")
        number = int(re.sub(r"[.,\s]", "", text))

        if negative and number:
            if not self.allow_negative:
                raise forms.ValidationError(self.error_messages["negative"], code="negative")
            number = -number
        if abs(number) >= MAX_AMOUNT:
            raise forms.ValidationError(self.error_messages["too_large"], code="too_large")
        return number

    def prepare_value(self, value):
        # Show stored integers with dot separators when the form is re-displayed.
        if isinstance(value, int):
            return f"{value:,}".replace(",", ".")
        return value
