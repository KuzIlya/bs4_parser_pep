import logging
import re
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, MAIN_PEP_URL
from outputs import control_output
from utils import find_tag, create_soup
from exceptions import EmptyResponseException


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')

    main_div = find_tag(
        create_soup(session, whats_new_url), 'section',
        attrs={'id': 'what-s-new-in-python'}
    )

    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})

    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]

    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        version_link = urljoin(whats_new_url, version_a_tag['href'])
        h1 = find_tag(create_soup(session, version_link), 'h1')
        dl = find_tag(create_soup(session, version_link), 'dl')
        dl_text = dl.text.replace('\n', ' ')

        results.append(
            (version_link, h1.text, dl_text)
        )

    return results


def latest_versions(session):

    sidebar = find_tag(
        create_soup, 'div', {'class': 'sphinxsidebarwrapper'}
    )
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise EmptyResponseException('Ничего не нашлось')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        link = a_tag['href']
        ver_stat = re.search(pattern, a_tag.text)
        if ver_stat is not None:
            version, status = ver_stat.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')

    main_tag = find_tag(
        create_soup(session, downloads_url), 'div', {'role': 'main'}
    )
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]

    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = session.get(archive_url)

    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):

    logs_error = []

    numerical_index = find_tag(
        create_soup(session, MAIN_PEP_URL), 'section',
        {'id': 'numerical-index'}
    )
    table_tags = numerical_index.find_all('tr')

    for tag in tqdm(table_tags[1:], desc='Смотрю статусы PEP'):
        pep_link = tag.td.find_next_sibling().find('a')['href']
        pep_url = urljoin(MAIN_PEP_URL, pep_link)

        pep_information = find_tag(create_soup(session, pep_url), 'dl')

        pep_statuses = find_tag(
            pep_information,
            lambda tag: tag.name == 'dt' and 'Status' in tag.text
        )

        pep_status = pep_statuses.find_next_sibling().text

        try:
            EXPECTED_STATUS[pep_status] += 1
        except KeyError:
            logs_error.append(logging.info(f'статуса {pep_status} нету'))

    results = [('Статус', 'Количество')]

    results.extend(EXPECTED_STATUS.items())
    total_value = sum(EXPECTED_STATUS.values())
    results.append(('Total', total_value))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()

    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)

    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
