import os
from typing import Optional

ENV_VAR = 'YC_FOLDER_ID'

def get_folder_id(folder_id: Optional[str]) -> str:
    """
    Returns the folder_id from the argument or environment variable.
    """
    if folder_id is not None:
        return folder_id

    folder_id = os.getenv(ENV_VAR)
    if folder_id is None:
        raise ValueError(
            f"You must provide the 'folder_id' parameter or set the '{ENV_VAR}' environment variable."
        )

    return folder_id
