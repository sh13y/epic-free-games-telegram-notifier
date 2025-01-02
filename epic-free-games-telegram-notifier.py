import os
import requests
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import datetime

# Load environment variables
load_dotenv()

# Telegram bot token and chat ID
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Your chat ID (you can use `getUpdates` to find this)

def fetch_free_games():
    """Fetch free games from the Epic Games Store."""
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return f"Error fetching free games: {e}"

    free_games = []
    for game in data.get("data", {}).get("Catalog", {}).get("searchStore", {}).get("elements", []):
        if game.get("promotions"):
            for promo in game["promotions"].get("promotionalOffers", []):
                for offer in promo.get("promotionalOffers", []):
                    original_price = game.get("price", {}).get("totalPrice", {}).get("originalPrice", 0)
                    discounted_price = game.get("price", {}).get("totalPrice", {}).get("discountPrice", 0)
                    if original_price == 0 and discounted_price == 0:
                        free_games.append({
                            "title": game.get("title"),
                            "url": f"https://store.epicgames.com/en-US/p/{game.get('productSlug')}",
                            "image_url": game.get("keyImages", [{}])[0].get("url", ""),
                            "end_date": offer.get("endDate")
                        })
    return free_games

def format_date(date_string):
    """Format the ISO date string to a human-readable format."""
    try:
        date_obj = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
        return date_obj.strftime("%B %d, %Y at %I:%M %p")  # Example: January 09, 2025 at 04:00 PM
    except ValueError:
        return date_string  # Return the original string if parsing fails

def escape_markdown(text):
    """Escape special characters in MarkdownV2."""
    reserved_chars = r"_*[]()~`>#+-=|{}.!"
    for char in reserved_chars:
        text = text.replace(char, f"\\{char}")
    return text

async def send_telegram_message_with_image(bot_token, chat_id, message, image_url, button_text=None, button_url=None):
    """Send a message to the Telegram bot asynchronously with an image and inline button."""
    bot = Bot(token=bot_token)
    
    # Create inline button if specified
    reply_markup = None
    if button_text and button_url:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=button_text, url=button_url)]
        ])
    
    try:
        # Send the photo with the message
        await bot.send_photo(
            chat_id=chat_id,
            photo=image_url,
            caption=message,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Failed to send message: {e}")

async def main():
    free_games = fetch_free_games()
    if isinstance(free_games, str):  # Error message
        await send_telegram_message_with_image(BOT_TOKEN, CHAT_ID, escape_markdown(free_games), "")
    elif free_games:
        for game in free_games:
            end_date = format_date(game["end_date"])
            message = (
                f"*{escape_markdown(game['title'])}*\n\n"
                f"*Now available for free on the Epic Games Store\\.*\n\n"
                f"Offer valid until: *{escape_markdown(end_date)}*\n\n"
                f"Don't miss out\\."
            )
            await send_telegram_message_with_image(
                BOT_TOKEN,
                CHAT_ID,
                message,
                image_url=game["image_url"],
                button_text="Claim Now",
                button_url=game["url"]
            )
    else:
        await send_telegram_message_with_image(
            BOT_TOKEN, CHAT_ID, escape_markdown("No free games available at the moment. Check back later!"), ""
        )

if __name__ == "__main__":
    asyncio.run(main())
