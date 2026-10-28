from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional


class ChangeLinkForm(FlaskForm):
    """
    Форма для изменения длинных ссылок на короткие.
    """
    original_link = URLField(
        'Поле для оригинальной ссылки',
        validators=[DataRequired(message='Обязательное поле'),
                    Length(1, 128)]
    )
    custom_id = StringField(
        'Ваш вариант короткой ссылки',
        validators=[Length(1, 16), Optional()]
    )
    submit = SubmitField('Добавить')


class AddFilesForm(FlaskForm):
    """Форма для добавления файлов и создания ссылок для них."""
    files = MultipleFileField()
    submit = SubmitField('Добавить')
