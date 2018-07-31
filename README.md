#Functions:#

##modify_by_string_operator(mod_str, mod_input, mod_val)
Modifies input using a string operator, e.g. '+', '-', '*'.

##roll(rolldesc='d20', min1=None, verbose=False)
Returns the result of a dice roll.

    min1 flags a floor of 1 on the result of a roll. It defaults to True if you aren't doing a difficulty check, and false if you are.

    verbose flagged True returns the result, the individual dice rolls that made it (in the case of multiple dice), and the rolldesc.
