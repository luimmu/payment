import discord
from discord.ext import commands, tasks
import os
import datetime

PAYERS_FILE = "payers.txt"

def load_payers():
    try:
        with open(PAYERS_FILE, "r") as f:
            return [int(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_payers(user_ids):
    with open(PAYERS_FILE, "w") as f:
        for uid in user_ids:
            f.write(f"{uid}\n")

def get_ping_message():
    user_ids = load_payers()
    if not user_ids:
        return "No payers set yet! Use !addpayer @user to set up the list."
    mentions = " ".join([f"<@{uid}>" for uid in user_ids])
    return (
        f"{mentions}\n"
        "💰 **Monthly Reminder**\n"
        f"Please pay **RM 10** for ChatGPT Plus. React with ✅ to confirm."
    )

TOKEN = os.environ['DISCORD_BOT_TOKEN']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
PAYMENT_EMOJI = '✅'

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.command()
async def addpayer(ctx, user: discord.Member):
    user_ids = load_payers()
    if user.id in user_ids:
        await ctx.send(f"{user.mention} is already in the payer list.")
        return
    user_ids.append(user.id)
    save_payers(user_ids)
    await ctx.send(f"Added {user.mention} to the payer list.")

@bot.command()
async def removepayer(ctx, user: discord.Member):
    user_ids = load_payers()
    if user.id not in user_ids:
        await ctx.send(f"{user.mention} is not in the payer list.")
        return
    user_ids.remove(user.id)
    save_payers(user_ids)
    await ctx.send(f"Removed {user.mention} from the payer list.")

@bot.command()
async def listpayers(ctx):
    user_ids = load_payers()
    if not user_ids:
        await ctx.send("No payers in the list.")
        return
    mentions = " ".join([f"<@{uid}>" for uid in user_ids])
    await ctx.send(f"Current payers: {mentions}")

@bot.command()
async def remindnow(ctx):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        msg = await channel.send(get_ping_message())
        await msg.add_reaction(PAYMENT_EMOJI)
        await ctx.send("Reminder sent to selected users!")

@bot.command()
async def help(ctx):
    help_text = (
        "**Payment Bot Commands:**\n"
        "`!addpayer @user` — Add a user to the payer ping list.\n"
        "`!removepayer @user` — Remove a user from the payer ping list.\n"
        "`!listpayers` — List the current payers who will be pinged.\n"
        "`!remindnow` — Send a payment reminder ping to payers.\n"
        "`!help` — Show this help message.\n"
        "`!checkpayments` — Check who has confirmed their payments."
    )
    await ctx.send(help_text)

@bot.command()
async def checkpayments(ctx):
    channel = bot.get_channel(CHANNEL_ID)
    async for message in channel.history(limit=20):
        if message.author == bot.user and "Monthly Reminder" in message.content:
            for reaction in message.reactions:
                if str(reaction.emoji) == PAYMENT_EMOJI:
                    users = [user async for user in reaction.users() if not user.bot]
                    if users:
                        lines = [f"• {user.name}#{user.discriminator}" for user in users]
                        await ctx.send("**Confirmed Payments:**\n" + "\n".join(lines))
                    else:
                        await ctx.send("No payments confirmed yet.")
                    return
    await ctx.send("No recent reminder found or no reactions yet.")


bot.run(TOKEN)
