#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import base64
import json
import logging
import random
import sys

import aiohttp

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._experimental.audio.microphone import AsyncMicrophone
from yandex_cloud_ml_sdk._experimental.audio.out import AsyncAudioOut

assert sys.version_info >= (3, 10), "Python 3.10+ is required"

# Настройки API

# Конфигурация аудио для сервера
IN_RATE = 44100
OUT_RATE = 44100
CHANNELS = 1
VOICE = "dasha"

# Конфигурация инструментов
VECTOR_STORE_ID = "..."


# ======== Вспомогательные функции ========

# Декодирует строку base64 в байты
def b64_decode(s: str) -> bytes:
    return base64.b64decode(s)


# Кодирует байты в строку base64
def b64_encode(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# Генерирует фиктивные погодные данные в виде JSON
def fake_weather(city: str) -> str:
    rng = random.Random(hash(city) & 0xFFFFFFFF)

    weather_data = {
        "city": city,
        "temperature_c": rng.randint(-10, 35),
        "condition": rng.choice(["ясно", "облачно", "дождь", "снег", "гроза", "туман"]),
        "wind_m_s": round(rng.uniform(0.5, 10.0), 1),
        "advice": rng.choice([
            "Возьми лёгкую куртку.",
            "Зонт пригодится.",
            "Пей воду и избегай солнца.",
            "На дорогах скользко — будь аккуратнее.",
            "Ветрено, капюшон не помешает.",
        ]),
    }

    return json.dumps(weather_data, ensure_ascii=False)


def process_function_call(item):
    call_id = item.get("call_id")
    args_text = item.get("arguments") or "{}"

    try:
        args = json.loads(args_text)
    except json.JSONDecodeError:
        args = {}

    city = (args.get("city") or "Москва").strip()
    weather_json = fake_weather(city)

    return {
        "type": "conversation.item.create",
        "item": {
            "type": "function_call_output",
            "call_id": call_id,
            "output": weather_json
        }
    }

# ======== Основное приложение ========

async def setup_session(ws):
    """Настройка сессии"""

    await ws.send_json({
        "type": "session.update",
        "session": {
            "instructions": (
                "Ты ассистент. Помогаешь с ответами на вопросы. Отвечаешь кратко и по делу. "
                "Если просят рассказать новости —  используй функцию web_search. "
                "Если спрашивают о погоде — вызывай функцию get_weather. "
                "При вопросе про {голосовой профилировщик} - обращайся к фукнции file_search"
            ),
            "modalities": ["text", "audio"],
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "turn_detection": {
                "type": "server_vad",  # включаем серверный VAD
                "threshold": 0.5,  # чувствительность
                "silence_duration_ms": 400,  # длительность тишины для завершения речи
            },
            "voice": VOICE,
            # Инструменты для использования в агенте
            "tools": [
                # Рукописная фукнция модели для демонстрации работы с function calling
                {
                    "type": "function",
                    "name": "get_weather",
                    "description": "Получить краткую сводку погоды по городу.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"}
                        },
                        "required": ["city"],
                        "additionalProperties": False
                    }
                },
                # Встроенная функция для поиска в интернете.
                # Задание сайтов для поиска будет добавлено в API позже
                {
                    "type": "function",
                    "name": "web_search",
                    "description": "Поиск в интернете",
                    "parameters": "{}"
                },
                # Встроенная функция для поиска по файлам.
                {
                    "type": "function",
                    "name": "file_search",  # обязательное имя функции
                    "description": VECTOR_STORE_ID,  # id индекса
                    "parameters": "{}"
                }
            ]
        }
    })


# pylint: disable-next=too-many-branches
async def downlink(ws, audio_out):
    """Приём и обработка сообщений от сервера"""
    # Управление "эпохами" озвучки
    play_epoch = 0
    current_response_epoch = None

    async for msg in ws:
        if msg.type != aiohttp.WSMsgType.TEXT:
            logger.info('got non-text payload from websocket: %s', msg.data)
            continue

        message = json.loads(msg.data)
        msg_type = message.get("type")

        match msg_type:
            # Распознанный текст пользователя
            case "conversation.item.input_audio_transcription.completed":
                transcript = message.get("transcript", "")
                if transcript:
                    logger.info("on_message %s: [user (transcript): %r]", msg_type, transcript)

            # Текст, который сервер отправляет на озвучку
            case "response.output_text.delta":
                delta = message.get("delta", "")
                if delta:
                    logger.info("on_message %s: [agent (text): %r]", msg_type, delta)

            # Логируем id сессии
            case "session.created":
                session_id = (message.get("session") or {}).get("id")
                logger.info("on_message %s: [session.id = %r]", msg_type, session_id)

            # Пользователь начал говорить — прерываем текущий ответ
            case "input_audio_buffer.speech_started":
                play_epoch += 1
                current_response_epoch = None
                logger.debug("on_message %s: clear audio out buffer", msg_type)
                await audio_out.clear()

            # Начало нового ответа ассистента
            case "response.created":
                current_response_epoch = play_epoch

            # Поступают аудиоданные от ассистента
            case "response.output_audio.delta":
                if current_response_epoch == play_epoch:
                    delta = message["delta"]
                    decoded = b64_decode(delta)
                    logger.debug("on_message %s: got %d bytes", msg_type, len(decoded))
                    await audio_out.write(decoded)

            case "response.output_item.done":
                item = message.get("item") or {}
                if item.get("type") != 'function_call':
                    logger.info(
                        'on_message %s: got non-function call payload %r',
                        msg_type, item
                    )
                    continue

                payload_item = process_function_call(item)

                logger.info(
                    "[conversation.item.create(function_call_output): %r]",
                    payload_item,
                )
                await ws.send_json(payload_item)

                # Запрашиваем новый ответ агента
                logger.info("отправляем response.create после функции")
                await ws.send_json({
                    "type": "response.create"
                })

            case "error":
                logger.error("ОШИБКА СЕРВЕРА: %r", json.dumps(message, ensure_ascii=False))

            case other:
                logger.info('on_message %s: [можно добавить ваш обработчик]', other)

    logger.info("WS соединение закрыто")


async def uplink(ws):
    """Отправка аудио с микрофона на сервер"""
    mic = AsyncMicrophone(samplerate=IN_RATE)
    async for pcm in mic:
        logger.debug('send payload with size %d', len(pcm))

        try:
            await ws.send_json({
                "type": "input_audio_buffer.append",
                "audio": b64_encode(pcm)
            })
        except aiohttp.ClientConnectionResetError:
            logger.warning("unable to send new data due to websocket was closed")
            return


# Главный цикл приложения
async def main():
    sdk = AsyncYCloudML()

    # получение хедеров и folder_id - не для продакшена
    # pylint: disable=protected-access
    headers = dict(await sdk._client._get_common_headers(True, 60))
    folder_id = sdk._folder_id

    ws_url = (
        "wss://rest-assistant.api.cloud.yandex.net/v1/realtime/openai"
        f"?model=gpt://{folder_id}/speech-realtime-250923"
    )

    print("Говорите (server VAD). Нажмите Ctrl+C для выхода.")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url, headers=headers, heartbeat=20.0) as ws:
                logger.info("Подключено к Realtime API.")
                await setup_session(ws)

                async with AsyncAudioOut(samplerate=OUT_RATE) as audio_out:
                    await asyncio.gather(
                        uplink(ws),
                        downlink(ws, audio_out)
                    )
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        logger.info("Выход.")


if __name__ == "__main__":
    asyncio.run(main())
