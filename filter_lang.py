"""
>>> segment("**")
"""

from dataclasses import dataclass
from parser import *
from typing import List, Optional

@dataclass
class Fragment:
    """
    TODO: Add doc test
    """
    pass

@dataclass
class Word(Fragment):
    """
    >>> word("Hello")
    (['H', 'e', 'l', 'l', 'o'], Input(s='Hello', i=5))
    >>> word("99hellos")
    (['9', '9', 'h', 'e', 'l', 'l', 'o', 's'], Input(s='99hellos', i=8))
    """
    value: str

@dataclass
class Ls(Fragment):
    """
    TODO: Add doc test
    """
    words: List[Word]


@dataclass
class Many0(Fragment):
    """
    TODO: Add doc test
    """
    pass

@dataclass
class Many1(Fragment):
    """
    TODO: Add doc test
    """
    pass

@dataclass
class Single(Fragment):
    """
    TODO: Add doc test
    """
    pass

@dataclass
class Segment:
    """
    TODO: Add doc test
    """
    pass

@dataclass
class Fragments(Segment):
    """
    TODO: Add doc test
    """
    fragments: List[Fragment]

@dataclass
class Dirs(Segment):
    """
    TODO: Add doc test
    """
    pass

@dataclass
class Path:
    """
    TODO: Add doc test
    """
    root: Optional[str]
    segments: List[Segment]

@dataclass
class Union:
    """
    TODO: Add doc test
    """
    paths: List[Path]

@dataclass
class Intersection:
    """
    TODO: Add doc test
    """
    paths: List[Path]

word = (alnum + tag("_")).many1().string()[1].map(Word)
ls = (tag("{") >> ws >> word ** (ws * tag(",") * ws) << ws << tag("}")).map(Ls)
fragment = (-tag("**") >> tag("*")).map(lambda x: Many0) + tag("?").map(lambda _: Single()) + tag("+").map(lambda _: Many1()) + word + ls
segment = tag("**").map(lambda _: Dirs()) + fragment.many1().map(Fragments)
path = (tag("/").opt() * (segment ** tag("/"))).starmap(Path)
union = (path ** space.many1()).map(Union)
intersection = (union ** (ws * tag("+") * ws)).map(Intersection)
