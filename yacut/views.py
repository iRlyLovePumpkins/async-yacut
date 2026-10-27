from random import choice
from string import ascii_letters, digits
from urllib.parse import parse_qs, urlparse

import requests
from flask import Response, flash, redirect, render_template

from . import app, db
from .forms import AddFilesForm, ChangeLinkForm
from .models import URLMap
from .yandex_disk import async_upload_files_to_yandex_disk


def get_unique_short_id():
    char_pool = ascii_letters + digits
    length = 6
    result = "".join(choice(char_pool) for _ in range(length))
    return result


@app.route('/', methods=['GET', 'POST'])
def index_view():
    form = ChangeLinkForm()

    if form.validate_on_submit():
        original_url = form.original_link.data
        short_id = form.custom_id.data

        if short_id:
            if (
                short_id == 'files'
                or URLMap.query.filter_by(short=short_id).first()
            ):
                flash('Предложенный вариант короткой ссылки уже существует.')
                return render_template('index.html', form=form)
        else:
            while True:
                short_id = get_unique_short_id()
                if (
                    short_id != 'files'
                    and not URLMap.query.filter_by(short=short_id).first()
                ):
                    break
        new_url = URLMap(
            original=original_url,
            short=short_id
        )
        db.session.add(new_url)
        db.session.commit()
        return render_template('index.html', form=form, new_url=new_url)
    return render_template('index.html', form=form)


@app.route('/<short_id>')
def redirect_view(short_id):
    url_map = URLMap.query.filter_by(short=short_id).first_or_404()

    if (
        'downloader.disk.yandex.ru' in url_map.original
        or 'yandex' in url_map.original
    ):
        yandex_response = requests.get(url_map.original, stream=True)

        if yandex_response.status_code != 200:
            return 'File not found or expired on storage', 404

        parsed_url = urlparse(url_map.original)
        query_params = parse_qs(parsed_url.query)
        filename = query_params.get('filename', [f'file_{short_id}'])[0]

        return Response(
            yandex_response.iter_content(chunk_size=8192),
            content_type=yandex_response.headers.get(
                'content-type', 'application/octet-stream'
            ),
            headers={
                'Content-Disposition': (
                    'attachment; '
                    f'filename="{filename}"'
                )
            },
        )

    return redirect(url_map.original, code=302)


@app.route('/files', methods=['GET', 'POST'])
async def files_view():
    form = AddFilesForm()

    if not form.validate_on_submit():
        return render_template('files.html', form=form)

    files = form.files.data
    uploaded_files_data = await async_upload_files_to_yandex_disk(files)
    result_files = []

    for filename, download_url in uploaded_files_data:
        if not download_url:
            continue

        while True:
            short_id = get_unique_short_id()
            if (
                short_id != 'files'
                and not URLMap.query.filter_by(short=short_id).first()
            ):
                break
        new_url = URLMap(original=download_url, short=short_id)
        db.session.add(new_url)
        db.session.commit()
        result_files.append({'filename': filename, 'short': short_id})
    return render_template('files.html', form=form, result_files=result_files)