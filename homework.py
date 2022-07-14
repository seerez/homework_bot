import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

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
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


class HomeworksIsNotList(Exception):
    """Класс исключения"""

    pass


def send_message(bot, message) -> None:
    """Отправка сообщения пользователю"""
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )


def get_api_answer(current_timestamp) -> dict:
    """Получение ответа с сервера за определенный период времени"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logging.error(f'Ошибка при запросе к API: {error}')
    if response.status_code != 200:
        raise Exception('API не ответил')
    return response.json()


def check_response(response) -> list:
    """Проверка ответа API на корректность"""
    try:
        homeworks = response['homeworks']
    except KeyError as error:
        logging.error(f'Ошибка доступа к ключу: {error}')
    hw_list = response.get('homeworks', [])
    if not isinstance(hw_list, list):
        raise HomeworksIsNotList('The list of homeworks is not a list')
    return homeworks


def parse_status(homework):
    """Получение статуса домашней работы"""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка переменных окружения"""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутсвуют одна или несколько переменных окружения')
        print("Программа остановлена")
        os._exit(1)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(1656152278)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            list_homeworks = check_response(response)
            logging.info(f'Найдено{len(list_homeworks)} работ')
            if len(homework) == 0:
                print('Список домашних заданий пуст')
            else:
                status = parse_status(homework[0])
                send_message(bot, status)
            current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
