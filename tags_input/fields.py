from django import forms
import widgets
import utils
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class TagsInputField(forms.ModelMultipleChoiceField):
    widget = widgets.TagsInputWidget
    default_error_messages = {
        'list': _('Enter a list of values.'),
        'invalid_choice': _('Select a valid choice. %s is not one of the'
                            ' available choices.'),
        'invalid_pk_value': _('"%s" is not a valid value for a primary key.')
    }

    def __init__(self, queryset, **kwargs):
        self.create_missing = kwargs.pop('create_missing', False)
        self.mapping = kwargs.pop('mapping', None)
        super(TagsInputField, self).__init__(queryset, **kwargs)
        self.widget.mapping = self.get_mapping()

    def get_mapping(self):
        if not self.mapping:
            self.mapping = mapping = utils.get_mapping(self.queryset)
            mapping['queryset'] = self.queryset
            mapping['create_missing'] = (
                self.create_missing
                or mapping.get('create_missing', False)
            )

        return self.mapping

    def clean(self, value):
        mapping = self.get_mapping()
        fields = mapping['fields']
        filter_func = mapping['filter_func']
        join_func = mapping['join_func']
        split_func = mapping['split_func']

        values = dict(
            join_func(v)[::-1] for v in self.queryset
            .filter(**filter_func(value))
            .values('pk', *fields)
        )
        values = dict((k.lower(), v) for k, v in values.iteritems())
        missing = [v for v in values if v.lower() not in values]
        if missing:
            if mapping['create_missing']:
                for v in value:
                    if v in missing:
                        o = self.queryset.model(**split_func(v))
                        o.clean()
                        o.save()
                        values[v] = o.pk
            else:
                raise ValidationError(self.error_messages['invalid_choice']
                                      % ', '.join(missing))

        ids = []
        for v in value:
            ids.append(values[v.lower()])

        return forms.ModelMultipleChoiceField.clean(self, ids)


class AdminTagsInputField(TagsInputField):
    widget = widgets.AdminTagsInputWidget

