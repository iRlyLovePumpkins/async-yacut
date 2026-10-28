from http import HTTPStatus
from urllib.parse import parse_qs, urlparse

import requests
from flask import Response, flash, redirect, render_template

from . import app
from .forms import AddFilesForm, ChangeLinkForm
from .models import URLMap
from .utils import check_and_generate_short_link, save_url_map
from .yandex_disk import async_upload_files_to_yandex_disk


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
            short_id = check_and_generate_short_link()

        new_url = save_url_map(short_id, original_url)
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

        if yandex_response.status_code != HTTPStatus.OK:
            return 'File not found or expired on storage', HTTPStatus.NOT_FOUND

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

    return redirect(url_map.original, code=HTTPStatus.FOUND)


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

        short_id = check_and_generate_short_link()
        save_url_map(short_id, download_url)
        result_files.append({'filename': filename, 'short': short_id})
    return render_template('files.html', form=form, result_files=result_files)
