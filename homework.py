import os
import sys
import time
import logging
import requests
import telegram
from dotenv import load_dotenv
from logging import StreamHandler
from http import HTTPStatus
from exeption import (EndpoionNotResponse,
                      APINotResponse,
                      KeyNotInList,
                      KeyNotExists,
                      KeyNotRegister,
                      StatusKeyNotExists)


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    encoding='utf-8',
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(sys.stdout)
logger.addHandler(handler)
formater = logging.Formatter('%(asctime)s,'
                             '%(name)s, %(levelname)s, %(message)s')
handler.setFormatter(formater)


def check_tokens():
    """Проверяет доспупность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение отправлено')
    except Exception:
        logger.error('Ошибка не удалось отправить сообщение')


def get_api_answer(timestamp):
    """Делает запрос к API практикума."""
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp})
        if response.status_code != HTTPStatus.OK:
            raise APINotResponse('Запрос к API не удался')
    except Exception:
        raise EndpoionNotResponse('Ендпоинт не доступен')
    return response.json()


def check_response(response):
    """Проверяет ответ на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ пришел не ввиде словоря')
    if 'homeworks' not in response:
        raise KeyNotInList('Даного ключа нет в словаре')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Ответ пришел не в словаре')
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает информацию о статусе домашней работы."""
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))
    if 'status' not in homework:
        raise StatusKeyNotExists('Нет ключа статус')
    if homework.get('status') not in HOMEWORK_VERDICTS:
        raise KeyNotRegister('Нет зарегестрированного ключа')
    if 'homework_name' not in homework:
        raise KeyNotExists('Ошибка нет ключа')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time() - 2629743)
    logger.debug('Проверка переменных окружения')
    if not check_tokens():
        logger.critical('Нет переменных окружения')
        exit()
    last_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if not homeworks:
                None
            else:
                current_message = parse_status(homeworks[0])
                if last_message == current_message:
                    logger.debug('Сообщение не будет отправлено')
                else:
                    send_message(bot, current_message)
                    last_message = current_message
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(f'{error} Ошибка, не удалось отправить сообщение')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
