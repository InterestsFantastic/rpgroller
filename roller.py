#!/usr/bin/python3
'''Rolls dice using the format you may see in a tabletop RPG, e.g. '3d6'.

roll() does a single roll.
When called using argv, one roll will be performed and output will be to STDOUT as a string.


### Roll Description String Format:
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
 - 6d10>7=4 Returns 1 if 4 or more successes are achieved, 0 if not.
 - 6d10>7sb=4 Same but returns -1 if the number of successes is negative (a botch in V20)
 
This does not count a success by the best roll necessarily. 's' rolls only work for '>' rolls. Roll descriptions
are not case sensitive. If min1 is true and the roll is a difficulty check the script will intentionally crash.


### TODO:
 - give more depth to argv
 - Rename most vars to PEP8 if not already there?
 - fix _PATTERN: Make the pattern full to cover all valid rolls and assert that it matches perfectly.
 - ',' to make multiple rolls? Maybe use a list vs a string?
 - Fate/Fudge dice.
 - Exploding dice.

'''

_DEBUG = False
_TESTS = False
_DOCUMENT = False
##_DEBUG = True
_TESTS = True
##_DOCUMENT = True

import re, random
random.seed()

_PATTERN = r'\d*d\d+[*x+-]?\d*'
_COMPILED = re.compile(_PATTERN, re.IGNORECASE)


# -------Tests-----------------------------------------


def _tests():
    _test_rollstrings()
    _test_rolls()

def _test_rolls():
    print(roll('2d6'))
   
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
    reroll = False
    if m:
        m = m.group()[2:]
        if m[-1] == 'O': once = True 
        reroll = int(m[:-1]) if once else int(m)
    assert reroll is False or (0 < reroll < dicesides)
    
    # Make function to modify results (+2, *10, etc.).
    pat = re.compile(r'[*X+-]\d+')
    m = pat.search(up)
    if m:
        mod_str, mod_val = m.group()[0], int(m.group()[1:])
    else:
        mod_str = False
        mod_val = False

    # Keep high or low dice.
    keep_str = False
    keep_dice = False
    pat = re.compile(r'K[HL]\d+')
    m = pat.search(up)
    if m:
        keep_str = m.group()[1]
        keep_dice = int(m.group()[2:])
        assert 0 < keep_dice <= numdice

    #Find difficulty, and whether max rolls are double successes.
    doubles = False
    botches = False
    cancel_apex = False
    difficulty = None
    difficulty_direction = False
    difficulty_target = None
    pat = re.compile(r'[><]\d+[SBC]*')
    m = pat.search(up)
    if m:
        if 'S' in m.group(): doubles = True
        if 'B' in m.group(): botches = True
        if 'C' in m.group(): cancel_apex = True
        difficulty_direction = m.group()[0]

        if cancel_apex:
            assert botches and doubles and difficulty_direction == '>'
        assert not (doubles and difficulty_direction == '<')
        
        #Gathering numbers only.
        difficulty = int(''.join([x for x in m.group()[1:] if x not in 'SBC']))

        #Getting target successes only if difficulty is the desired type of roll.
        pat = re.compile(r'=\d+')
        m = pat.search(up)
        if m: difficulty_target = int(m.group()[1:])
        
    return numdice, dicesides, mod_str, mod_val, reroll, once, keep_str, keep_dice, difficulty, difficulty_direction, doubles, botches, cancel_apex, difficulty_target


#designed for sum of rolls or individual rolls
def modify_by_string_operator(mod_str, mod_input, mod_val):
    '''Modifies input using a string operator, e.g. '+', '-', '*'.'''
    if mod_str == "+":
        return mod_input + mod_val
    elif mod_str == "-":
        return mod_input - mod_val
    elif mod_str == "*":
        return mod_input * mod_val


def roll(rolldesc='d20', min1=None, complete_output=False):
    '''Returns the result of a dice roll.

    min1 flags a floor of 1 on the result of a roll. It defaults to True if you aren't doing a difficulty check, and false if you are.

    If complete_output is False it returns a string otherwise it returns a results object.
    '''

    numdice, dicesides, mod_str, mod_val, reroll, once, keep_str, keep_dice, difficulty, difficulty_direction, doubles, botches, cancel_apex, difficulty_target = _parse(rolldesc)
    # Setting defaults
    if min1 is None:
        if difficulty is not None:
            min1 = False
        else:
            min1 = True
    # Making sure min1 and difficulty are in accord.
    assert not (min1 == True and difficulty is not None)

    # Raw rolls generated here.
    origrolls = []
    for n in range(numdice):
        if reroll:
            # When infinite rerolls are allowed, skip the low rolls.
            if not once:
                origrolls.append(random.randint(reroll+1, dicesides))
            else:
                origrolls.append(random.randint(1, dicesides))
                if origrolls[-1] <= reroll:
                    origrolls[-1] = [origrolls[-1],random.randint(1, dicesides)]
        else:
            origrolls.append(random.randint(1, dicesides))

    # Define rolls here and condense.
    if not reroll:
        rolls = list(origrolls)
    else:
        rolls = []
        for n in origrolls:
            try:
                rolls.append(n[1])
            except:
                rolls.append(n)
        # Dereference from origrolls
        rolls = list(rolls)

    if complete_output:
        class RollResult:
            pass
        r = RollResult()
        r.rolldesc = rolldesc
        r.origrolls = list(origrolls)
        r.rolls = list(rolls)
        r.rollparams = {'numdice':numdice, 'dicesides':dicesides, 'mod_str':mod_str, 'mod_val':mod_val, 'reroll':reroll, 'once':once, 'keep_str':keep_str, 'keep_dice':keep_dice, 'difficulty':difficulty, 'difficulty_direction':difficulty_direction, 'doubles':doubles, 'botches':botches, 'cancel_apex':cancel_apex, 'difficulty_target':difficulty_target}

    # Keep highest or lowest keep_dice dice.
    if keep_dice:
        if keep_str == 'H':
            rolls = sorted(rolls)[numdice-keep_dice:]
        else:
            rolls = sorted(rolls)[:keep_dice]
        if complete_output:
            r.kept_rolls = list(rolls)
    
    #How successes are counted depends on elsewhere.
    def count_successes():
        successes = 0
        one_tally = 0
        max_tally = 0
        for r in rolls:
            if r == 1: one_tally += 1
            if r == dicesides: max_tally += 1
            if mod_str:
                r = modify_by_string_operator(mod_str, r, mod_val)
            if difficulty_direction == '>' and r >= difficulty:
                successes += 1
            if difficulty_direction == '<' and r <= difficulty:
                successes += 1
        
        if doubles: successes += max_tally
        if botches: successes -= one_tally
        if botches and cancel_apex and doubles:
            successes -= min(max_tally, one_tally)

        if difficulty_target is None:
            return successes
        if successes >= difficulty_target:
            return 1
        elif botches and successes < 0:
            return -1
        else:
            return 0
    
    if mod_str:
        if difficulty is not None:
            result = count_successes()
        else:
            result = modify_by_string_operator(mod_str, sum(rolls), mod_val)
    else:
        # Note that the individual rolls have already been modified...
        if difficulty is not None:
            result = count_successes()
        else:
            result = sum(rolls)
            
    if result < 1 and min1:
        result = 1

    if complete_output:
        r.result = result
        return r
    else:
        return result
    
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        print(roll(*sys.argv[1:]))
    else:
        if _TESTS:
            _tests()
    if _DOCUMENT:
        import autodocumenter
        autodocumenter.do('roller', 'RPG-Roller')

