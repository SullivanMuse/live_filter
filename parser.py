from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Tuple

@dataclass
class Input:
    s: str = field(default_factory=input)
    i: int = 0
    
    def __bool__(self):
        return self.i < len(self.s)
    
    def curr(self, n=1):
        return self.s[self.i : self.i + n]
    
    def advance(self, n=1):
        return Input(self.s, self.i + n)

@dataclass
class Parser:
    f: Callable[[Input], Optional[Tuple[Any, Input]]] = None
    
    def __call__(self, s=None):
        if not isinstance(s, Input):
            s = Input(s)
        return self.f(s)
    
    def __mul__(self, other):
        """
        Concatenation

        >>> p = tag("x") * tag("y")
        >>> p("xy")
        (('x', 'y'), Input(s='xy', i=2))
        >>> p("yx")
        >>> p("x")
        >>> p("y")
        """
        @Parser
        def call(s):
            if (r := self(s)):
                (a, s) = r
                if (r := other(s)):
                    (b, s) = r
                    return ((a, b), s)
        return call
    
    def __add__(self, other):
        """
        Like regex |

        >>> p = tag("x") + tag("y")
        >>> p("xy")
        ('x', Input(s='xy', i=1))
        >>> p("yx")
        ('y', Input(s='yx', i=1))
        >>> p("x")
        ('x', Input(s='x', i=1))
        >>> p("y")
        ('y', Input(s='y', i=1))
        """
        @Parser
        def call(s):
            return self(s) or other(s)
        return call
    
    def __neg__(self):
        """
        Like regex !

        >>> p = -tag("x")
        >>> p("x")
        >>> p("y")
        (None, Input(s='y', i=0))
        >>> p("z")
        (None, Input(s='z', i=0))
        """
        @Parser
        def call(s):
            if self(s) is None:
                return (None, s)
        return call
    
    def map(self, f):
        """
        Transform result

        >>> p = (tag("x") * tag("y")).map(list)
        >>> p("xy")
        (['x', 'y'], Input(s='xy', i=2))
        """
        @Parser
        def call(s):
            if (r := self(s)):
                (x, s) = r
                return (f(x), s)
        return call
    
    def __getitem__(self, ix):
        """
        Index result

        >>> p1 = (tag("x") * tag("y"))[0]
        >>> p1("xy")
        ('x', Input(s='xy', i=2))
        >>> p2 = (tag("x") * tag("y"))[1]
        >>> p2("xy")
        ('y', Input(s='xy', i=2))
        >>> p1("yx")
        >>> p1("x")
        >>> p1("y")
        """
        return self.map(lambda x: x[ix])
    
    def __lshift__(self, other):
        """
        Ignore right

        >>> p = tag("x") << tag("y")
        >>> p("xy")
        ('x', Input(s='xy', i=2))
        >>> p("yx")
        >>> p("x")
        >>> p("y")
        """
        return (self * other)[0]
    
    def __rshift__(self, other):
        """
        Ignore left

        >>> p = tag("x") >> tag("y")
        >>> p("xy")
        ('y', Input(s='xy', i=2))
        >>> p("yx")
        >>> p("x")
        >>> p("y")
        """
        return (self * other)[1]
    
    def many0(self):
        """
        Like regex *

        >>> p = tag("x").many0()
        >>> p("")
        ([], Input(s='', i=0))
        >>> p("x")
        (['x'], Input(s='x', i=1))
        >>> p("xx")
        (['x', 'x'], Input(s='xx', i=2))
        >>> p("yx")
        ([], Input(s='yx', i=0))
        """
        @Parser
        def call(s):
            xs = []
            while (r := self(s)):
                (x, s) = r
                xs.append(x)
            return (xs, s)
        return call
    
    def many1(self):
        """
        Like regex +

        >>> p = tag("x").many0()
        >>> p("")
        >>> p("x")
        (['x'], Input(s='x', i=1))
        >>> p("xx")
        (['x', 'x'], Input(s='xx', i=2))
        >>> p("yx")
        """
        @Parser
        def call(s):
            xs = []
            if (r := self(s)):
                (x, s) =  r
                xs = [x]
                while (r := self(s)):
                    (x, s) = r
                    xs.append(x)
                return (xs, s)
        return call
    
    def __pow__(self, other):
        """
        self separated by (and possibly ended by) other
        
        >>> p = tag("x") ** (ws * tag(",") * ws)
        >>> p("x, x, x")
        (['x', 'x', 'x'], Input(s='x, x, x', i=7))
        >>> p("x, x, x,")
        (['x', 'x', 'x'], Input(s='x, x, x,', i=8))
        >>> p("x ,x ,x")
        (['x', 'x', 'x'], Input(s='x ,x ,x', i=7))
        >>> p("x")
        (['x'], Input(s='x', i=1))
        >>> p("x ,")
        (['x'], Input(s='x ,', i=3))
        >>> p("")
        ([], Input(s='', i=0))
        """
        @Parser
        def call(s):
            xs = []
            while (r := self(s)):
                (x, s) = r
                xs.append(x)
                if (r := other(s)):
                    (_, s) = r
                else:
                    break
            return (xs, s)
        return call
    
    def string(self):
        """
        Get the matched string as a result

        >>> p = tag("x").many0().string()
        >>> p("")
        >>> p("x")
        ((['x'], 'x'), Input(s='x', i=1))
        >>> p("xx")
        ((['x', 'x'], 'xx'), Input(s='xx', i=2))
        >>> p("yx")
        """
        @Parser
        def call(s):
            if (r := self(s)):
                (x, s1) = r
                return ((x, s.curr(s1.i)), s1)
        return call
    
    def span(self):
        """
        Get the [start, stop) of the match

        >>> p = tag("x").many0().span()
        >>> p("")
        >>> p("x")
        ((['x'], (0, 1)), Input(s='x', i=1))
        >>> p("xx")
        ((['x', 'x'], (0, 2)), Input(s='xx', i=2))
        >>> p("yx")
        """
        @Parser
        def call(s):
            if (r := self(s)):
                (x, s1) = r
                return ((x, (s.i, s1.i)), s1)
        return call
    
    def opt(self):
        """
        Like regex ?

        >>> p = tag("x").opt()
        >>> p("x")
        ('x', Input(s='x', i=1))
        >>> p("y")
        (None, Input(s='y', i=0))
        >>> p("z")
        (None, Input(s='z', i=0))
        """
        return -self + self
    
    def starmap(self, f):
        return self.map(lambda xs: f(*xs))

def tag(m):
    """
    Parse the prefix exactly matching m

    >>> tag("x")("x")
    ('x', Input(s='x', i=1))
    >>> tag("x")("y")
    """
    @Parser
    def call(s):
        if s.curr(len(m)) == m:
            return (m, s.advance(len(m)))
    return call

def pred(p):
    """
    Parse one character matching the predicate

    >>> pred(str.isalpha)("a")
    ('a', Input(s='a', i=1))
    >>> pred(str.isalpha)("9")
    >>> pred(str.isdigit)("9")
    ('9', Input(s='9', i=1))
    >>> pred(str.isdigit)("a")
    """
    @Parser
    def call(s):
        if p(s.curr()):
            return (s.curr(), s.advance())
    return call

alpha = pred(str.isalpha)
alnum = pred(str.isalnum)
digit = pred(str.isdigit)
space = pred(str.isspace)
ws = space.many0()