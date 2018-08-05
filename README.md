RPG-Roller
==========


Rolls dice using the format you may see in a tabletop RPG, e.g. '3d6'.

roller.roll() does a single roll.
roller.Roller stores the results of rolls and delivers output.
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
 - update autodocumenter to get rid of the self in class methods
 - argv order (roll() order) desc,verbose,min1?
 - Rename most vars to PEP8 if not already there?
 - Automate versioning via git client ideally
 - Make the pattern full to cover all valid rolls and assert that it matches perfectly.
 - ',' to make multiple rolls?
 - Fate/Fudge dice.
 - Exploding dice.
 - Output object should ideally condense output that is set to verbose, but currently that's handled by roll()
 - Write a discord output object.


## Module Functions:

#### modify_by_string_operator(mod_str, mod_input, mod_val)
Modifies input using a string operator, e.g. '+', '-', '*'.

#### roll(rolldesc='d20', min1=None, verbose=False)
Returns the result of a dice roll.
min1 flags a floor of 1 on the result of a roll. It defaults to True if you aren't doing a difficulty check, and false if you are.
verbose flagged True returns the result, the individual dice rolls that made it (in the case of multiple dice), and the rolldesc.


## Classes:

### roller.Roller
Rolls dice, stores results, produces output.

#### Roller.__init__(rolldesc='d20', min1=None, verbose=False, out=_OutTerm)

#### Roller.roll()
Rolls dice according to current rolldesc and appends to results.

#### Roller.newroll(rolldesc)
Assigns new rolldesc. Does not roll.

#### Roller.render(*args)
Pass through method to displays output by calling self.out.render().

#### Roller.initout(*args)
Pass through method to initialize your output object. Default is good values for OutTerm
