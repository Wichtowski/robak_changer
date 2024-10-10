blacklist = open('blacklist.csv', 'r').read().split('\n')
    
kiss = [
    "{zao} says that :flag_pt: ronaldo :fire: > :flag_ar: messi :x: and {user} agrees :+1:",
    "{user} gives {zao} a soft kiss :kiss:",
    "{user} plants a gentle kiss on {zao}'s cheek :heartbeat:",
    "{zao} messi gol! :goal: ... {user} is not impressed :unamused:",
    "{zao} zostaje zabity tępym narzędziem przez {user} :hammer:",
    "{user} gives {zao} you a quick peck on the forehead :heartpulse:",
    "{user} shares a loving kiss with {zao} :heart:",
    "{zao} gently kisses {user} hand :lips:",
    "{zao} ty draniu :broken_heart: :sob: {user}",
    "{user} is gonna touch you {zao} :palm_up_hand:",
    "{user} kisses {zao} warmly :kissing_heart:",
    "{user} dreams about {zao} without a shirt :sweat_drops::sweat_drops::sweat_drops:",
    "{user} wali spuche na {zao} :face_with_spiral_eyes:",
    "{user} hugs {zao} tightly :hugs:",
    "{user} and {zao} share a secret smile :smirk:",
    "{user} winks at {zao} :wink:",
    "{user} and {zao} dance together :dancer::man_dancing:",
    "{user} and {zao} share a moment of silence :shushing_face:",
    "{user} and {zao} stroke together :joy:",
]

menu = "### !robak command_name\n" \
        "> **helpme**: Get help\n" \
        "> **generate** Generate me a new nickname!\n" \
        "> **add** Adds a new nick to the list\n" \
        "> **remove** Remove a nickname\n" \
        "> **setlang** Set language\n" \
        "> **all** List all nicknames\n" \
        "> **last** List last 10 nicknames\n" \
        "> **endorsed** List most endorsed nicknames\n" \
        "> **zao** <- love this guy he a fren\n" \
        "> **kiss** :flushed:\n" \
        "> **?**: More\n"

helpme = """### _!robak_ command_name\n
```
helpme   | Get help
generate | Generate a new nickname!
add      | Add a new nickname to the list
remove   | Remove a nickname from the list
setlang  | Set the preferred language
all      | List all nicknames
last     | List the last 10 nicknames
endorsed | List the most endorsed nicknames
zao      | Love this guy, he's a fren!
kiss     | :flushed: Send a kiss!
?        | Get more information```"""

country_codes = [
    "pl",  # Polish
    "en",  # English
    "fr",  # French
    "de",  # German
    "jp",  # Japanese
    "in",  # Indian
    "cn",  # Chinese
    "sp",  # Spanish
]
