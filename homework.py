import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (ErrorAccessingJson, HomeworksIsNotList,
                        MessageIsNotSent, ResponseError, ResponseNotAnswered)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='.homework.log',
    format='%(asctime)s, %(levelname)s, %(funcName)s, %(message)s, %(name)s'
)


def send_message(bot, message) -> None:
    """Отправка сообщения пользователю."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.info('Сообщение отправлено')
    except MessageIsNotSent:
        logging.error('Ошибка при отправке сообщения')


def get_api_answer(current_timestamp) -> dict:
    """Получение ответа с сервера за определенный период времени."""
    logging.info("Запрос к API")
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except ResponseError:
        logging.error('Ошибка при запросе к API')
    if response.status_code != HTTPStatus.OK:
        raise ResponseNotAnswered('API не ответил')
    try:
        return response.json()
    except ErrorAccessingJson:
        logging.error('Ошибка при форматировании данных в формат json')


def check_response(response) -> list:
    """Проверка ответа API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Ошибка типа данных response')
    if 'homeworks' not in response:
        logging.error('Ошибка доступа к ключу homeworks')
        raise KeyError('Ключ homeworks отсутсвует в словаре')
    if 'current_date' not in response:
        logging.error('Ошибка доступа к ключу current_date')
        raise KeyError('Ключ current_date отсутсвует в словаре')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise HomeworksIsNotList('The list of homeworks is not a list')
    return homeworks


def parse_status(homework):
    """Получение статуса домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        raise KeyError('Ошибка при обращении к homework_name')
    if homework_status is None:
        raise KeyError("Ошибка при обращении к status")
    if HOMEWORK_STATUSES.get(homework_status) is None:
        raise KeyError("Статуса нет в словаре")
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутсвуют одна или несколько переменных окружения')
        sys.exit('Отсутсвуют одна или несколько переменных окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_report = {}
    prev_report = {}
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            list_homeworks = check_response(response)
            logging.info(f'Найдено {len(list_homeworks)} работ')
            for homework in list_homeworks:
                current_report = {
                    'homework_name': homework.get('homework_name'),
                    'message': parse_status(homework),
                    'homework_status': homework.get('status')
                }
                logging.debug('Работа {0} статус {1}'.format(
                    current_report['homework_name'],
                    current_report['homework_status']
                ))
            if current_report != prev_report:
                send_message(bot, current_report.get('message'))
                prev_report = current_report.copy()
            if not homework:
                logging.info('Список домашних заданий пуст')
            else:
                status = parse_status(homework[0])
                send_message(bot, status)
            current_timestamp = response['current_date']

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
