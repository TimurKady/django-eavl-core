from model_utils import Choices
from django.utils.translation import gettext_lazy as _

FIELD_TYPES = Choices(
    (0, 'nested', _('Nested – Allows you to nest a Schema inside a field')),
    (1, 'bool', _('Boolean – A boolean field')),
    (2, 'const', _('Const – A field of preset constant')),
    (3, 'date', _('Date – ISO8601-formatted date string')),
    (4, 'datetime', _('DateTime – A formatted datetime string')),
    (5, 'decimal', _('Decimal – A Python Decimal type field')),
    (6, 'email', _('E-mail – An email field')),
    (7, 'enum', _('ENum – A character and value enumeration field')),
    (8, 'float', _('Float – A double as an IEEE-754 double precision float')),
    (9, 'IP', _('IP – A general IP address field')),
    (10, 'int', _('Integer – An integer field')),
    (11, 'raw', _('Raw – Field that applies no formatting')),
    (12, 'string', _('String – A string field')),
    (13, 'text', _('Text – A text field')),
    (14, 'time', _('Time – A formatted time string')),
    (15, 'timedelta', _('TimeDelta – Field containing time span values')),
    (16, 'URL', _('URL – An URL field')),
    (17, 'UUID', _('UUID – A UUID field')),
)

UNIQUE_SET = Choices(
    (0, 'normal', _('Do not check for uniqueness')),
    (1, 'globaly', _('Unique globally')),
    (2, 'entity', _('Unique within an entity type')),
)


VALIDATOR_TYPES = Choices(
    (0, 'Equal', _('Equal – Validator which succeeds if the value passed to \
it is equal to comparable.')),

    (1, 'Length', _('Length – Validator which succeeds if the value passed to \
it has a length between a minimum and maximum.')),

    (2, 'OneOf', _('OneOf – Validator which succeeds if value is a member of \
choices.')),

    (3, 'Range', _('Range – Validator which succeeds if the value passed to \
it is within the specified range.')),

    (4, 'Regexp', _('Regexp – Validator which succeeds if the value matches \
regex.')),
)
