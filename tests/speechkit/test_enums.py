from __future__ import annotations

import pytest
from yandex_ai_studio_sdk._speechkit.enums import PCM16, AudioFormat, LanguageCode


@pytest.mark.parametrize(
    'input_,etalon', [
        ('mp3', AudioFormat.MP3),
        ('MP3', AudioFormat.MP3),
        ('wav', AudioFormat.WAV),
        ('OGG_OPUS', AudioFormat.OGG_OPUS),
        ('OPUS', AudioFormat.OGG_OPUS),
        ('PCM16(100)', PCM16(100, 1)),
        ('PCM16(200, 2)', PCM16(200, 2)),
        ('PCM16(300,3)', PCM16(300, 3)),
        ('LINEAR16_PCM(400,4)', PCM16(400, 4)),
        (AudioFormat.MP3, AudioFormat.MP3),
        (AudioFormat.PCM16(400), PCM16(400, 1)),
    ]
)
def test_audio_format_coerce(input_, etalon):
    assert AudioFormat._coerce(input_) == etalon


@pytest.mark.parametrize(
    'input_,exc_type', [
        ('mp4', ValueError),
        ('PCM16', ValueError),
        ('PCM16()', ValueError),
        ('PCM16(1,  2)', ValueError),
        ('PCM16(100, 200, 300)', ValueError),
        ({}, TypeError),
    ]
)
def test_audio_format_exception(input_, exc_type):
    with pytest.raises(exc_type):
        AudioFormat._coerce(input_)


@pytest.mark.parametrize(
    'input_,etalon', [
        (LanguageCode.ru_RU, 'ru-RU'),
        (LanguageCode.auto , 'auto'),
        ('RU_ru', 'ru-RU'),
        ('FOO_bAr', 'foo-BAR'),
    ]
)
def test_language_code_coerce(input_, etalon):
    assert LanguageCode._coerce_to_str(input_) == etalon


@pytest.mark.parametrize(
    'input_,exc_type', [
        ({}, TypeError),
        ('foo-bar-baz', ValueError),
        ('-foo-bar', ValueError),
        ('foo', ValueError)
    ]
)
def test_language_code_exception(input_, exc_type):
    with pytest.raises(exc_type):
        AudioFormat._coerce(input_)
