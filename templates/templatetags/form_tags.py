from django import template

register = template.Library()

@register.inclusion_tag('components/inputs/input.html')
def render_input(field, label=None, type="text", required=False):
    return {
        'field': field,
        'label': label or field.label,
        'type': type,
        'required': required,
        'errors': field.errors,
    }

@register.inclusion_tag('components/inputs/select.html')
def render_select(field, label=None, required=False):
    return {
        'field': field,
        'label': label or field.label,
        'required': required,
        'errors': field.errors,
    }

@register.inclusion_tag('components/inputs/checkbox.html')
def render_checkbox(field, label=None):
    return {
        'field': field,
        'label': label or field.label,
        'errors': field.errors,
    }

@register.inclusion_tag('components/inputs/textarea.html')
def render_textarea(field, label=None, rows=4):
    return {
        'field': field,
        'label': label or field.label,
        'rows': rows,
        'errors': field.errors,
    }