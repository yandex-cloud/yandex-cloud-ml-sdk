import re

NOT_AVAILABLE: str = 'N/A'
URI_PATTERN: str = r'^\w+://[^/]+/(?P<name>[^/]+)/(?P<version>[^@/]+)(@(?P<fine_tune>[^/]+))?'

def parse_uri(uri: str) -> dict:
    # Uri example: emb://source/model_name/version@fine_tune
    match = re.match(URI_PATTERN, uri)
    if not match:
        return {'name': NOT_AVAILABLE, 'version': NOT_AVAILABLE, 'fine_tuned': False}
    groups = match.groupdict()
    return {
        'name': groups.get('name', NOT_AVAILABLE),
        'version': groups.get('version', NOT_AVAILABLE),
        'fine_tuned': groups.get('fine_tune') is not None,
    }
