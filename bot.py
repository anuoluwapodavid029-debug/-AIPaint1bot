"""
AIPaint1bot - A Telegram bot for AI-powered image generation
Uses Google Gemini AI to generate images from text descriptions
Ready for deployment on Railway using GitHub
"""

import os
import sys
import logging
import io
import requests
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
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

if not BOT_TOKEN:
    print("❌ BOT_TOKEN is not set in environment variables")
    sys.exit(1)

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY is not set in environment variables")
    sys.exit(1)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

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

# Available aspect ratios
ASPECT_RATIOS = {
    "1:1": "1:1",
    "16:9": "16:9",
    "9:16": "9:16",
    "4:3": "4:3",
    "3:4": "3:4"
}

# Available art styles
ART_STYLES = {
    "photorealistic": "Photorealistic",
    "anime": "Anime/Manga",
    "oil_painting": "Oil Painting",
    "watercolor": "Watercolor",
    "sketch": "Sketch/Drawing",
    "3d_render": "3D Render",
    "cinematic": "Cinematic",
    "abstract": "Abstract"
}

# User session storage (in-memory, for Railway deployment)
user_sessions = {}


def get_gemini_model():
    """Get Gemini model instance"""
    return genai.GenerativeModel('gemini-2.0-flash-exp-image-generation')


async def generate_image_with_gemini(prompt: str, aspect_ratio: str = "1:1") -> tuple:
    """
    Generate an image using Gemini AI
    
    Args:
        prompt: Text description of the image
        aspect_ratio: Aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4)
    
    Returns:
        Tuple of (success, image_data_or_error_message)
    """
    try:
        # Generate image using Gemini
        model = genai.GenerativeModel('gemini-2.0-flash-exp-image-generation')
        
        # Construct the full prompt with style and aspect ratio
        full_prompt = f"{prompt} - Generate a high-quality image in {aspect_ratio} aspect ratio."
        
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 0,
                "max_output_tokens": 2048,
            }
        )
        
        # Extract image from response
        if hasattr(response, '_result') and hasattr(response._result, 'candidates'):
            candidate = response._result.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        mime_type = part.inline_data.mime_type
                        image_data = part.inline_data.data
                        return True, (image_data, mime_type)
        
        return False, "No image generated. Please try a different prompt."
        
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
        "Welcome to **AIPaint1bot** - your AI art generator!\n\n"
        "📌 **How it works:**\n"
        "1. Use the menu below to select options\n"
        "2. Enter your image description\n"
        "3. AI will generate your image!\n\n"
        "📊 **Commands:**\n"
        "/start - Show this menu\n"
        "/generate - Generate an image\n"
        "/settings - Configure settings\n"
        "/help - Get help\n"
        "/about - Bot information\n"
        "/support - Get support"
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
        "⚡ AI Model: `Google Gemini 2.0 Flash`\n"
        "📅 Status: ✅ **Online**\n\n"
        "🔹 **Features:**\n"
        "• AI-powered image generation\n"
        "• Multiple aspect ratios\n"
        "• Various art styles\n"
        "• User-friendly interface\n"
        "• Production-ready for Railway\n\n"
        f"💡 **Created for:** @{BOT_NAME}"
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /support command"""
    support_text = (
        "📞 **Support**\n\n"
        "For help or questions:\n"
        "• Use /help for guidance\n"
        "• Contact the bot admin\n\n"
        "📚 **Useful Resources:**\n"
        "• Google Gemini AI: https://ai.google.dev/\n"
        "• Telegram Bot API: https://core.telegram.org/bots"
    )
    await update.message.reply_text(support_text, parse_mode="Markdown")


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /generate command"""
    user_id = update.effective_user.id
    
    # Initialize session for this user
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "aspect_ratio": "1:1",
            "style": "photorealistic",
            "waiting_for_prompt": False
        }
    
    user_sessions[user_id]["waiting_for_prompt"] = True
    
    await update.message.reply_text(
        "🎨 **Image Generation Started!**\n\n"
        "Please describe the image you want to generate.\n"
        "Be specific for better results!\n\n"
        "📝 **Example:** 'A futuristic city at sunset with neon lights, cyberpunk style'\n\n"
        "🔧 Use /settings to change aspect ratio or style.",
        parse_mode="Markdown"
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "aspect_ratio": "1:1",
            "style": "photorealistic",
            "waiting_for_prompt": False
        }
    
    current_ratio = user_sessions[user_id].get("aspect_ratio", "1:1")
    current_style = user_sessions[user_id].get("style", "photorealistic")
    
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
            "style": "photorealistic",
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
            [InlineKeyboardButton("📸 Photorealistic", callback_data="style_photorealistic")],
            [InlineKeyboardButton("🎨 Anime/Manga", callback_data="style_anime")],
            [InlineKeyboardButton("🖼️ Oil Painting", callback_data="style_oil_painting")],
            [InlineKeyboardButton("💧 Watercolor", callback_data="style_watercolor")],
            [InlineKeyboardButton("✏️ Sketch/Drawing", callback_data="style_sketch")],
            [InlineKeyboardButton("🎮 3D Render", callback_data="style_3d_render")],
            [InlineKeyboardButton("🎬 Cinematic", callback_data="style_cinematic")],
            [InlineKeyboardButton("🌀 Abstract", callback_data="style_abstract")],
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
            "style": "photorealistic",
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
    style = user_sessions[user_id].get("style", "photorealistic")
    
    # Build enhanced prompt
    style_prompts = {
        "photorealistic": "photorealistic, highly detailed",
        "anime": "anime style, manga style",
        "oil_painting": "oil painting style, artistic",
        "watercolor": "watercolor painting style",
        "sketch": "sketch style, pencil drawing",
        "3d_render": "3D render, CGI, detailed",
        "cinematic": "cinematic style, movie scene",
        "abstract": "abstract art style"
    }
    
    style_prompt = style_prompts.get(style, "")
    enhanced_prompt = f"{text} - {style_prompt}" if style_prompt else text
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ **Generating your image...**\n\n"
        f"📐 Aspect Ratio: `{aspect_ratio}`\n"
        f"🎨 Style: `{style}`\n\n"
        "This may take a few seconds.",
        parse_mode="Markdown"
    )
    
    # Generate the image
    success, result = await generate_image_with_gemini(enhanced_prompt, aspect_ratio)
    
    if success:
        image_data, mime_type = result
        await processing_msg.delete()
        
        # Send the generated image
        await update.message.reply_photo(
            photo=image_data,
            caption=(
                f"✅ **Image Generated!**\n\n"
                f"📝 **Prompt:** `{text}`\n"
                f"🎨 **Style:** `{style}`\n"
                f"📐 **Aspect Ratio:** `{aspect_ratio}`\n\n"
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
    logger.info(f"🤖 AI Model: Gemini 2.0 Flash")
    
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("support", support_command))
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
