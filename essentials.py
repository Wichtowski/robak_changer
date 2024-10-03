blacklist = open('blacklist.csv', 'r').read().split('\n')


input_actions = ['add', 'remove']
input_exec = []


for action in input_actions:
    input_func = f"""
@bot.CLIENT.command(name='{action}')
async def perform_{action}(ctx):
    try:
        message_content = str(ctx.message.content.split(' ')[2])
        if message_content == '':
            return await ctx.reply("> Umm do I look like I read minds?")
        else:
            if message_content not in blacklist:
                action_result = bot.get_response(response_initialization='{action}', user_input=message_content)
                return await ctx.reply("> " + action_result)    
            else:
                return await ctx.reply("> This value is blacklisted")    
    except Forbidden as e:
        log.write(str(e))
        return await ctx.reply("> I don't have permission to {action}")
    except HTTPException as e:
        log.write(str(e))
        return await ctx.reply(f"> An error occurred while trying to {action}") 
    except Exception as e:
        log.write(str(e))
        return await ctx.reply(bot.get_response('helpme'))
    """
    
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
    "just imagine {user} t h i c c {zao} without a shirt :sweat_drops::sweat_drops::sweat_drops:",
    "{user} wali spuche na {zao} :face_with_spiral_eyes:",
    "{user} hugs {zao} tightly :hugs:",
    "{user} and {zao} share a secret smile :smirk:",
    "{user} winks at {zao} :wink:",
    "{user} and {zao} dance together :dancer::man_dancing:",
    "{user} and {zao} share a moment of silence :shushing_face:",
    "{user} and {zao} laugh together :joy:",
]

helpme = "## !robak \n" \
        "> **helpme**: Get help\n" \
        "> **generate** Generate me a new nickname!\n" \
        "> **add** Adds a new nick to the list\n" \
        "> **remove** Remove a nickname\n" \
        "> **all** List all nicknames\n" \
        "> **last** List last 10 nicknames\n" \
        "> **endorsed** List most endorsed nicknames\n" \
        "> **zao** <- love this guy he a fren\n" \
        "> **kiss** :flushed:\n" \
        "> **?**: More\n"
