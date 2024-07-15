import argparse
import logging
from logging.handlers import RotatingFileHandler

from constants import (DT_FORMAT, FILE_CHOICE, LOG_DIR, LOG_FILE, LOG_FORMAT,
                       PRETTY_CHOICE)


def configure_argument_parser(available_modes):
    parser = argparse.ArgumentParser(description='Парсер документации Pep')
    parser.add_argument(
        'mode',
        choices=available_modes,
        help='Режимы работы парсера'
    )
    parser.add_argument(
        '-c',
        '--clear-cache',
        action='store_true',
        help='Очистка кеша'
    )

    parser.add_argument(
        '-o',
        '--output',
        choices=(PRETTY_CHOICE, FILE_CHOICE),
        help='Дополнительные способы вывода данных'
    )
    return parser


def configure_logging():
    log_dir = LOG_DIR
    log_dir.mkdir(exist_ok=True)
    log_file = LOG_FILE

    rotating_handler = RotatingFileHandler(
        log_file, maxBytes=10 ** 6, backupCount=5
    )
    logging.basicConfig(
        datefmt=DT_FORMAT,
        format=LOG_FORMAT,
        level=logging.INFO,
        handlers=(rotating_handler, logging.StreamHandler())
    )
