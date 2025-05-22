import discord
from discord.ext import commands
from discord import app_commands
import pandas as pd
from fuzzywuzzy import fuzz
import os
from dotenv import load_dotenv
import aiofiles

NOT_FOUND_LOG = 'not_found_teams.txt'

# Load .env file
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CLEANED_CSV = 'output_cleaned.csv'

# Helper function: fuzzy match two unit names
def is_fuzzy_match(input_name, candidate_name, threshold=85):
    return fuzz.ratio(input_name.lower(), candidate_name.lower()) >= threshold

# Helper function: fuzzy match 3 user units to 3 defense units
def defense_units_match(user_units, defense_units):
    matched = []
    for user_unit in user_units:
        for def_unit in defense_units:
            if def_unit in matched:
                continue  # skip already matched
            if is_fuzzy_match(user_unit, def_unit):
                matched.append(def_unit)
                break
    return len(matched) == 3

def main():
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix='!', intents=intents)

    df = pd.read_csv(CLEANED_CSV)

    sets = []
    current_set = {'Defense': [], 'Attack': [], 'Notes': ''}
    for _, row in df.iterrows():
        team = row['Team']
        unit = row['Unit']
        notes = row['Notes']

        if team == 'Defense':
            current_set['Defense'].append(unit)
        elif team == 'Attack':
            current_set['Attack'].append(unit)

        if pd.notnull(notes) and notes != '':
            current_set['Notes'] = notes

        if len(current_set['Defense']) == 3 and len(current_set['Attack']) == 3:
            sets.append(current_set)
            current_set = {'Defense': [], 'Attack': [], 'Notes': ''}

    defense_units_list = set()
    for s in sets:
        filtered_units = [unit for unit in s['Defense'] 
                         if unit not in ['Defense Unit 1', 'Defense Unit 2', 'Defense Unit 3']]
        defense_units_list.update(filtered_units)
    all_units = sorted(set(defense_units_list))

    async def unit_autocomplete(interaction: discord.Interaction, current: str):
        matches = [u for u in all_units if current.lower() in u.lower()]
        return [app_commands.Choice(name=unit, value=unit) for unit in matches[:25]]

    @bot.event
    async def on_ready():
        await bot.tree.sync()
        print(f'✅ Bot is online as {bot.user}')

    @bot.tree.command(name="team", description="Find attack team for defense units")
    @app_commands.describe(unit1="Defense Unit 1", unit2="Defense Unit 2", unit3="Defense Unit 3")
    @app_commands.autocomplete(unit1=unit_autocomplete, unit2=unit_autocomplete, unit3=unit_autocomplete)
    async def team(interaction: discord.Interaction, unit1: str, unit2: str, unit3: str):
        user_units = [unit1, unit2, unit3]
        found = False

        for s in sets:
            if defense_units_match(user_units, s['Defense']):
                atk_units = ' | '.join(s['Attack'])
                notes = s['Notes']
                reply = f"**Attack Units:** {atk_units}\n**Notes:**\n{notes}"
                await interaction.response.send_message(reply)
                found = True
                break

        if not found:
            async with aiofiles.open(NOT_FOUND_LOG, mode='a') as f:
                await f.write(f"{unit1}, {unit2}, {unit3}\n")
        await interaction.response.send_message("❌ No matching defense set found. Logged the query.")

    @bot.tree.command(name="notfound", description="Show all unmatched defense unit sets")
    async def notfound(interaction: discord.Interaction):
        if not os.path.exists(NOT_FOUND_LOG):
            await interaction.response.send_message("✅ No unmatched teams logged yet.")
            return

        async with aiofiles.open(NOT_FOUND_LOG, mode='r') as f:
            content = await f.read()

        if not content.strip():
            await interaction.response.send_message("✅ No unmatched teams logged yet.")
        else:
            # Show in code block for clarity
            await interaction.response.send_message(f"📋 **Unmatched Defense Sets:**\n```{content.strip()}```")

    @bot.tree.command(name="clear_not_found", description="Clear all logged unmatched defense teams.")
    async def clear_misses(interaction: discord.Interaction):
        try:
            async with aiofiles.open("not_found_teams.txt", "w") as f:
                await f.write("")  # Truncate file content
            await interaction.response.send_message("🗑️ All unmatched defense entries have been cleared.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to clear the file: {e}")

    bot.run(TOKEN)
if __name__ == '__main__':
    main()
