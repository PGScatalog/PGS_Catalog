from django.utils.html import format_html


def individuals_format(value, use_icon=None):
    html = '{:,} individuals'.format(value)
    if use_icon:
        html = f'<div class="individuals_count">{html}</div>'
    return format_html(html)
