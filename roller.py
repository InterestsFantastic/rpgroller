#!/usr/bin/python2

# I should check v:tm mechanics to see how  regular 10 is counted in terms of successes and also what creates a botch... is a roll of 1 a success of -1? Etc. Figure it out.

'''Rolls dice using the format you may see in a tabletop RPG, e.g. '3d6'.

Roll Description String Format:
    1d6         Rolls a dice with 6 sides
    d6          Same
    12d4        Sum of twelve d4 results
    4d6kh3      Rolls 4d6 and returns the sum of the highest three dice
    4d6kl3      ...lowest
    2d6+2       Sum of 2d6 and 2
    2d6-1       Sum of 2d6 and -1
    3d8*10      Product of 3d8 and 10
    3d6rr2      Rolls 3d6 but rerolls any 2's or below
    3d6rr2o     Rerolls only once per die
    6d10=7      Counts the number of rolls that meet or exceed 7
    6d10+1>6    Counts the number of rolls (adding 1 to each die) that exceed 6
    6d10=7s     Counts rolling a 10 (the maximum roll) as two successes instead of 1

Improvements Required:
    -Currently only the rolldesc is accepted by sys.argv but it should actually take verbose and min1 (and kwargs if applicable)...
    -more rigourous pattern testing; fail when it should
    -convert the docstrings to markdown for github
'''

_DEBUG = False
_TESTS = False
_UPDATE_DOCSTRING_OUTPUT = False
##_DEBUG = True
_TESTS = True
##_UPDATE_DOCSTRING_OUTPUT = True

import re, random
random.seed()

_PATTERN = r'\d*d\d+[*x+-]?\d*'
_COMPILED = re.compile(_PATTERN, re.IGNORECASE)


# -------TESTING AREA-----------------------------------------


def _tests():
    _test_rollstrings()
    _test_rolls()

def _test_rolls():
    test = Roller('3d6rr2o', verbose=True)
    for n in range(6):
        test.roll()
    test.newroll('3d8*10')
    test.roll()
    test.newroll('6d10+3=7s')
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

    # Rerolling instructions
    pat = re.compile(r'RR\d+O?')
    m = pat.search(up)
    once = False
    reroll = None
    if m:
        m = m.group()[2:]
        if m[-1] == 'O': once = True 
        reroll = int(m[:-1]) if once else int(m)
    assert reroll is None or (reroll > 0 and reroll < dicesides)
    
    # Make function to modify results (+2, *10, etc.).
    pat = re.compile(r'[*X+-]\d+')
    m = pat.search(up)
    if m:
        modifier, modval = m.group()[0], int(m.group()[1:])
    else:
        modifier = None
        modval = None

    # Keep high or low dice.
    pat = re.compile(r'K[HL]\d+')
    m = pat.search(up)
    if m:
        keep = m.group()[1]
        keepdice = int(m.group()[2:])
        assert keepdice > 0 and keepdice <= numdice
    else:
        keep = None
        keepdice = None

    # Find difficulty, and whether max rolls are double successes
    pat = re.compile(r'[=>]\d+s?')
    m = pat.search(up)
    doubles = True if m else None
    pat = re.compile(r'[=>]\d+')
    m = pat.search(up)
    if m:
        if m.group()[0] == '=':
            difficulty = int(m.group()[1:])
        else:
            difficulty = int(m.group()[1:])+1
    else:
        difficulty = None
        
    return numdice, dicesides, modifier, modval, reroll, once, keep, keepdice, difficulty, doubles


def roll(rolldesc='1d20', min1=None, verbose=False):
    '''Returns the result of a dice roll.

    min1 flags a floor of 1 on the result of a roll. It defaults to True if you aren't doing a difficulty check, and false if you are.

    verbose flagged True returns the result, the individual dice rolls that made it (in the case of multiple dice), and the rolldesc.
    '''
    
    numdice, dicesides, modifier, modval, reroll, once, keep, keepdice, difficulty, doubles = _parse(rolldesc)
    if min1 is None:
        if difficulty is not None:
            min1 = False
        else:
            min1 = True
    assert not (min1 == True and difficulty is not None)

    # Because when infinite rerolls are allowed, we don't bother offering a chance of rolling too low,
    # this gathers MOST of the data for the rolls for presentation during verbose output
    origrolls = []
    for n in range(numdice):
        if reroll:
            if not once:
                origrolls.append(random.randint(reroll+1, dicesides))
            else:
                origrolls.append(random.randint(1, dicesides))
                if origrolls[-1] <= reroll:
                    origrolls[-1] = [origrolls[-1],random.randint(1, dicesides)]
        else:
            origrolls.append(random.randint(1, dicesides))

    #define rolls here and condense it
    rolls = []
    for n in origrolls:
        try:
            rolls.append(n[1])
        except:
            rolls.append(n)
    #to dereference from origrolls
    rolls = list(rolls)
    
    #keep highest or lowest keepdice dice.
    if keepdice is not None:
        if keep == 'H':
            rolls = sorted(group)[numdice-keepdice:]
        else:
            rolls = sorted(group)[:keepdice]

    #designed for sum of rolls or individual rolls
    def modsomething(something):
            if modifier == "+":
                return something + modval
            elif modifier == "-":
                return something - modval
            elif modifier == "*":
                return something * modval

    #fix for specialized roll where max roll = 2x successes    
    def countsuccesses():
        successes = 0
        for r in rolls:
            if r == dicesides and doubles:
                successes += 1
            if modifier is None:
                if r >= difficulty:
                    successes += 1
            else:
                if modsomething(r) >= difficulty: 
                    successes += 1                
        return successes
    
    if modifier is not None:
        if difficulty is not None:
            result = countsuccesses()
        else:
            result = modsomething(sum(rolls))
    else:
        if difficulty is not None:
            result = countsuccesses()
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
    
    def __init__(self, rolldesc='1d20', min1=None, verbose=False, out=OutTerm):
        '''the min1 flag indicates that the lowest result of any roll (sum of all dice) is 1.'''
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
            self.out = self.out(self.results, verbose=self.verbose)
        else:
            self.out = self.out(*args)


# ------EXECUTION-------------------------------------


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        print roll(sys.argv[1])
    else:
        if _TESTS: _tests()
        if _UPDATE_DOCSTRING_OUTPUT:
            pass

