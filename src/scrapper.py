import re
import os
import json
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError

# Load environment variables
load_dotenv()
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv("API_HASH")
CHANNEL_NAME = os.getenv('CHANNEL_NAME')

def get_last_message_id():
    """Reads last processed message ID from file"""
    try:
        with open('config/last_message_id.txt', 'r') as f:
            return int(f.read())
    except (FileNotFoundError, ValueError):
        return 0

def save_last_message_id(message_id):
    """Saves last processed message ID"""
    os.makedirs('config', exist_ok=True)
    with open('config/last_message_id.txt', 'w') as f:
        f.write(str(message_id))

async def extract_onion_links():
    """Async function to extract .onion links"""
    os.makedirs('outputs', exist_ok=True)
    last_id = get_last_message_id()
    onion_links = []

    try:
        async with TelegramClient('anon', API_ID, API_HASH) as client:
            try:
                messages = await client.get_messages(
                    CHANNEL_NAME,
                    limit=50,
                    min_id=last_id
                )

                for msg in messages:
                    if msg.text:
                        links = re.findall(
                            r'http[s]?://[a-z2-7]{56}\.onion',
                            msg.text
                        )
                        for link in links:
                            onion_links.append({
                                "source": "telegram",
                                "url": link.replace("https://", "http://"),
                                "discovered_at": datetime.now(timezone.utc).isoformat(timespec='milliseconds') + "Z",
                                "context": f"Found in Telegram channel @{CHANNEL_NAME}",
                                "status": "pending"
                            })

                if messages:
                    save_last_message_id(messages[0].id)

            except FloodWaitError as e:
                print(f"⏳ Rate limited! Waiting {e.seconds} seconds...")
                await asyncio.sleep(e.seconds + 5)
                return await extract_onion_links()  # Recursive retry

    except Exception as e:
        print(f"Error: {str(e)}")
        return []

    # Save results
    with open('outputs/onion_links.json', 'w') as f:
        json.dump(onion_links, f, indent=2)

    print(f"Extracted {len(onion_links)} .onion links")
    return onion_links

if __name__ == "__main__":
    asyncio.run(extract_onion_links())