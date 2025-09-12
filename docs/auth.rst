Authentication
==============
To authenticate in Yandex Cloud ML SDK, you need to provide the ``YCloudML`` object to the model. This object contains the following fields:

``folder_id``
   `ID of the folder <https://yandex.cloud/docs/resource-manager/operations/folder/get-id>`_ you are going to use to work with models.

``auth``
   Key, token, or other authentication data to identify the user. You can specify the ``auth`` field value explicitly or get it automatically from the environment.

Explicitly Set Value
---------------------

If set explicitly, the ``auth`` field value can be one of the following:

**String Authentication**

As a string, you can provide:

* `IAM token <https://yandex.cloud/docs/iam/concepts/authorization/iam-token>`_ of a user or `service account <https://yandex.cloud/docs/iam/concepts/users/service-accounts>`_.
* Secret part of the service account `API key <https://yandex.cloud/docs/iam/concepts/authorization/api-key>`_.
* `OAuth token <https://yandex.cloud/docs/iam/concepts/authorization/oauth-token>`_ of a user account.

The SDK will automatically determine the type of authentication data.

**Authentication Classes**

Object of one of the following classes:

* `APIKeyAuth`: Allows you to explicitly set authentication by the provided API key. Example: `auth = APIKeyAuth('<API_key>')`.
* `IAMTokenAuth`: Allows you to explicitly set authentication by the provided API token. Example: `auth = IAMTokenAuth('<IAM_token>')`.
* `OAuthTokenAuth`: Allows you to explicitly set authentication by the provided OAuth token. Example: `auth = OAuthTokenAuth('<OAuth_token>')`.
* `MetadataAuth`: Allows you to explicitly set authentication as the service account specified in the {{ compute-full-name }} VM [metadata](../../compute/concepts/vm-metadata.md). Example: `auth = MetadataAuth()`.
* `EnvIAMTokenAuth`: Allows you to explicitly set authentication using the IAM token specified in the `YC_TOKEN` or any other environment variable. Example: `auth = EnvIAMTokenAuth()` or `auth = EnvIAMTokenAuth("ENV_VAR")`.

The SDK obtains the IAM token from this environment variable with each request, so you can occasionally update the IAM token in the environment variable yourself outside the SDK. This authentication option is optimal for use with a [service agent](../../datasphere/operations/community/create-ssa.md) in {{ ml-platform-full-name }} if that service has [access](../../iam/concepts/service-control.md) to other resources in the user's cloud.
* `YandexCloudCLIAuth`: Allows you to explicitly set authentication as a [user](../../iam/concepts/users/accounts.md) or service account [specified](../../cli/operations/index.md#auth) in the [{{ yandex-cloud }} CLI](../../cli/index.yaml) profile on the user's computer. Example: `auth = YandexCloudCLIAuth()`.
* `NoAuth`: Specifies that no authentication data will be provided. Example: `auth = NoAuth()`.

You can get these classes by importing them from the ML SDK library. Here is an example:

.. code-block:: python

   from yandex_cloud_ml_sdk.auth import APIKeyAuth

Value Obtained from the Environment
------------------------------------

If the ``auth`` field is not explicitly set, the SDK will automatically try to select one of the authentication options in the following order:

1. Authenticate using the API key from the ``YC_API_KEY`` environment variable if it is set.
2. Authenticate using the IAM token from the ``YC_IAM_TOKEN`` environment variable if it is set.
3. Authenticate using the OAuth token from the ``YC_OAUTH_TOKEN`` environment variable if it is set.
4. If none of these environment variables are set, the SDK will attempt to authenticate using the IAM token of the service account specified in the VM metadata.
5. Authenticate using the IAM token from the ``YC_TOKEN`` environment variable if it is set.

   The SDK obtains the IAM token from this environment variable with each request, so you can occasionally update the IAM token in the ``YC_TOKEN`` environment variable yourself outside the SDK.
6. If the previous options fail, the SDK will attempt to authenticate using the IAM token of the `user <https://yandex.cloud/docs/iam/concepts/users/accounts>`_ or service account `specified <https://yandex.cloud/docs/cli/operations/#auth>`_ in the `Yandex Cloud CLI <https://yandex.cloud/docs/cli/>`_ profile on the user's computer.

.. note::

   The maximum `lifetime <https://yandex.cloud/docs/iam/concepts/authorization/iam-token#lifetime>`_ of an IAM token is 12 hours. Keep this in mind when sending requests with authentication based on an IAM token specified in a string, object of the ``IAMTokenAuth`` class, or the ``YC_IAM_TOKEN`` environment variable.

Authentication methods classes
------------------------------

.. automodule:: yandex_cloud_ml_sdk.auth
   :no-undoc-members:
