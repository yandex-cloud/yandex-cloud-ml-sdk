#!/usr/bin/env python3

from __future__ import annotations

from yandex_ai_studio_sdk import AIStudio


def main() -> None:
    # Imports are inside only because of SDK strange testing reasons
    # pylint: disable=import-outside-toplevel
    import numpy as np
    from scipy.spatial.distance import cdist

    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    # This is how to create model object:
    doc_model = sdk.chat.text_embeddings('text-search-doc')
    query_model = sdk.chat.text_embeddings('text-search-query')
    # sdk.chat.embeddings.list() is also available;

    # Array of texts to search
    doc_texts = [
        """Александр Сергеевич Пушкин (26 мая [6 июня] 1799, Москва — 29 января [10 февраля] 1837, Санкт-Петербург)
        — русский поэт, драматург и прозаик, заложивший основы русского реалистического направления,
        литературный критик и теоретик литературы, историк, публицист, журналист.""",
        """Пушкин неоднократно писал о своей родословной в стихах и прозе; он видел в своих предках образец истинной
        «аристократии», древнего рода, честно служившего отечеству, но не снискавшего благосклонности правителей и
        «гонимого». Не раз он обращался (в том числе в художественной форме) и к образу своего прадеда по матери —
        африканца Абрама Петровича Ганнибала, ставшего слугой и воспитанником Петра I, а потом военным инженером и
        генералом""",
    ]

    # Search query
    query_text = "когда день рождения Пушкина?"

    # Getting texts embeddings:
    doc_embeddings = []
    for text in doc_texts:
        # Removing extra spaces from """-syntax
        text = ' '.join(text.split())
        embedding = doc_model.run(text)
        doc_embeddings.append(embedding)

    # Getting query embedding:
    query_embedding = query_model.run(query_text)

    # Cosine distance calculation:
    cosine_distance = cdist([query_embedding], doc_embeddings, metric="cosine")
    # Similarity calculation:
    cosine_similarity = 1 - cosine_distance
    # Finding most suitable text index:
    argmax = np.argmax(cosine_similarity)
    # Getting text by calculated index:
    result = doc_texts[argmax]

    # Wonderful, printing of found text:
    print(' '.join(result.split()))


if __name__ == '__main__':
    main()
