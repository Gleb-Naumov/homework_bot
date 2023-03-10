import os
import sys
import time
import logging
import requests
import telegram
from dotenv import load_dotenv
from logging import StreamHandler


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
    except Exception as error:
        logger.error(f'Ошибка {error} сообщение не отправлено')


def get_api_answer(timestamp):
    """Делает запрос к API практикума."""
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp})
    except Exception as error:
        logging.error(f'Ендпоинт не доступен {error}')
    if response.status_code != 200:
        raise Exception('Запрос к API не удался')
    return response.json()


def check_response(response):
    """Проверяет ответ на соответствие документации."""
    if type(response) != dict:
        raise TypeError('Ответ пришел не ввиде словоря')
    if 'homeworks' not in response:
        raise Exception('Даного ключа нет в словаре')
    if type(response['homeworks']) != list:
        raise TypeError('Ответ пришел не в словаре')
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает информацию о статусе домашней работы."""
    try:
        homework
    except Exception:
        raise Exception('Ошибка')
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))
    if ('status' not in homework or homework.get('status')
            not in HOMEWORK_VERDICTS):
        raise Exception('Нет ключа "status"'
                        'или не задукоментированный статус домашней работы')
    if 'homework_name' not in homework:
        raise Exception('Ошибка нет ключа')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time() - 2629743)
    logger.debug('Проверка переменных окружения')
    if not check_tokens():
        logger.critical('Нет переменных окружения')
        exit()
    while True:
        try:
            response = get_api_answer(timestamp)
            response_check = check_response(response)[0]
            message = parse_status(response_check)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print(message)
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
