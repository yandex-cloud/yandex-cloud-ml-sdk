# Migration from Yandex Cloud ML SDK to Yandex Cloud AI Studio SDK

`yandex-cloud-ml-sdk` release is a compatibility wrapper package for `yandex-ai-studio-sdk`,
making possible for users to get their updates without changing their code.

## Renaming

Just an example commands you could run in your project directory:

```
grep -rl 'YCloudML' . | xargs sed -i 's/YCloudML/AIStudio/g'
grep -rl 'yandex-cloud-ml-sdk' . | xargs sed -i 's/yandex-cloud-ml-sdk/yandex-ai-studio-sdk/g'
grep -rl 'yandex_cloud_ml_sdk' . | xargs sed -i 's/yandex_cloud_ml_sdk/yandex_ai_studio_sdk/g'

```

Point is:

* All imports have to changed from `yandex_cloud_ml_sdk` to `yandex_ai_studio_sdk`;

* All package names in requirements have to changed from `yandex-cloud-ml-sdk` to `yandex-ai-studio-sdk`;

* Certain symbols like `YCLoudMLSDK`, `AsyncYCLoudMLSDK` and few more, must have their prefix `YCloudML` to be changed into `AIStudo`.

## Versioning policy

Last `yandex-cloud-ml-sdk` real version in PyPI is `0.18`.

`yandex-cloud-ml-sdk` release `0.19.0` is a compatibility wrapper
for `yandex-ai-studio-sdk`.

`yandex-ai-studio-sdk` have 0.19.0 as it's first release in PyPI.
