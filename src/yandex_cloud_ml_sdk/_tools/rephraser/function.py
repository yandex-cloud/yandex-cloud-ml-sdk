from __future__ import annotations

from typing import Literal, Union

from typing_extensions import TypeAlias, override

from yandex_cloud_ml_sdk._models.completions.function import BaseCompletions

from .model import Rephraser

RephraserInputType: TypeAlias = Union[str, Literal[True], Rephraser]


class RephraserFunction(BaseCompletions[Rephraser]):
    """Function for creating Rephraser object, which incapsulating
    rephrasing settings.
    """

    _model_type = Rephraser

    @override
    def __call__(
        self,
        model_name: RephraserInputType,
        *,
        model_version: str = 'latest',
    ) -> Rephraser:
        """Creates a Rephraser object, which incapsulating rephrasing settings.

        :param model_name:
            Model ID used for model uri definition in a resulting Rephraser object.
            It is handled differently depending on the type and format of the input value:

            * If ``model_name`` includes ``://`` substring, it would be used unchanged.

            * Otherwise if ``model_name`` is a string, it would be used in
              ``gpt://<folder_id>/<model_name>/<model_version>`` template.

            * If ``model_name`` is a True, it would be transformed into default value
              ``gpt://<folder_id>/rephraser/<model_version>``

            * If ``model_name`` is a Rephraser object, it would returned unchanged.

        :param model_version: ``<model_version>`` value for model uri template,
            refer to model_name parameter documentation for details.

        :returns: Rephraser object, which incapsulating rephrasing settings

        """

        name: str
        if model_name is True:
            name = 'rephraser'
        elif isinstance(model_name, str):
            name = model_name
        elif isinstance(model_name, Rephraser):
            return model_name
        else:
            raise TypeError('wrong type for model_name')

        return super().__call__(
            model_name=name,
            model_version=model_version,
        )
