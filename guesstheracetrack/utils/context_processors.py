# Context processors
# https://docs.djangoproject.com/en/4.1/ref/templates/api/#context-processors


def user_context(request):
    """Generates context variables for the user"""
    return {"user": request.user if request.user.is_authenticated else None}
