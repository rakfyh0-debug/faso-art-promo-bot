import telebot
from telebot import types
import os
import sqlite3
import time
from flask import Flask, render_template
from threading import Thread

# --- INIT FLASK ---
app = Flask(__name__)
@app.route('/')
def index(): return render_template('index.html')

# --- CONFIG BOT ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
bot = telebot.TeleBot(TOKEN)

# --- 🔷 5.4 SÉCURITÉ ANTI-FRAUDE ---
# Dictionnaire pour limiter les actions (1 action / 5 min)
user_cooldowns = {}

def check_cooldown(user_id):
    current_time = time.time()
    if user_id in user_cooldowns:
        if current_time - user_cooldowns[user_id] < 300: # 5 minutes
            return False
    user_cooldowns[user_id] = current_time
    return True

# --- 🔷 1. PREMIER CONTACT ---
@bot.message_handler(commands=['start'])
def start_sequence(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔵 [ DÉMARRER ]")
    bot.send_message(message.chat.id, "📂 **FASO ART PROMO (V.2026)**\n\nCliquez sur démarrer pour accepter les règles et accéder à l'application.", 
                     reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🔵 [ DÉMARRER ]")
def accept_rules(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ J'ACCEPTE LES RÈGLES", callback_data="rules_ok"))
    text = "📜 **RÈGLES PROFESSIONNELLES**\n\n- Vidéo max 80MB / 2min\n- Paiement vérifié manuellement\n- Pas de contenu illégal."
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# --- 🔷 5. MONÉTISATION & PAIEMENT ---
@bot.callback_query_handler(func=lambda call: call.data == "rules_ok")
def show_app_button(call):
    # Ici on libère enfin l'accès à la Web App
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_info = types.WebAppInfo(url="https://faso-art-promo.onrender.com")
    markup.add(types.KeyboardButton("🚀 OUVRIR L'APPLICATION", web_app=web_info))
    bot.send_message(call.message.chat.id, "✅ Accès validé ! Utilisez le bouton en bas pour naviguer.", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def handle_app_actions(message):
    action = message.web_app_data.data
    
    if not check_cooldown(message.chat.id):
        bot.send_message(message.chat.id, "⚠️ **Anti-Spam** : Veuillez attendre 5 minutes entre deux actions.")
        return

    if action == "premium":
        msg = (
            "💎 **VITRINE PREMIUM**\n\n"
            "🟠 Orange Money : 07218439\n"
            "🟢 Moov Money : 03489109\n"
            "💰 Montant : 2500 FCFA\n\n"
            "👉 Envoyez la CAPTURE D'ÉCRAN ici."
        )
        bot.send_message(message.chat.id, msg)
    
    elif action == "boost":
        bot.send_message(message.chat.id, "🚀 **BOOST FLASH (1000 FCFA)**\nEnvoyez votre vidéo pour la mettre en tête de liste.")

# --- 🔷 6. VALIDATION ADMIN (PHOTO) ---
@bot.message_handler(content_types=['photo'])
def process_payment(message):
    bot.send_message(message.chat.id, "⏳ **Vérification sous 24h maximum.**\nVotre ID transaction est en cours d'analyse.")
    # Transfert à l'Admin
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(ADMIN_ID, f"🔔 **NOUVEAU PAIEMENT**\nUser: @{message.from_user.username}\nID: {message.chat.id}")

# --- LANCEMENT ---
def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.polling(none_stop=True)
