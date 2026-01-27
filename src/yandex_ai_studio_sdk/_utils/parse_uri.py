from __future__ import annotations

import re

URI_PATTERN: str = r'^\w+://(?P<folder_id>[^/]+)/(?P<name>[^/]+)/(?P<version>[^@/]+)(@(?P<fine_tune>[^/]+))?'

def parse_uri(uri: str) -> dict:
    # Uri example: emb://source/model_name/version@fine_tune
    match = re.match(URI_PATTERN, uri)
    if not match:
        return {'name': None, 'version': None, 'fine_tuned': None}
    groups = match.groupdict()

    version = groups.get('version')
    fine_tuned = groups.get('fine_tune') is not None if version is not None else None

    return {
        'name': groups.get('name'),
        'version': version,
        'fine_tuned': fine_tuned
    }
