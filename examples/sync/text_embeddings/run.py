#!/usr/bin/env python3
# pylint: disable=import-outside-toplevel
from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML

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

    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    query_model = sdk.models.text_embeddings('query')
    query_embedding = query_model.run("когда день рождения Пушкина?")

    doc_model = sdk.models.text_embeddings('doc')
    doc_embeddings = [doc_model.run(text) for text in doc_texts]

    query_embedding = np.array(query_embedding)

    dist = cdist([query_embedding], doc_embeddings, metric='cosine')
    sim = 1 - dist
    result = doc_texts[np.argmax(sim)]
    print(result)


if __name__ == '__main__':
    main()
