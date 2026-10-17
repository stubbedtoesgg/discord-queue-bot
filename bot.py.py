import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# --- DATABASE SETUP ---
conn = sqlite3.connect("game_queue.db")
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        game_name TEXT,
        added_by TEXT
    )
"""
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        game_name TEXT,
        completed_by TEXT
    )
"""
)
conn.commit()
conn.close()


def get_db():
  return sqlite3.connect("game_queue.db")


# --- BOT SETUP ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s).")
  except Exception as e:
    print(e)
  print(f"Logged in as {bot.user} (ID: {bot.user.id})")
  print("------")


# --- SLASH COMMANDS ---


@bot.tree.command(
    name="add_game", description="Add a game to your server's play queue."
)
@app_commands.describe(game="The name of the game you want to add")
async def add_game(interaction: discord.Interaction, game: str):
  conn = get_db()
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO queue (guild_id, game_name, added_by) VALUES (?, ?, ?)",
      (interaction.guild.id, game, interaction.user.display_name),
  )
  conn.commit()
  conn.close()

  embed = discord.Embed(
      title="🎮 Game Added to Queue",
      description=f"**{game}** has been successfully added!",
      color=discord.Color.green(),
  )
  embed.set_footer(text=f"Added by {interaction.user.display_name}")
  await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="queue", description="View the full current game queue."
)
async def view_queue(interaction: discord.Interaction):
  conn = get_db()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, game_name, added_by FROM queue WHERE guild_id = ? ORDER BY id"
      " ASC",
      (interaction.guild.id,),
  )
  rows = cursor.fetchall()
  conn.close()

  embed = discord.Embed(
      title="📋 Current Game Queue", color=discord.Color.blue()
  )

  if not rows:
    embed.description = (
        "The queue is currently empty! Use `/add_game` to add some games."
    )
  else:
    queue_list = []
    for idx, (row_id, game_name, added_by) in enumerate(rows, 1):
      queue_list.append(f"`{idx}.` **{game_name}** *(Added by {added_by})*")
    embed.description = "\n".join(queue_list)

  await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="next_game",
    description="See the next game up in the queue without removing it.",
)
async def next_game(interaction: discord.Interaction):
  conn = get_db()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT game_name, added_by FROM queue WHERE guild_id = ? ORDER BY id ASC"
      " LIMIT 1",
      (interaction.guild.id,),
  )
  row = cursor.fetchone()
  conn.close()

  embed = discord.Embed(
      title="🎯 Up Next", color=discord.Color.gold()
  )
  if row:
    embed.description = (
        f"The next game to play is **{row[0]}** *(Suggested by {row[1]})*"
    )
  else:
    embed.description = "There are no games in the queue!"

  await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="check_off",
    description="Mark the top game as played/completed and remove it from the"
    " queue.",
)
async def check_off(interaction: discord.Interaction):
  conn = get_db()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, game_name, added_by FROM queue WHERE guild_id = ? ORDER BY id"
      " ASC LIMIT 1",
      (interaction.guild.id,),
  )
  row = cursor.fetchone()

  if row:
    row_id, game_name, added_by = row
    # Remove from queue
    cursor.execute("DELETE FROM queue WHERE id = ?", (row_id,))
    # Add to history
    cursor.execute(
        "INSERT INTO history (guild_id, game_name, completed_by) VALUES (?, ?,"
        " ?)",
        (interaction.guild.id, game_name, interaction.user.display_name),
    )
    conn.commit()
    conn.close()

    embed = discord.Embed(
        title="✅ Game Completed!",
        description=(
            f"**{game_name}** has been checked off the queue! Great session!"
        ),
        color=discord.Color.purple(),
    )
    await interaction.response.send_message(embed=embed)
  else:
    conn.close()
    await interaction.response.send_message(
        "The queue is already empty!", ephemeral=True
    )


@bot.tree.command(
    name="remove_game", description="Remove a specific game from the queue."
)
@app_commands.describe(
    game_number="The number of the game in /queue to remove"
)
async def remove_game(interaction: discord.Interaction, game_number: int):
  conn = get_db()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, game_name FROM queue WHERE guild_id = ? ORDER BY id ASC",
      (interaction.guild.id,),
  )
  rows = cursor.fetchall()

  if 1 <= game_number <= len(rows):
    target_id, game_name = rows[game_number - 1]
    cursor.execute("DELETE FROM queue WHERE id = ?", (target_id,))
    conn.commit()
    conn.close()

    embed = discord.Embed(
        title="🗑️ Game Removed",
        description=f"Removed **{game_name}** from the queue.",
        color=discord.Color.red(),
    )
    await interaction.response.send_message(embed=embed)
  else:
    conn.close()
    await interaction.response.send_message(
        "Invalid game number! Check `/queue` for the correct numbers.",
        ephemeral=True,
    )


# --- RUN THE BOT ---
# Replace 'YOUR_BOT_TOKEN_HERE' with your actual bot token from Step 1
bot.run(MTU2MDg3NDE4NTgwOTU5MjM4MQ.GE92Tg.yLOeREYFqiuXh-MYfTMz2K6vg7oHogjPfhrfvY)