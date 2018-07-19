#!/usr/bin/python2
'''Rolls dice using the format you may see in a tabletop RPG, e.g. '3d6'.

Roll Description String Format:
    1d6         Rolls a dice with 6 sides
    d6          Same
    12d4        Sum of twelve d4 results
    4d6kh3      Rolls 4d6 and returns the sum of the highest three dice.
    4d6kl3      ...lowest
    2d6+2       Sum of 2d6 and 2
    2d6-1       Sum of 2d6 and -1
    3d8*10      Product of 3d8 and 10

Improvements Required:
    -ask reddit if it's necessary to protect the _PATTERN name, etc.

    -Add success counts vs a difficulty, including max roll = 2 successes
    -Add rerolling (reroll 1's, etc. by default reroll low but potentially also reroll high)

    -make sure that all kinds of stuff fails that should fail will fail in the testing area.
'''

_DEBUG = False
_TESTS = False
##_DEBUG = True
_TESTS = True

import re, random
random.seed()

_PATTERN = r'\d*d\d+[*x+-]?\d*'
_COMPILED = re.compile(_PATTERN, re.IGNORECASE)


# -------TESTING AREA-----------------------------------------


def _tests():
    _test_rollstrings()
    _test_rolls()

def _test_rolls():
    test = Roller('3d6')
    for n in range(6):
        test.roll()
    test.newroll('3d8*10')
    test.roll()
    test.display('lines')
    
def _test_rollstrings():
    assert _COMPILED.match('d20')
    assert _COMPILED.match('D6')
    assert _COMPILED.match('d6+1')
    assert _COMPILED.match('d6-1')
    assert _COMPILED.match('2d6*10')
    assert _COMPILED.match('2d6x10')
    # I don't know if this is a bug or a feature below
    assert _COMPILED.match('D20aa234234')
    assert len(_COMPILED.match('D20aa234234').group()) == len('D20') 
    assert not _COMPILED.match('20D')
    assert not _COMPILED.match('da20')
    assert not _COMPILED.match('ad20')
##    assert not _COMPILED.match('2d6x*-10') #Currently this passes, which it shouldn't.


# ------FUNCTIONS------------------------------------------------


def _parse(rollstr):
    assert _COMPILED.match(rollstr)
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
    '''Returns the result of a dice roll.

    min1 flags a floor of 1 on the result of a roll.

    verbose flagged True returns the result, the individual dice rolls that made it (in the case of multiple dice), and the rolldesc.
    '''
    
    numdice, dicesides, keepdice, modify = _parse(rolldesc)

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
    '''A default output object, which prints to terminal.
        
    CURRENTLY THIS DOESN'T HANDLE VERBOSITY.
    '''
    
    def __init__(self, results=None, meth='string', verbose=False):
        self.verbose = verbose
        self.meth = meth
        self.results = results

    def display(self, meth=None, verbose=None, ):
        '''Outputs to terminal.

        'string' prints results as a string.

        'lines' prints one result per line.
        '''
        assert self.results is not None
        if meth is None: meth = self.meth
        if verbose is None: verbose = self.verbose
        
        if meth == 'string':
            print self.results
        elif meth == 'lines':
            for n in self.results:
                print n

                
class Roller:
    '''Rolls dice and stores results.'''
    
    def __init__(self, rolldesc='1d20', min1=True, verbose=False, out=OutTerm):
        # the min1 flag indicates that the lowest result of any roll (sum of all dice) is 1.
        self.min1 = min1
        self.verbose = verbose
        self.rolldesc = rolldesc
        self.results = []
        self.out = out
        self.initout()

    def roll(self):
        '''Rolls dice according to current rolldesc and appends to results.'''
        self.results.append(roll(self.rolldesc, self.min1, self.verbose))
    
    def newroll(self, rolldesc):
        '''Assigns new rolldesc.'''
        self.rolldesc = rolldesc
    
    def display(self, *args):
        '''Pass through method to displays output by calling self.out.display().'''
        if len(args) != 0:
            self.out.display(*args)
        else:
            self.out.display()

    def initout(self, *args):
        '''Pass through method to initialize your output object. Default is good values for OutTerm'''
        if len(args) == 0:
            self.out = self.out(self.results)
        else:
            self.out = self.out(*args)


# ------EXECUTION-------------------------------------


if __name__ == '__main__':
    if _TESTS: _tests()
