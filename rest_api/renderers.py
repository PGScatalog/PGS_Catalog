from rest_framework.renderers import BrowsableAPIRenderer

class NoOptionBrowsableAPIRenderer(BrowsableAPIRenderer):
    """Overrides the default BrowsableAPIRenderer to disable the OPTIONS button without having to modify the template"""

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super().get_context(data, accepted_media_type, renderer_context)
        context['options_form'] = None # This disables the rendering of the OPTIONS button
        return context