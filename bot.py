"""
AIPaint1bot - A Telegram bot for FREE AI-powered image generation
Uses Pollinations.ai API - NO API KEY REQUIRED!
Ready for deployment on Railway using GitHub
"""

import os
import sys
import logging
import requests
from io import BytesIO
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

if not BOT_TOKEN:
    print("❌ BOT_TOKEN is not set in environment variables")
    sys.exit(1)

# Logging setup
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
BOT_NAME = "AIPaint1bot"
BOT_VERSION = "1.0.0"

# Available aspect ratios for Pollinations.ai
ASPECT_RATIOS = {
    "1:1": "1:1",
    "16:9": "16:9",
    "9:16": "9:16",
    "4:3": "4:3",
    "3:4": "3:4"
}

# Available art styles
ART_STYLES = {
    "realistic": "Realistic",
    "anime": "Anime",
    "cartoon": "Cartoon",
    "oil_painting": "Oil Painting",
    "watercolor": "Watercolor",
    "sketch": "Sketch",
    "3d": "3D Render",
    "cinematic": "Cinematic"
}

# User session storage
user_sessions = {}


async def generate_image_free(prompt: str, aspect_ratio: str = "1:1", style: str = "realistic") -> tuple:
    """
    Generate an image using Pollinations.ai API (FREE - No API Key Required)
    
    Args:
        prompt: Text description of the image
        aspect_ratio: Aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4)
        style: Art style
    
    Returns:
        Tuple of (success, image_data_or_error_message)
    """
    try:
        # Map style to Pollinations.ai style parameters
        style_map = {
            "realistic": "photorealistic",
            "anime": "anime",
            "cartoon": "cartoon",
            "oil_painting": "oil-painting",
            "watercolor": "watercolor",
            "sketch": "sketch",
            "3d": "3d-render",
            "cinematic": "cinematic"
        }
        
        pollinations_style = style_map.get(style, "photorealistic")
        
        # Map aspect ratio
        ratio_map = {
            "1:1": "square",
            "16:9": "landscape",
            "9:16": "portrait",
            "4:3": "standard",
            "3:4": "standard-portrait"
        }
        
        pollinations_ratio = ratio_map.get(aspect_ratio, "square")
        
        # Construct the URL with parameters
        # Using Pollinations.ai API (FREE)
        encoded_prompt = requests.utils.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        
        # Add parameters
        params = {
            "width": 1024,
            "height": 1024,
            "seed": "random",
            "nologo": "true"
        }
        
        # Adjust dimensions based on aspect ratio
        if aspect_ratio == "16:9":
            params["width"] = 1024
            params["height"] = 576
        elif aspect_ratio == "9:16":
            params["width"] = 576
            params["height"] = 1024
        elif aspect_ratio == "4:3":
            params["width"] = 1024
            params["height"] = 768
        elif aspect_ratio == "3:4":
            params["width"] = 768
            params["height"] = 1024
        
        # Add style to prompt
        if pollinations_style:
            full_prompt = f"{prompt}, {pollinations_style} style, high quality, detailed"
            encoded_full_prompt = requests.utils.quote(full_prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_full_prompt}"
        
        # Make the request
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            image_data = response.content
            return True, image_data
        else:
            return False, f"Image generation failed with status: {response.status_code}"
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        return False, f"Error generating image: {str(e)}"


# ============ COMMAND HANDLERS ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"✅ Start command from {user.id} ({user.username})")
    
    welcome_text = (
        f"🎨 **Hello {user.first_name}!**\n\n"
        "Welcome to **AIPaint1bot** - your FREE AI art generator!\n\n"
        "✨ **No API keys required!**\n\n"
        "📌 **How it works:**\n"
        "1. Use the menu below\n"
        "2. Enter your image description\n"
        "3. AI will generate your image for FREE!\n\n"
        "📊 **Commands:**\n"
        "/start - Show this menu\n"
        "/generate - Generate an image\n"
        "/settings - Configure settings\n"
        "/help - Get help\n"
        "/about - Bot information"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 Generate Image", callback_data="generate_image")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ])
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "🆘 **Help Guide**\n\n"
        "📖 **How to generate images:**\n\n"
        "1. Use /generate command\n"
        "2. Type your image description\n"
        "3. Wait for the AI to generate your image\n\n"
        "✅ **Tips for good prompts:**\n"
        "• Be specific and detailed\n"
        "• Describe style, colors, mood\n"
        "• Include objects, people, settings\n"
        "• Use adjectives for better results\n\n"
        "❌ **Example bad:** 'a cat'\n"
        "✅ **Example good:** 'a fluffy ginger cat sitting on a windowsill, sunset light, photorealistic, warm colors'\n\n"
        "📊 **Commands:**\n"
        "/start - Main menu\n"
        "/generate - Generate image\n"
        "/settings - Configure settings\n"
        "/help - This message"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command"""
    about_text = (
        f"🤖 **{BOT_NAME}**\n\n"
        f"📌 Version: `{BOT_VERSION}`\n"
        "⚡ AI Model: `Pollinations.ai`\n"
        "💲 **FREE - No API Key Required!**\n"
        "📅 Status: ✅ **Online**\n\n"
        "🔹 **Features:**\n"
        "• FREE AI image generation\n"
        "• No sign-up required\n"
        "• Multiple aspect ratios\n"
        "• Various art styles\n"
        "• User-friendly interface\n"
        "• Production-ready for Railway\n\n"
        f"💡 **Created for:** @{BOT_NAME}"
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /generate command"""
    user_id = update.effective_user.id
    
    # Initialize session for this user
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "aspect_ratio": "1:1",
            "style": "realistic",
            "waiting_for_prompt": False
        }
    
    user_sessions[user_id]["waiting_for_prompt"] = True
    
    await update.message.reply_text(
        "🎨 **Image Generation Started!**\n\n"
        "Please describe the image you want to generate.\n"
        "Be specific for better results!\n\n"
        "📝 **Example:** 'A futuristic city at sunset with neon lights, cyberpunk style'\n\n"
        "🔧 Use /settings to change aspect ratio or style.\n"
        "💲 **FREE - No API Key Required!**",
        parse_mode="Markdown"
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "aspect_ratio": "1:1",
            "style": "realistic",
            "waiting_for_prompt": False
        }
    
    current_ratio = user_sessions[user_id].get("aspect_ratio", "1:1")
    current_style = user_sessions[user_id].get("style", "realistic")
    
    settings_text = (
        f"⚙️ **Settings**\n\n"
        f"📐 **Aspect Ratio:** `{current_ratio}`\n"
        f"🎨 **Art Style:** `{current_style}`\n\n"
        "Select what you want to change:"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📐 Change Aspect Ratio", callback_data="change_ratio")],
        [InlineKeyboardButton("🎨 Change Art Style", callback_data="change_style")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
    ])
    
    await update.message.reply_text(
        settings_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ============ CALLBACK QUERY HANDLERS ============

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline buttons"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "aspect_ratio": "1:1",
            "style": "realistic",
            "waiting_for_prompt": False
        }
    
    if query.data == "generate_image":
        await generate_command(query.message, context)
        await query.message.delete()
    
    elif query.data == "settings":
        await settings_command(query.message, context)
        await query.message.delete()
    
    elif query.data == "help":
        await help_command(query.message, context)
        await query.message.delete()
    
    elif query.data == "back_to_menu":
        await start_command(query.message, context)
        await query.message.delete()
    
    elif query.data == "change_ratio":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("1:1 (Square)", callback_data="ratio_1:1")],
            [InlineKeyboardButton("16:9 (Landscape)", callback_data="ratio_16:9")],
            [InlineKeyboardButton("9:16 (Portrait)", callback_data="ratio_9:16")],
            [InlineKeyboardButton("4:3 (Standard)", callback_data="ratio_4:3")],
            [InlineKeyboardButton("3:4 (Standard Portrait)", callback_data="ratio_3:4")],
            [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")]
        ])
        
        await query.message.reply_text(
            "📐 **Select Aspect Ratio:**",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("ratio_"):
        ratio = query.data.replace("ratio_", "")
        user_sessions[user_id]["aspect_ratio"] = ratio
        await query.message.reply_text(f"✅ Aspect ratio set to: `{ratio}`", parse_mode="Markdown")
        await settings_command(query.message, context)
    
    elif query.data == "change_style":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📸 Realistic", callback_data="style_realistic")],
            [InlineKeyboardButton("🎨 Anime", callback_data="style_anime")],
            [InlineKeyboardButton("🖼️ Oil Painting", callback_data="style_oil_painting")],
            [InlineKeyboardButton("💧 Watercolor", callback_data="style_watercolor")],
            [InlineKeyboardButton("✏️ Sketch", callback_data="style_sketch")],
            [InlineKeyboardButton("🎮 3D Render", callback_data="style_3d")],
            [InlineKeyboardButton("🎬 Cinematic", callback_data="style_cinematic")],
            [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")]
        ])
        
        await query.message.reply_text(
            "🎨 **Select Art Style:**",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("style_"):
        style = query.data.replace("style_", "")
        user_sessions[user_id]["style"] = style
        await query.message.reply_text(f"✅ Art style set to: `{style}`", parse_mode="Markdown")
        await settings_command(query.message, context)


# ============ MESSAGE HANDLERS ============

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages (image generation prompts)"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "aspect_ratio": "1:1",
            "style": "realistic",
            "waiting_for_prompt": False
        }
    
    # Check if user is waiting for a prompt
    if not user_sessions[user_id].get("waiting_for_prompt", False):
        await update.message.reply_text(
            "❓ Use /generate to start image generation or /help for commands.",
            parse_mode="Markdown"
        )
        return
    
    # Get user settings
    aspect_ratio = user_sessions[user_id].get("aspect_ratio", "1:1")
    style = user_sessions[user_id].get("style", "realistic")
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ **Generating your image...**\n\n"
        f"📐 Aspect Ratio: `{aspect_ratio}`\n"
        f"🎨 Style: `{style}`\n\n"
        "This may take a few seconds.",
        parse_mode="Markdown"
    )
    
    # Generate the image
    success, result = await generate_image_free(text, aspect_ratio, style)
    
    if success:
        image_data = result
        await processing_msg.delete()
        
        # Send the generated image
        await update.message.reply_photo(
            photo=BytesIO(image_data),
            caption=(
                f"✅ **Image Generated!**\n\n"
                f"📝 **Prompt:** `{text}`\n"
                f"🎨 **Style:** `{style}`\n"
                f"📐 **Aspect Ratio:** `{aspect_ratio}`\n"
                f"💲 **FREE - No API Key Required!**\n\n"
                f"🔄 Send another description to generate more images!"
            ),
            parse_mode="Markdown"
        )
        
        # Add quick buttons
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎨 Generate More", callback_data="generate_image")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
        ])
        
        await update.message.reply_text(
            "What would you like to do next?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    else:
        await processing_msg.edit_text(
            f"❌ **Failed to generate image:**\n\n{result}\n\nPlease try again with a different description.",
            parse_mode="Markdown"
        )
    
    # Reset waiting state
    user_sessions[user_id]["waiting_for_prompt"] = False


# ============ ERROR HANDLER ============

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")


# ============ MAIN ============

def main():
    """Main entry point"""
    logger.info(f"🚀 Starting {BOT_NAME}...")
    logger.info(f"📌 Version: {BOT_VERSION}")
    logger.info(f"🔧 Debug Mode: {DEBUG_MODE}")
    logger.info(f"🤖 AI Model: Pollinations.ai (FREE - No API Key)")
    
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("generate", generate_command))
        application.add_handler(CommandHandler("settings", settings_command))
        
        # Add message handler for prompts
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Add callback query handler
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Start polling
        logger.info("✅ Bot is running and listening for messages...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise


if __name__ == "__main__":
    main()
