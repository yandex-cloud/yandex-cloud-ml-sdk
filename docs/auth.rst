Authentication
==============
To authenticate in Yandex Cloud ML SDK, you need to provide the ``YCloudML`` object to the model. This object contains the following fields:

``folder_id``
   `ID of the folder <https://yandex.cloud/en/docs/resource-manager/operations/folder/get-id>`_ you are going to use to work with models.

``auth``
   Key, token, or other authentication data to identify the user. You can specify the ``auth`` field value explicitly or get it automatically from the environment.

Explicitly Set Value
---------------------

If set explicitly, the ``auth`` field value can be one of the following:

**String Authentication**

As a string, you can provide:

* `IAM token <../../iam/concepts/authorization/iam-token.md>`_ of a user or `service account <../../iam/concepts/users/service-accounts.md>`_.
* Secret part of the service account `API key <../../iam/concepts/authorization/api-key.md>`_.
* `OAuth token <../../iam/concepts/authorization/oauth-token.md>`_ of a user account.

The SDK will automatically determine the type of authentication data.

**Authentication Classes**

Object of one of the following classes:

.. automodule:: yandex_cloud_ml_sdk.auth
   :no-undoc-members:

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
6. If the previous options fail, the SDK will attempt to authenticate using the IAM token of the `user <../../iam/concepts/users/accounts.md>`_ or service account `specified <../../cli/operations/index.md#auth>`_ in the `Yandex Cloud CLI <../../cli/index.yaml>`_ profile on the user's computer.

.. note::

   The maximum `lifetime <../../iam/concepts/authorization/iam-token.md#lifetime>`_ of an IAM token is 12 hours. Keep this in mind when sending requests with authentication based on an IAM token specified in a string, object of the ``IAMTokenAuth`` class, or the ``YC_IAM_TOKEN`` environment variable.