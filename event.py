from __future__ import annotations
import dataclasses
import io
import sys
import typing as t
import collections.abc as t_abc
import yaml
from pathlib import Path

from c3 import C


emoji_star = '⭐'
emoji_trophy = '🏆'
emoji_question = '❓'
emoji_warning = '⚠️'
emoji_pc = '🖥️'
emoji_paper = '📝'


class _FalsyJunk:
    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return '<N/A>'


junk = _FalsyJunk()
# junk = None


class NS(C[str, t.Any]):
    def __getattr__(self, attr: str) -> t.Any:
        try:
            return self[attr]
        except KeyError:
            return junk

    def __setattr__(self, attr: str, val: t.Any) -> None:
        if attr.startswith('__') and attr.endswith('__'):
            return super().__setattr__(attr, val)
        self[attr] = val


@dataclasses.dataclass
class RespItem:
    value: t.Any
    sort_key: t.Any | None

no_value = RespItem('?', None)

def html_link(url: str, title: str | None = None) -> str:
    if title is None:
        title = url
    return f'<a href="{url}">{title}</a>'

class Event(NS):

    # def __repr__(self) -> str:
    #     return f'{self.id!r}'
    table_columns: list[dict[str, t.Any]] = [
        {
            'id': 'id',
            'title': 'ID',
        },
        {
            'id': 'name',
            'title': 'Название',
        },
        {
            'id': 'stage',
            'title': 'Этап',
        },
        {
            'id': 'url',
            'title': 'Ссылка',
            'sortable': False,
            'html': True,
        },
        {
            'id': 'grades',
            'title': 'Классы',
            'sortable': False,
        },
        {
            'id': 'diff',
            'title': 'Сложность',
        },
        {
            'id': 'date',
            'title': 'Дата',
        },
        {
            'id': 'rating',
            'title': 'Уровень РСОШ',
        },
        {
            'id': 'format',
            'title': 'Формат',
        },
        {
            'id': 'solutions_url',
            'title': 'Ссылка на решения',
            'sortable': False,
            'html': True,
        },
    ]
    table_columns = [
        {
            'sortable': True,
            'visible': True,
        }
        | c
        for c in table_columns
    ]

    # {
    #     'id': '$vseros_2024',
    #     'name': 'Всероссийская олимпиада школьников 2024-2025, <этап>',
    #     'stage': {'value': '0/4', 'sort_key': 0},
    #     'url': 'https://vos.olimpiada.ru/',
    #     'grades': '5,6,7,8',
    #     'diff': '2',
    #     'date': {'value': '2024', 'sort_key': 2024},
    #     'rating': '0',
    #     'format': 'online',
    #     'solutions_url': 'https://olympiads.mccme.ru/vmo/',
    # }

    def display(self) -> dict[str, t.Any]:
        res = {
            'id': self.id,
            'is_meta': self.id.startswith('$'),
            # 'name': ', '.join(str(v) for k, v in sorted(self.items()) if k.startswith('name') if v),
            'name': self.name.format_map(self) if self.name is not junk else no_value,
            'stage': (
                RespItem(f'{self.stage}/{self.num_stages}', sort_key=self.stage / self.num_stages)
                if self.stage is not junk and self.num_stages is not junk
                else no_value
            ),
            'url': html_link(self.url, title='=>') if self.url else no_value,
            'grades': RespItem(dump_grades(self.grades), sort_key=sorted(self.grades)) if self.grades else no_value,
            'diff': RespItem(self.diff * emoji_star, sort_key=self.diff) if self.diff is not junk else no_value,
            'date': format_date(self.date) if self.date is not junk else no_value,
            'rating': RespItem(self.rating * 'I' + ' ' + (4 - self.rating) * emoji_trophy, sort_key=self.rating) if self.rating else no_value,
            'format': (
                {
                    'online': emoji_pc,
                    'offline': emoji_paper,
                }.get(self.format, self.format)
                if self.format is not junk
                else no_value
            ),
            'solutions_url': html_link(self.solutions_url, title='=>') if self.solutions_url else no_value,
            'raw': repr(self),
            'mro': repr([x.id for x in self.mro()]),
            'extra': format_dict(
                {
                    k: v
                    for k, v in self.items()
                    if k
                    not in {
                        'id',
                        'name',
                        'name_main',
                        'name_year',
                        'name_stage',
                        'name_num',
                        'url',
                        'solutions_url',
                        'grades',
                        'diff',
                        'date',
                        'rating',
                        'stage',
                        'num_stages',
                        'format',
                        # 'other',
                    }
                }
            ),
        }
        res = {k: RespItem(v, v) if not isinstance(v, RespItem) else v for k, v in res.items()}
        res = {k: dataclasses.asdict(v) for k, v in res.items()}
        return res


def parse_grades(s: str) -> set[int]:
    s = str(s)

    def parse_item(s: str) -> set[int]:
        if '-' not in s:
            return {int(s)}
        mn, mx = map(int, s.split('-'))
        return set(range(mn, mx + 1))

    return set.union(*map(parse_item, s.split(',')))


def dump_grades(s: set[int]) -> str:
    return ','.join('-'.join(map(str, rng)) for rng in collapse_numbers_into_ranges(s))


def format_dict(self) -> str:
    return '\n'.join(f'{k}: {v}' for k, v in self.items())


def format_date(d: t.Any) -> str:
    match d:
        case {'start': start, 'end': end}:
            return f'{start} - {end}'
        case str():
            return d
        case _:
            return repr(d)


def collapse_numbers_into_ranges(nums: t_abc.Iterable[int]) -> t_abc.Iterator[list[int]]:
    import itertools

    rng = []
    for x in itertools.chain(sorted(nums), [t.cast(int, ...)]):
        if not rng:
            rng = [x, x]
            continue
        if x == rng[-1] + 1:
            rng[-1] = x
        else:
            yield rng if rng[0] != rng[1] else [rng[0]]
            rng = [x, x]


def _load_segment(text: str, blt: C[str, Event]) -> C[str, Event]:
    try:
        data = yaml.safe_load(io.StringIO(text))
    except Exception:
        print(text)
        raise

    events = C[str, Event](b=[blt])

    if data is None:
        return events

    for id, defi in data.items():
        defi: dict[str, t.Any]
        match defi.pop('$', None):
            case str(s):
                base_ids = s.split()
            case list(s):
                base_ids = s
            case None:
                base_ids = []
            case _:
                raise Exception(defi)
        if any(not id.startswith('$') for id in base_ids):
            raise Exception(
                f"non-abstract base(s) specified in {id}: {[id for id in base_ids if not id.startswith('$')]}"
            )
        bases = [events[id] for id in base_ids]
        event = Event(b=bases)
        event.id = id

        if 'grades' in defi:
            event.grades = parse_grades(defi.pop('grades'))

        event.__C_d__ |= defi
        events[id] = event

    return events


def _load_file(file: Path, blt: C[str, Event]) -> C[str, Event]:
    sep = '#' * 50
    text = file.read_text(encoding='utf-8')

    res = C[str, Event]()
    for part in text.split(sep):
        res.__C_b__.append(_load_segment(part, blt))
    return res


def load(p: Path) -> C[str, Event]:
    assert p.is_dir()
    blt_file = p / '__builtins__.yaml'
    assert blt_file.is_file()

    blt = _load_file(blt_file, C())

    res = C[str, Event]()
    for file in sorted(p.rglob('*.yaml')):
        if file == blt_file:
            continue
        if file.name == '_.yaml':
            continue
        res.__C_b__.append(_load_file(file, blt))
    return res
