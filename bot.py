import io
import os
import random
import time
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Google Drive API imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
SUBFOLDER_ID_FOXES = os.getenv('SUBFOLDER_ID_FOXES')
SUBFOLDER_ID_TURTLES = os.getenv('SUBFOLDER_ID_TURTLES')

# Set up intents and bot instance
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Google Drive Authentication setup
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    

    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands globally.")

# REUSABLE HELPER FUNCTION
async def send_random_image_from_folder(interaction: discord.Interaction, folder_id: str):
    await interaction.response.defer()

    try:
        service = get_drive_service()

        # Query files specifically inside this folder ID
        query = f"'{folder_id}' in parents and (mimeType contains 'image/') and trashed = false"
        results = service.files().list(
            q=query, pageSize=100, fields="files(id, name)"
        ).execute()
        files = results.get('files', [])

        if not files:
            await interaction.followup.send("No pictures found in this folder!", ephemeral=True)
            return

        # Pick and download a random file
        chosen_file = random.choice(files)
        request = service.files().get_media(fileId=chosen_file['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        discord_file = discord.File(fh, filename=chosen_file['name'])
        await interaction.followup.send(file=discord_file)

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

@bot.tree.command(name="fox", description="Gets a random picture of a fox.")
async def pica(interaction: discord.Interaction):
    await send_random_image_from_folder(interaction, SUBFOLDER_ID_FOXES)

@bot.tree.command(name="turtle", description="Gets a random picture of a turtle.")
async def picb(interaction: discord.Interaction):
    await send_random_image_from_folder(interaction, SUBFOLDER_ID_TURTLES)

@bot.tree.command(name="ping", description="Measures the bot's connection latency.")
async def ping(interaction: discord.Interaction):
    start_time = time.perf_counter()
    await interaction.response.send_message("Pinging...")
    response_latency = (time.perf_counter() - start_time) * 1000
    websocket_latency = bot.latency * 1000

    await interaction.edit_original_response(
        content=(
            f"🏓 Pong!\n"
            f"Response latency: `{response_latency:.0f} ms`\n"
            f"WebSocket latency: `{websocket_latency:.0f} ms`"
        )
    )


bot.run(TOKEN)