import telebot
from telebot import types
import os
import sqlite3
from flask import Flask, render_template
from threading import Thread

# --- 1. CONFIGURATION WEB APP (FLASK) ---
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. CONFIGURATION BOT ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID') # Ton ID pour recevoir les preuves de paiement
bot = telebot.TeleBot(TOKEN)
WEBAPP_URL = "https://faso-art-promo.onrender.com"

# --- 3. BASE DE DONNÉES (PROTECTION DES INFOS) ---
def init_db():
    conn = sqlite3.connect('faso_art.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
        (tg_id INTEGER PRIMARY KEY, name TEXT, job TEXT, status TEXT DEFAULT 'Gratuit')''')
    conn.commit()
    conn.close()

init_db()

# --- 4. MENUS (RETOUR ET PRINCIPAL) ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_info = types.WebAppInfo(url=WEBAPP_URL)
    markup.add(types.KeyboardButton("🚀 OUVRIR L'APPLICATION", web_app=web_info))
    markup.add("🚀 BOOST FLASH", "✨ VITRINE PREMIUM")
    markup.add("⚙️ PARAMÈTRES", "💬 CONTACT ADMIN")
    return markup

def back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⬅️ RETOUR AU MENU")
    return markup

# --- 5. LOGIQUE DU BOT ---

@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda m: m.text == "⬅️ RETOUR AU MENU")
def start(message):
    bot.send_message(message.chat.id, "📂 **FASO ART PROMO (V.2026)**\nL'application n'est pas qu'un bot, c'est ton agence digitale.", 
                     reply_markup=main_menu(), parse_mode='Markdown')

# Gestion des règles professionnelles avant inscription
@bot.message_handler(func=lambda m: m.text == "✨ VITRINE PREMIUM")
def show_rules(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ J'ACCEPTE LES RÈGLES", callback_data="accept_rules"))
    rules_text = (
        "⚖️ **RÈGLES PROFESSIONNELLES**\n\n"
        "1. Les dépôts sont vérifiés manuellement.\n"
        "2. Aucune validation sans preuve de paiement.\n"
        "3. Contenu artistique respectueux uniquement."
    )
    bot.send_message(message.chat.id, rules_text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "accept_rules")
def ask_payment(call):
    bot.send_message(call.message.chat.id, "💳 **PAIEMENT**\nEnvoyez 2500 FCFA au +226 XX XX XX XX.\n\n**PUIS ENVOYEZ ICI LA CAPTURE D'ÉCRAN DU REÇU.**")

# --- 6. VÉRIFICATION DU DÉPÔT (TA RÈGLE D'OR) ---
@bot.message_handler(content_types=['photo'])
def handle_payment_proof(message):
    # On transfère la preuve à l'ADMIN (Toi)
    bot.send_message(ADMIN_ID, f"🔔 **NOUVELLE PREUVE DE PAIEMENT**\nUtilisateur : @{message.from_user.username}\nID : {message.chat.id}")
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    
    bot.send_message(message.chat.id, "✅ **Reçu envoyé !**\nL'administrateur vérifie le dépôt. Votre premium sera activé sous peu.")

# Gestion des autres boutons
@bot.message_handler(func=lambda m: m.text == "🚀 BOOST FLASH")
def boost(message):
    bot.send_message(message.chat.id, "🚀 **BOOST FLASH**\nVisibilité maximale pendant 24h. Tarif : 1000 FCFA.", reply_markup=back_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "💬 CONTACT ADMIN")
def contact(message):
    bot.send_message(message.chat.id, "💬 **CONTACT**\nUne question ? Écrivez à l'administrateur ici : @ton_username", reply_markup=back_menu())

# --- 7. LANCEMENT ---
if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    bot.remove_webhook()
    bot.polling(none_stop=True)
