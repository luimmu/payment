import discord
import os

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
        return "No payers set yet! Use /addpayer to set up the list."
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

bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await tree.sync()

@tree.command(name="addpayer", description="Add a user to the payer ping list.")
async def addpayer(interaction: discord.Interaction, user: discord.Member):
    user_ids = load_payers()
    if user.id in user_ids:
        await interaction.response.send_message(f"{user.mention} is already in the payer list.", ephemeral=True)
        return
    user_ids.append(user.id)
    save_payers(user_ids)
    await interaction.response.send_message(f"Added {user.mention} to the payer list.", ephemeral=False)

@tree.command(name="removepayer", description="Remove a user from the payer ping list.")
async def removepayer(interaction: discord.Interaction, user: discord.Member):
    user_ids = load_payers()
    if user.id not in user_ids:
        await interaction.response.send_message(f"{user.mention} is not in the payer list.", ephemeral=True)
        return
    user_ids.remove(user.id)
    save_payers(user_ids)
    await interaction.response.send_message(f"Removed {user.mention} from the payer list.", ephemeral=False)

@tree.command(name="listpayers", description="List the current payers who will be pinged.")
async def listpayers(interaction: discord.Interaction):
    user_ids = load_payers()
    if not user_ids:
        await interaction.response.send_message("No payers in the list.", ephemeral=True)
        return
    mentions = " ".join([f"<@{uid}>" for uid in user_ids])
    await interaction.response.send_message(f"Current payers: {mentions}", ephemeral=False)

@tree.command(name="remindnow", description="Send a payment reminder ping to payers.")
async def remindnow(interaction: discord.Interaction):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        msg = await channel.send(get_ping_message())
        await msg.add_reaction(PAYMENT_EMOJI)
        await interaction.response.send_message("Reminder sent to selected users!", ephemeral=False)

@tree.command(name="help", description="Show all payment bot commands.")
async def help_command(interaction: discord.Interaction):
    help_text = (
        "**Payment Bot Slash Commands:**\n"
        "`/addpayer @user` — Add a user to the payer ping list.\n"
        "`/removepayer @user` — Remove a user from the payer ping list.\n"
        "`/listpayers` — List the current payers who will be pinged.\n"
        "`/remindnow` — Send a payment reminder ping to payers.\n"
        "`/checkpayments` — Check who has confirmed their payments.\n"
        "`/help` — Show this help message."
    )
    await interaction.response.send_message(help_text, ephemeral=True)

@tree.command(name="checkpayments", description="Check who has confirmed their payments (reacted with ✅).")
async def checkpayments(interaction: discord.Interaction):
    channel = bot.get_channel(CHANNEL_ID)
    async for message in channel.history(limit=20):
        if message.author == bot.user and "Monthly Reminder" in message.content:
            for reaction in message.reactions:
                if str(reaction.emoji) == PAYMENT_EMOJI:
                    users = [user async for user in reaction.users() if not user.bot]
                    if users:
                        lines = [f"• {user.name}#{user.discriminator}" for user in users]
                        await interaction.response.send_message("**Confirmed Payments:**\n" + "\n".join(lines), ephemeral=False)
                    else:
                        await interaction.response.send_message("No payments confirmed yet.", ephemeral=False)
                    return
    await interaction.response.send_message("No recent reminder found or no reactions yet.", ephemeral=False)

bot.run(TOKEN)
