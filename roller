'''NEXT STEPS:
-ask reddit if it's necessary to protect the PATTERN name, etc.

-Add success counts vs a difficulty, including max roll = 2 successes
-Add rerolling (reroll 1's, etc. by default reroll low but potentially also reroll high)

-make sure that all kinds of stuff fails that should fail will fail in the testing area.
-pydoc?
'''

'''Roll Descriptions
        1d6         Rolls a dice with 6 sides
        None        Equivalent to 1d20
        d4          Equivalent to 1d4
        12d4        Sum of twelve d4
        4d6kh3      Rolls 4d6 and returns the sum of the highest three dice.
        4d6kl3      ...lowest
        d4+20       Sum of 1d4 and 20
        d6-1        
        d4*100      The product of 1d4 and 100.
'''

DEBUG = False
TESTS = False
##DEBUG = True
TESTS = True

import re, random
random.seed()

PATTERN = r'\d*d\d+[*x+-]?\d*'
COMPILED = re.compile(PATTERN, re.IGNORECASE)


# -------TESTING AREA-----------------------------------------


def tests():
    test_rollstrings()
    test_rolls()

def test_rolls():
    test = Roller('3d6')
    for n in range(6):
        test.roll()
    test.newroll('3d8*10')
    test.roll()
    test.display('lines')

def test_rollstrings():
    assert COMPILED.match('d20')
    assert COMPILED.match('D6')
    assert COMPILED.match('d6+1')
    assert COMPILED.match('d6-1')
    assert COMPILED.match('2d6*10')
    assert COMPILED.match('2d6x10')
    # I don't know if this is a bug or a feature below
    assert COMPILED.match('D20aa234234')
    assert len(COMPILED.match('D20aa234234').group()) == len('D20') 
    assert not COMPILED.match('20D')
    assert not COMPILED.match('da20')
    assert not COMPILED.match('ad20')
##    assert not COMPILED.match('2d6x*-10') #Currently this passes, which it shouldn't.


# ------FUNCTIONS------------------------------------------------


def parse(rollstr):
    assert COMPILED.match(rollstr)
    up = rollstr.upper()
    
    # Number and sides of dice
    pat = re.compile(r'\d*D\d+')
    m = pat.match(up)
    assert m
    m = m.group().split('D')
    numdice = int(m[0]) if m[0] else 1
    dicesides = int(m[1])
    assert numdice > 0
    assert dicesides > 0

    # Make function to modify results (+2, *10, etc.).
    pat = re.compile(r'[*X+-]\d+')
    m = pat.search(up)
    if m:
        modtype, modval = m.group()[0], int(m.group()[1:])
        if modtype == '+':
            modify = lambda roll: roll + modval
        elif modtype == '-':
            modify = lambda roll: roll - modval
        elif modtype == '*' or modtype == 'X':
            modify = lambda roll: roll * modval
    else:
        modify = None

    # Make function for keeping high or low dice.
    pat = re.compile(r'K[HL]\d+')
    m = pat.search(up)
    if m:
        keepnum = int(m.group()[2:])
        assert keepnum > 0 and keepnum <= numdice
        if m.group()[1] == 'H':
            keepdice = lambda group: sorted(group)[numdice-keepnum:]
        else:
            keepdice = lambda group: sorted(group)[:keepnum]
    else:
        keepdice = None

    return numdice, dicesides, keepdice, modify


def roll(rolldesc='1d20', min1=True, verbose=False):
    numdice, dicesides, keepdice, modify = parse(rolldesc)

    rolls = []
    for n in range(numdice):
        rolls.append(random.randint(1, dicesides))
    origrolls = list(rolls)
    
    if keepdice:
        rolls = keepdice(rolls)

    if modify:
        result = modify(sum(rolls))
    else:
        result = sum(rolls)

    if result < 1 and min1:
        result = 1

    if verbose:
        return result, origrolls, rolldesc
    else:
        return result
    

# ------OBJECTS------------------------------------------------


class OutTerm:
    def __init__(self, results, verbose=False, meth='string'):
        self.results = results
        self.verbose = verbose
        self.meth = meth

    def display(self, meth=None):
        # Currently this doesn't handle verbosity.
        if meth is None:
            meth = self.meth
        if meth == 'string':
            print self.results
        elif meth == 'lines':
            for n in self.results:
                print n

                
class Roller:
    def __init__(self, rolldesc='1d20', min1=True, verbose=False, out=OutTerm):
        # the min1 flag indicates that the lowest result of any roll (sum of all dice) is 1.
        self.min1 = min1
        self.verbose = verbose
        self.rolldesc = rolldesc
        self.results = []
        self.out = out

    def roll(self):
        self.results.append(roll(self.rolldesc, self.min1, self.verbose))
    
    def newroll(self, rolldesc):
        self.rolldesc = rolldesc
    
    def display(self, meth=None):
        self.out(self.results, self.verbose).display(meth)


# ------EXECUTION-------------------------------------


if __name__ == '__main__':
    if TESTS: tests()

