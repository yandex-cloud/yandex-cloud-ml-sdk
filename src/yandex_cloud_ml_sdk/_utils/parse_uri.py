import re
from typing import Dict, Union

NOT_AVAILABLE: str = 'N/A'

def parse_uri(uri: str) -> Dict[str, Union[str, bool]]:
    # Uri example: emb://source/model_name/version@fine_tune
    pattern = r'^\w+://[^/]+/(?P<name>[^/]+)/(?P<version>[^@/]+)(@(?P<fine_tune>[^/]+))?'
    match = re.match(pattern, uri)
    if not match:
        return {'name': NOT_AVAILABLE, 'version': NOT_AVAILABLE, 'fine_tuned': False}
    groups = match.groupdict()
    return {
        'name': groups.get('name', NOT_AVAILABLE),
        'version': groups.get('version', NOT_AVAILABLE),
        'fine_tuned': groups.get('fine_tune') is not None,
    }