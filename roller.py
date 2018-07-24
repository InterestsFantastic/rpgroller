#!/usr/bin/python2

'''Rolls dice using the format you may see in a tabletop RPG, e.g. '3d6'.

roller.roll() does a single roll.
roller.Roller stores the results of rolls and delivers output.
When called using argv, one roll will be performed and output will be to STDOUT as a string.


#Roll Description String Format:
 - 1d6  Rolls a dice with 6 sides
 - d6   Same
 - 12d4 Sum of twelve d4 results
 - 4d6kh3   Rolls 4d6 and returns the sum of the highest three dice
 - 4d6kl3   ...lowest
 - 2d6+2    Sum of 2d6 and 2
 - 2d6-1    Sum of 2d6 and -1
 - 3d8*10   Product of 3d8 and 10
 - 3d6rr2   Rolls 3d6 but rerolls any 2's or below
 - 3d6rr2o  Rerolls only once per die
 - 6d10>7   Counts the number of rolls that meet or exceed 7
 - d6+1<3   Counts the number of rolls (adding 1 to each die) that exceed 6
 - 6d10>7s  Counts rolling a 10 (the maximum roll) as two successes instead of 1 ("Specialization" from V20)
 - 6d10>7b  Rolling a 1 now counts as -1 success
 - 6d10>7sb Works
 - 6d10>7sbc    Cancels the effects of a max roll (necessarily only important in rolls with 's')

_This does not count a success by the best roll necessarily. 's' rolls only work for '>' rolls. Roll descriptions
are not case sensitive._


#TODO:
 - FIX DIFFICULTY CHECKS!
 - Give this a version number, ideally automated through a git client.
 - Add automated .md from docstring
 - Take more vars through argv and document this feature properly.
 - Make the pattern full to cover all valid rolls and assert that it matches perfectly.
 - Convert the docstrings to markdown for github
 - ',' to make multiple rolls?
 - Maybe generalize some of the success checking for other programs?
 - Generalize modifying by string.
'''

_DEBUG = False
_TESTS = False
_UPDATE_DOCSTRING_OUTPUT = False
##_DEBUG = True
_TESTS = True
_UPDATE_DOCSTRING_OUTPUT = True

import re, random
random.seed()

_PATTERN = r'\d*d\d+[*x+-]?\d*'
_COMPILED = re.compile(_PATTERN, re.IGNORECASE)


# -------Tests-----------------------------------------


def _tests():
    _test_rollstrings()
    _test_rolls()

def _test_rolls():
    test = Roller('3d6rr2o', verbose=True)
    for n in range(6):
        test.roll()
    test.newroll('3d8*10')
    test.roll()
    test.newroll('6d10>7sbc')
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


# ------Functions------------------------------------------------


def _parse(rollstr):
    '''Parses a roll description.'''
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
        mod_str, mod_val = m.group()[0], int(m.group()[1:])
    else:
        mod_str = None
        mod_val = None

    # Keep high or low dice.
    keep = None
    keepdice = None
    pat = re.compile(r'K[HL]\d+')
    m = pat.search(up)
    if m:
        keep = m.group()[1]
        keepdice = int(m.group()[2:])
        assert keepdice > 0 and keepdice <= numdice

    # Find difficulty, and whether max rolls are double successes
    doubles = None
    botches = None
    cancel_apex = None
    difficulty = None
    diffdir = None
    pat = re.compile(r'[><]\d+[SBC]*')
    m = pat.search(up)
    if m:
        if 'S' in m.group(): doubles = True
        if 'B' in m.group(): botches = True
        if 'C' in m.group(): cancel_apex = True
        diffdir = m.group()[0]

        if cancel_apex:
            assert botches is not None
            assert doubles is not None
            assert diffdir == '>'
        assert not (doubles is True and diffdir == '<')
        
        # gathering numbers only
        difficulty = int(''.join([x for x in m.group()[1:] if x not in 'SBC']))
        
    return numdice, dicesides, mod_str, mod_val, reroll, once, keep, keepdice, difficulty, diffdir, doubles, botches, cancel_apex


# DIFFICULTY CHECKS DO NOT WORK PROPERLY!
def roll(rolldesc='1d20', min1=None, verbose=False):
    '''Returns the result of a dice roll.

    min1 flags a floor of 1 on the result of a roll. It defaults to True if you aren't doing a difficulty check, and false if you are.

    verbose flagged True returns the result, the individual dice rolls that made it (in the case of multiple dice), and the rolldesc.
    '''
    
    numdice, dicesides, mod_str, mod_val, reroll, once, keep, keepdice, difficulty, diffdir, doubles, botches, cancel_apex = _parse(rolldesc)
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
            if mod_str == "+":
                return something + mod_val
            elif mod_str == "-":
                return something - mod_val
            elif mod_str == "*":
                return something * mod_val

    #fix for specialized roll where max roll = 2x successes    
    def count_successes():
        successes = 0
        for r in rolls:
            if r == dicesides and doubles:
                successes += 1
            if mod_str is None:
                if r >= difficulty:
                    successes += 1
            else:
                if modsomething(r) >= difficulty: 
                    successes += 1                
        return successes
    
    if mod_str is not None:
        if difficulty is not None:
            result = count_successes()
        else:
            result = modsomething(sum(rolls))
    else:
        if difficulty is not None:
            result = count_successes()
        else:
            result = sum(rolls)
            
    if result < 1 and min1:
        result = 1

    if verbose:
        return result, origrolls, rolldesc
    else:
        return result
    

# ------Objects------------------------------------------------


##CURRENTLY THIS DOESN'T HANDLE VERBOSITY
class OutTerm:
    '''Default output object, which prints to terminal.'''
    
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
    '''Rolls dice, stores results, produces output.'''
    
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
        '''Assigns new rolldesc. Does not roll.'''
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


# ------Execution-------------------------------------


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        print roll(sys.argv[1])
    else:
        if _TESTS: _tests()
        if _UPDATE_DOCSTRING_OUTPUT:
            pass
