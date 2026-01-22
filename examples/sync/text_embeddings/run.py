#!/usr/bin/env python3
# pylint: disable=import-outside-toplevel
from __future__ import annotations

from yandex_ai_studio_sdk import YCloudML

doc_texts = [
    """Александр Сергеевич Пушкин (26 мая [6 июня] 1799, Москва — 29 января [10 февраля] 1837, Санкт-Петербург)
    — русский поэт, драматург и прозаик, заложивший основы русского реалистического направления,
    литературный критик и теоретик литературы, историк, публицист, журналист.""",
    """Ромашка — род однолетних цветковых растений семейства астровые,
    или сложноцветные, по современной классификации объединяет около 70 видов невысоких пахучих трав,
    цветущих с первого года жизни."""
]


def main() -> None:
    import numpy as np
    from scipy.spatial.distance import cdist

    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()
    query_model = sdk.models.text_embeddings('query')
    query_result = query_model.run("когда день рождения Пушкина?")

    doc_model = sdk.models.text_embeddings('doc')
    doc_results = [doc_model.run(text) for text in doc_texts]

    query_embedding = np.array(query_result.embedding)
    doc_embeddings = [np.array(doc_result.embedding) for doc_result in doc_results]

    dist = cdist([query_embedding], doc_embeddings, metric='cosine')
    sim = 1 - dist
    result = doc_texts[np.argmax(sim)]
    print(result)


if __name__ == '__main__':
    main()
