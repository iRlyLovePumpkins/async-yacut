from random import choice
from string import ascii_letters, digits

from . import db
from .models import URLMap

MAX_ATTEMPTS = 1000


def get_unique_short_id():
    char_pool = ascii_letters + digits
    length = 6
    result = "".join(choice(char_pool) for _ in range(length))
    return result


def check_and_generate_short_link():
    for _ in range(MAX_ATTEMPTS):
        short_id = get_unique_short_id()
        if (
            short_id != 'files'
            and not URLMap.query.filter_by(short=short_id).first()
        ):
            return short_id
    raise RuntimeError('Не удалось сгенерировать уникальный идентификатор.')


def save_url_map(short_id, original_url):
    new_url = URLMap(
        original=original_url,
        short=short_id
    )
    db.session.add(new_url)
    db.session.commit()
    return new_url
