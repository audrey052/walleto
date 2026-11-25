from django import forms
from django.test import SimpleTestCase

from core.forms import AMOUNT_ERROR, AmountField


class AmountFieldTests(SimpleTestCase):
    """Scenarios from the wallets spec, "Rupiah amount input"."""

    def clean(self, value, **kwargs):
        return AmountField(required=False, **kwargs).clean(value)

    def test_indonesian_separators(self):
        self.assertEqual(self.clean("2.500.000"), 2500000)

    def test_prefix_and_commas(self):
        self.assertEqual(self.clean("Rp 1,250,000"), 1250000)

    def test_other_accepted_forms(self):
        for text, expected in [
            ("2500000", 2500000),
            ("Rp2.500.000", 2500000),
            ("rp. 750.000", 750000),
            ("1 250 000", 1250000),
            ("  15.000  ", 15000),
            ("0", 0),
        ]:
            with self.subTest(text=text):
                self.assertEqual(self.clean(text), expected)

    def test_not_a_number(self):
        for text in ["dua juta", "2,5", "2.5jt", "1.25.000", "12a", "Rp"]:
            with self.subTest(text=text):
                with self.assertRaisesMessage(forms.ValidationError, AMOUNT_ERROR):
                    self.clean(text)

    def test_empty_means_zero_when_optional(self):
        self.assertEqual(self.clean(""), 0)
        self.assertEqual(self.clean(None), 0)

    def test_empty_is_required_when_required(self):
        with self.assertRaises(forms.ValidationError):
            AmountField(required=True).clean("")

    def test_negative_rejected_by_default(self):
        with self.assertRaisesMessage(forms.ValidationError, "Amount cannot be negative."):
            self.clean("-50.000")

    def test_negative_allowed_when_asked(self):
        self.assertEqual(self.clean("−50.000", allow_negative=True), -50000)

    def test_too_large(self):
        with self.assertRaises(forms.ValidationError):
            self.clean("1.000.000.000.000.000")

    def test_redisplay_uses_dot_separators(self):
        self.assertEqual(AmountField().prepare_value(2500000), "2.500.000")
        self.assertEqual(AmountField().prepare_value("abc"), "abc")

    def test_marked_for_live_separators(self):
        # static/js/app.js formats inputs with data-money while typing.
        attrs = AmountField().widget_attrs(forms.TextInput())
        self.assertIn("data-money", attrs)
        self.assertEqual(attrs["inputmode"], "numeric")
        self.assertNotIn("data-money", AmountField(allow_negative=True).widget_attrs(forms.TextInput()))


class AssetTagTests(SimpleTestCase):
    def test_static_url_carries_the_file_version(self):
        import os
        from django.contrib.staticfiles import finders
        from core.templatetags.assets import asset
        url = asset("js/app.js")
        self.assertEqual(url, f"/static/js/app.js?v={int(os.path.getmtime(finders.find('js/app.js')))}")
        self.assertEqual(asset("missing/file.js"), "/static/missing/file.js")
