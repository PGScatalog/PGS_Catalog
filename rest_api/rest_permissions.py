from rest_framework import permissions
from django.conf import settings


#class SafelistPermission(permissions.BasePermission):
#    """
#    Ensure the request's IP address is on the safe list configured in Django settings.
#    """
#
#    def has_permission(self, request, view):
#
#        remote_addr = request.META['REMOTE_ADDR']
#
#        for valid_ip in settings.REST_SAFE_LIST_IPS:
#            if remote_addr == valid_ip or remote_addr.startswith(valid_ip):
#                return True
#
#        return False

class BlacklistPermission(permissions.BasePermission):
    """
    Check if the request's IP address is on the blacklist configured in Django settings.
    """

    def has_permission(self, request, view):

        remote_addr = request.META['REMOTE_ADDR']

        for backlist_ip in settings.REST_BLACKLIST_IPS:
            if remote_addr == backlist_ip or remote_addr.startswith(backlist_ip):
                return False

        return True
