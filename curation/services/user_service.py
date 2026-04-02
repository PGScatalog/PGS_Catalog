import os


def get_current_user_id():
    """Gets the current user ID from environment, or None if not set.
    The variable "PGS_USER" must be set with a valid username.
    This is only useful when using shell scripts that need to perform actions with auditlog, otherwise
    the current user can be fetched from the current request.
    """
    current_user = os.environ.get('PGS_USER', None)
    if current_user:
        # Check user exists, no need to keep the model though
        from django.contrib.auth import get_user_model
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=current_user)
        except user_model.DoesNotExist:
            raise ValueError(f'User "{current_user}" specified in PGS_USER environment variable does not exist.')
        current_user_id = user.id
        print(f'Running as user "{user.username}".')
    else:
        current_user_id = None
        print('No PGS_USER environment variable set. Running without user context.')
    return current_user_id
