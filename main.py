import telebot
from telebot import types
import os
import re
import sqlite3
import time

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID') # Ton ID Telegram pour valider les paiements
bot = telebot.TeleBot(TOKEN)

# --- INITIALISATION BASE DE DONNÉES (Module 0) ---
def init_db():
    conn = sqlite3.connect('faso_art.db')
    cursor = conn.cursor()
    # Table Artistes
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
        (tg_id INTEGER PRIMARY KEY, name TEXT, job TEXT, phone TEXT, 
        video_id TEXT, score INTEGER DEFAULT 0, status TEXT DEFAULT 'actif', 
        is_premium INTEGER DEFAULT 0, referral_code TEXT)''')
    # Table Transactions (Module 5.4)
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions 
        (trans_id TEXT PRIMARY KEY, user_id INTEGER, amount REAL, 
        status TEXT DEFAULT 'EN_ATTENTE', date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- MODULE 1 : PREMIER CONTACT ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("🔵 [ DÉMARRER ]"))
    bot.send_message(message.chat.id, "📂 **FASO ART PROMO (V.2026)**\nL'application n°1 des artistes du Burkina.", 
                     reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🔵 [ DÉMARRER ]")
def select_lang(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("FR 🇫🇷", callback_data="lang_fr"),
        types.InlineKeyboardButton("EN 🇬🇧", callback_data="lang_en"),
        types.InlineKeyboardButton("MOORE 🇧🇫", callback_data="lang_moore")
    )
    bot.send_message(message.chat.id, "🌐 Choisissez votre langue :", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def professional_rules(call):
    rules = (
        "⚖️ **RÈGLES PROFESSIONNELLES**\n\n"
        "1. Contenu original uniquement.\n"
        "2. **Paiement :** Vérification humaine avant validation.\n"
        "3. **Anti-Fraude :** Toute fausse preuve = Bannissement.\n"
        "4. Vidéo : Max 2 minutes / 80 Mo.\n\n"
        "Acceptez-vous ces règles ?"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ J’ACCEPTE", callback_data="rules_accept"))
    bot.edit_message_text(rules, call.message.chat.id, call.message.message_id, 
                          reply_markup=markup, parse_mode='Markdown')

# --- MODULE 2 : INSCRIPTION ---
@bot.callback_query_handler(func=lambda call: call.data == "rules_accept")
def ask_name(call):
    bot.send_message(call.message.chat.id, "🎨 Quel est votre **nom d'artiste** ?")
    bot.register_next_step_handler(call.message, save_user_info, 'name')

def save_user_info(message, field):
    # Logique simplifiée pour l'exemple (Nom -> Métier -> Téléphone -> Vidéo)
    # Dans un vrai code, on enchaînerait les register_next_step_handler
    bot.send_message(message.chat.id, f"✅ {field.capitalize()} enregistré. Continuez l'inscription...")
    # (Ici on insère la logique de collecte détaillée vue précédemment)
    show_main_menu(message)

# --- MODULE 3 : MENU PRINCIPAL (ASPECT APP) ---
def show_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚀 BOOST FLASH", "✨ VITRINE PREMIUM")
    markup.add("🎬 DÉCOUVRIR", "🔍 RECHERCHE")
    markup.add("⚙️ PARAMÈTRES", "💬 CONTACT ADMIN")
    
    # Calcul du niveau (Module 4)
    score = 0 # À récupérer en DB
    level = "Débutant" if score < 500 else "Confirmé"
    
    welcome = (
        f"🌟 **TABLEAU DE BORD**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Artiste : `Utilisateur` \n"
        f"📊 Score : `{score}` | Rang : `{level}`\n"
        f"🔥 Boost : `Inactif` \n"
        f"━━━━━━━━━━━━━━━"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=markup, parse_mode='Markdown')

# --- MODULE 5 : PAIEMENT & SÉCURITÉ ---
@bot.message_handler(func=lambda m: m.text == "✨ VITRINE PREMIUM")
def premium_payment(message):
    payment_msg = (
        "💎 **PASSER EN VITRINE PREMIUM**\n\n"
        "Avantages : Badge, Priorité d'affichage, Score Boosté.\n\n"
        "📍 **Envoyez 2500 FCFA vers :**\n"
        "🟠 Orange Money : `07218439`\n"
        "🔵 Moov Money : `03489109`\n\n"
        "⚠️ Après envoi, cliquez sur le bouton ci-dessous pour envoyer la preuve."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Envoyer la preuve (Capture/ID)", callback_data="send_proof"))
    bot.send_message(message.chat.id, payment_msg, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "send_proof")
def ask_proof(call):
    bot.send_message(call.message.chat.id, "Envoyez la **Capture d'écran** du dépôt et l'**ID de transaction** :")
    bot.register_next_step_handler(call.message, process_proof)

def process_proof(message):
    # Sécurité (Module 5.4)
    # On envoie à l'admin pour vérification (Module 6)
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(ADMIN_ID, f"🔔 **NOUVELLE DEMANDE PREMIUM**\nDe : @{message.from_user.username}\nID : {message.chat.id}")
    
    bot.send_message(message.chat.id, "⏳ **Vérification en cours...**\nVotre demande a été envoyée à l'administrateur. Réponse sous 24h.")

# --- MODULE 12 : INTERFACE ADMIN ---
@bot.message_handler(commands=['admin_stats'])
def admin_stats(message):
    if str(message.chat.id) == str(ADMIN_ID):
        # Ici calcul des revenus et stats (Module 12)
        bot.send_message(message.chat.id, "📊 **STATS GÉNÉRALES**\nArtistes : 12\nRevenus : 30.000 FCFA")

# --- LANCEMENT ---
if __name__ == "__main__":
    print("🚀 Faso Art Promo Bot lancé...")
    bot.polling(none_stop=True)
