"""`{% asset "js/app.js" %}`: a static URL that changes whenever the file changes.

Browsers cache `/static/js/app.js` and keep running the old script after an
edit. Adding the file's modification time as `?v=` gives each version its own
URL, so a normal reload picks up new CSS and JavaScript.
"""

import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def asset(path):
    url = static(path)
    found = finders.find(path)
    if found:
        url = f"{url}?v={int(os.path.getmtime(found))}"
    return url
