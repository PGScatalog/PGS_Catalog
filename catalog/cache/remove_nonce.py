from django.core.cache.backends.locmem import LocMemCache
import re


class RemoveNonceFromCacheBackend(LocMemCache):
    """If a page is cached on the server and contains CSP nonces, the value of the nonce
    if not refreshed making it not matching the nonce any new HTTP response header, and
    more problematically giving the same nonce to all clients. This subclass removes
    the nonce completely from a cached page, which will be put back downstream by the
    middleware with the correct value of the new request."""
    def get(self, key, default=None, version=None):
        result = super().get(key, default, version)
        if result is not None:
            if key.startswith('views.decorators.cache.cache_page') and hasattr(result, 'content'):
                # Remove every html nonce="..." attribute from cached content
                result.content = re.sub(
                        r' nonce="[^"]+"',
                        '',
                        result.content.decode('utf-8'),
                        flags=re.IGNORECASE
                    ).encode('utf-8')
        return result
