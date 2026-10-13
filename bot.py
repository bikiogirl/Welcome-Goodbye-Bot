# ==========================================
#   Discord Music Bot
#   Created & Maintained by Bikio
#   GitHub: https://github.com/bikiogirl
# ==========================================
"""
╔══════════════════════════════════════════════════════╗
║         Welcome & Goodbye Discord Bot                ║
║  Automatic, beautiful join/leave messages (embeds)   ║
╚══════════════════════════════════════════════════════╝

Features
--------
• Welcome embed with @user mention + @server name when someone joins
• Goodbye embed when someone leaves
• Member count, account age, avatar thumbnail, server icon
• Admin slash commands to configure channels + test the embeds
• Settings are saved in config.json (per server)

Run:  python bot.py
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
print("done!")
# ──────────────────────────────────────────────────────────
# 1. CONFIGURATION
# ──────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

CONFIG_FILE = Path("config.json")

# Colors (Discord-style palette)
COLOR_WELCOME = discord.Color.from_rgb(265, 58, 64)   # purple
COLOR_GOODBYE = discord.Color.from_rgb(265, 58, 64)    #purple (custom Color)

# Emojis / icons (change freely)
ICON_WELCOME = "👋"
ICON_GOODBYE = "😢"
ICON_MEMBERS = "👥"
ICON_CALENDAR = "📅"
ICON_JOINED = "📥"

# Banner images (optional – put a direct image URL or leave None)
WELCOME_BANNER = None   # e.g. "https://i.imgur.com/xxxxx.png"
GOODBYE_BANNER = None


# ──────────────────────────────────────────────────────────
# 2. SIMPLE JSON STORAGE (per guild)
# ──────────────────────────────────────────────────────────
def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


config = load_config()


def get_channel_id(guild_id: int, key: str):
    """key = 'welcome' or 'goodbye'"""
    return config.get(str(guild_id), {}).get(key)


def set_channel_id(guild_id: int, key: str, channel_id: int) -> None:
    config.setdefault(str(guild_id), {})[key] = channel_id
    save_config(config)


# ──────────────────────────────────────────────────────────
# 3. BOT SETUP + INTENTS
# ──────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True          # REQUIRED: join/leave events (Privileged Intent!)

bot = commands.Bot(command_prefix="!", intents=intents)


# ──────────────────────────────────────────────────────────
# 4. EMBED BUILDERS
# ──────────────────────────────────────────────────────────
def build_welcome_embed(member: discord.Member) -> discord.Embed:
    guild = member.guild
    embed = discord.Embed(
        title=f"{ICON_WELCOME} Welcome to {guild.name}!",
        description=(
            f"Welcome {member.mention} to **{guild.name}**! 🎉\n\n"
            f"We're happy to have you here. Make sure to read the rules "
            f"and enjoy your stay!"
        ),
        color=COLOR_WELCOME,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(
        name=f"{ICON_MEMBERS} Member Count",
        value=f"You are member **#{guild.member_count}**",
        inline=True,
    )
    embed.add_field(
        name=f"{ICON_CALENDAR} Account Created",
        value=discord.utils.format_dt(member.created_at, style="R"),
        inline=True,
    )
    if WELCOME_BANNER:
        embed.set_image(url=WELCOME_BANNER)
    if guild.icon:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
        embed.set_footer(text=f"{guild.name} • Welcome", icon_url=guild.icon.url)
    else:
        embed.set_footer(text=f"{guild.name} • Welcome")
    return embed


def build_goodbye_embed(member: discord.Member) -> discord.Embed:
    guild = member.guild
    embed = discord.Embed(
        title=f"{ICON_GOODBYE} A member has left",
        description=(
            f"{member.mention} (**{member.name}**) has left the server :(\n\n"
            f"We hope to see you again someday!"
        ),
        color=COLOR_GOODBYE,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(
        name=f"{ICON_MEMBERS} Members Left",
        value=f"**{guild.member_count}** members",
        inline=True,
    )
    if member.joined_at:
        embed.add_field(
            name=f"{ICON_JOINED} Joined",
            value=discord.utils.format_dt(member.joined_at, style="R"),
            inline=True,
        )
    if GOODBYE_BANNER:
        embed.set_image(url=GOODBYE_BANNER)
    if guild.icon:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
        embed.set_footer(text=f"{guild.name} • Goodbye", icon_url=guild.icon.url)
    else:
        embed.set_footer(text=f"{guild.name} • Goodbye")
    return embed


# ──────────────────────────────────────────────────────────
# 5. EVENTS
# ──────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()  # register slash commands
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="new members 👀")
    )
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_member_join(member: discord.Member):
    channel_id = get_channel_id(member.guild.id, "welcome")
    channel = member.guild.get_channel(channel_id) if channel_id else None
    if channel is None:
        return
    # content=member.mention makes the user actually get pinged
    await channel.send(content=member.mention, embed=build_welcome_embed(member))


@bot.event
async def on_member_remove(member: discord.Member):
    channel_id = get_channel_id(member.guild.id, "goodbye")
    channel = member.guild.get_channel(channel_id) if channel_id else None
    if channel is None:
        return
    await channel.send(embed=build_goodbye_embed(member))


# ──────────────────────────────────────────────────────────
# 6. SLASH COMMANDS (admins only)
# ──────────────────────────────────────────────────────────
@bot.tree.command(name="setwelcome", description="Set the channel for welcome messages")
@app_commands.describe(channel="Channel where welcome messages will be sent")
@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
async def setwelcome(interaction: discord.Interaction, channel: discord.TextChannel):
    set_channel_id(interaction.guild.id, "welcome", channel.id)
    await interaction.response.send_message(
        f"✅ Welcome messages will be sent in {channel.mention}.", ephemeral=True
    )


@bot.tree.command(name="setgoodbye", description="Set the channel for goodbye messages")
@app_commands.describe(channel="Channel where goodbye messages will be sent")
@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
async def setgoodbye(interaction: discord.Interaction, channel: discord.TextChannel):
    set_channel_id(interaction.guild.id, "goodbye", channel.id)
    await interaction.response.send_message(
        f"✅ Goodbye messages will be sent in {channel.mention}.", ephemeral=True
    )


@bot.tree.command(name="testwelcome", description="Preview the welcome message")
@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
async def testwelcome(interaction: discord.Interaction):
    await interaction.response.send_message(
        content=interaction.user.mention,
        embed=build_welcome_embed(interaction.user),
        ephemeral=True,
    )


@bot.tree.command(name="testgoodbye", description="Preview the goodbye message")
@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
async def testgoodbye(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=build_goodbye_embed(interaction.user), ephemeral=True
    )


# ──────────────────────────────────────────────────────────
# 7. START
# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("❌ DISCORD_TOKEN is missing. Create a .env file (see .env.example).")
    bot.run(TOKEN)
