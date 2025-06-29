
# This code has been modified by @Safaridev
# Please do not remove this credit

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from info import ADMINS, MAINTENANCE_MODE, LOG_CHANNEL
from Script import script
from database.users_chats_db import db

logger = logging.getLogger(__name__)

# Global variable to track maintenance mode
maintenance_status = MAINTENANCE_MODE

def is_maintenance_mode():
    """Check if maintenance mode is currently enabled"""
    return maintenance_status

def is_admin(user_id):
    """Check if user is an admin"""
    return user_id in ADMINS or str(user_id) in ADMINS

# Maintenance mode filter
def maintenance_filter(_, __, message):
    """Filter to check maintenance mode for non-admin users"""
    if not is_maintenance_mode():
        return True  # Allow all messages when maintenance is off
    
    if message.from_user and is_admin(message.from_user.id):
        return True  # Allow admin access during maintenance
    
    return False  # Block non-admin users during maintenance

# Create filter that passes when NOT in maintenance mode OR user is admin
maintenance_check = filters.create(maintenance_filter)

@Client.on_message(filters.command("maintenance") & filters.user(ADMINS))
async def toggle_maintenance(client, message: Message):
    """Admin command to toggle maintenance mode"""
    global maintenance_status
    
    try:
        if len(message.command) != 2:
            return await message.reply(
                "<b>Usage:</b>\n"
                "• <code>/maintenance on</code> - Enable maintenance mode\n"
                "• <code>/maintenance off</code> - Disable maintenance mode\n"
                f"• <b>Current Status:</b> {'🔧 ON' if maintenance_status else '✅ OFF'}"
            )
        
        action = message.command[1].lower()
        
        if action == "on":
            if maintenance_status:
                return await message.reply("🔧 <b>Maintenance mode is already enabled!</b>")
            
            maintenance_status = True
            
            # Save to database
            await db.set_setting("MAINTENANCE_MODE", True)
            
            # Log the change
            logger.info(f"Maintenance mode enabled by admin {message.from_user.id}")
            
            # Notify log channel
            if LOG_CHANNEL:
                try:
                    await client.send_message(
                        LOG_CHANNEL,
                        f"🔧 <b>Maintenance Mode Enabled</b>\n\n"
                        f"👤 <b>Admin:</b> {message.from_user.mention}\n"
                        f"🆔 <b>User ID:</b> <code>{message.from_user.id}</code>\n"
                        f"⏰ <b>Time:</b> <code>{message.date}</code>"
                    )
                except Exception as e:
                    logger.error(f"Failed to send maintenance log: {e}")
            
            await message.reply(
                "🔧 <b>Maintenance mode has been enabled!</b>\n\n"
                "• Regular users will now see maintenance message\n"
                "• Only admins can use bot commands\n"
                "• Use <code>/maintenance off</code> to disable"
            )
        
        elif action == "off":
            if not maintenance_status:
                return await message.reply("✅ <b>Maintenance mode is already disabled!</b>")
            
            maintenance_status = False
            
            # Save to database
            await db.set_setting("MAINTENANCE_MODE", False)
            
            # Log the change
            logger.info(f"Maintenance mode disabled by admin {message.from_user.id}")
            
            # Notify log channel
            if LOG_CHANNEL:
                try:
                    await client.send_message(
                        LOG_CHANNEL,
                        f"✅ <b>Maintenance Mode Disabled</b>\n\n"
                        f"👤 <b>Admin:</b> {message.from_user.mention}\n"
                        f"🆔 <b>User ID:</b> <code>{message.from_user.id}</code>\n"
                        f"⏰ <b>Time:</b> <code>{message.date}</code>"
                    )
                except Exception as e:
                    logger.error(f"Failed to send maintenance log: {e}")
            
            await message.reply(
                "✅ <b>Maintenance mode has been disabled!</b>\n\n"
                "• Bot is now accessible to all users\n"
                "• All features are restored\n"
                "• Normal operation resumed"
            )
        
        else:
            await message.reply(
                "<b>Invalid option!</b>\n\n"
                "<b>Usage:</b>\n"
                "• <code>/maintenance on</code> - Enable maintenance mode\n"
                "• <code>/maintenance off</code> - Disable maintenance mode"
            )
    
    except Exception as e:
        logger.error(f"Error in maintenance command: {e}")
        await message.reply(f"<b>Error:</b> <code>{str(e)}</code>")

@Client.on_message(filters.incoming & ~maintenance_check)
async def maintenance_handler(client, message: Message):
    """Handle messages during maintenance mode for non-admin users"""
    try:
        if message.from_user:
            # Double check - only send maintenance message to non-admins
            if not is_admin(message.from_user.id):
                # Send maintenance message
                await message.reply(
                    script.MAINTENANCE_MSG,
                    parse_mode=enums.ParseMode.HTML
                )
                
                # Log maintenance access attempt
                logger.info(
                    f"Maintenance access blocked - User: {message.from_user.id}, "
                    f"Username: {message.from_user.username}, "
                    f"Message: {message.text[:50] if message.text else 'Media'}"
                )
    
    except Exception as e:
        logger.error(f"Error in maintenance handler: {e}")

# Function to initialize maintenance status from database
async def initialize_maintenance_status():
    """Initialize maintenance status from database on bot startup"""
    global maintenance_status
    try:
        saved_status = await db.get_setting("MAINTENANCE_MODE", default=MAINTENANCE_MODE)
        maintenance_status = saved_status
        logger.info(f"Maintenance mode initialized: {'ON' if maintenance_status else 'OFF'}")
    except Exception as e:
        logger.error(f"Error initializing maintenance status: {e}")
        maintenance_status = MAINTENANCE_MODE
