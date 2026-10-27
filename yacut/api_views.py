import re

from flask import jsonify, request, url_for

from . import app, db
from .error_handlers import InvalidAPIUsage
from .models import URLMap
from .views import get_unique_short_id

MAX_SHORT_LINK_LENGTH = 16


@app.route('/api/id/', methods=['POST'])
def add_short_link():
    data = request.get_json(silent=True)
    if not data:
        raise InvalidAPIUsage('Отсутствует тело запроса')
    if 'url' not in data:
        raise InvalidAPIUsage('\"url\" является обязательным полем!')

    original_url = data['url']
    custom_id = data.get('custom_id')

    if custom_id:
        if (
            len(custom_id) > 16 or
            not re.match(r'^[A-Za-z0-9]+$', custom_id) or
            custom_id == 'files'
        ):
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки'
            )

        if URLMap.query.filter_by(short=custom_id).first() is not None:
            raise InvalidAPIUsage(
                'Предложенный вариант короткой ссылки уже существует.'
            )

        short_id = custom_id
    else:
        while True:
            short_id = get_unique_short_id()
            if (
                short_id != 'files'
                and not URLMap.query.filter_by(short=short_id).first()
            ):
                break

    new_url = URLMap(original=original_url, short=short_id)
    db.session.add(new_url)
    db.session.commit()
    return jsonify(
        {
            'url': new_url.original,
            'short_link': url_for(
                'redirect_view',
                short_id=new_url.short,
                _external=True
            ),
        }
    ), 201


@app.route('/api/id/<short_id>/', methods=['GET'])
def get_og_link(short_id):
    url_map = URLMap.query.filter_by(short=short_id).first()
    if not url_map:
        raise InvalidAPIUsage('Указанный id не найден', 404)
    return jsonify({'url': url_map.original}), 200
