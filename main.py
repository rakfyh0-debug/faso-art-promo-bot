import telebot
from telebot import types
import os
from flask import Flask
from threading import Thread

# --- SYSTÈME ANTI-SOMMEIL ---
app = Flask('')
@app.route('/')
def home(): return "Faso Art Promo Bot is Online!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_web_server, daemon=True).start()

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- MENUS ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚀 BOOST FLASH", "✨ VITRINE PREMIUM")
    markup.add("🎬 DÉCOUVRIR", "🔍 RECHERCHE")
    markup.add("⚙️ PARAMÈTRES", "💬 CONTACT ADMIN")
    return markup

def back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⬅️ RETOUR AU MENU")
    return markup

# --- GESTIONNAIRES ---
@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda m: m.text == "⬅️ RETOUR AU MENU")
def send_welcome(message):
    bot.send_message(message.chat.id, "🌟 **TABLEAU DE BORD**\nL'application n°1 des artistes du Burkina.", 
                     reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🚀 BOOST FLASH")
def boost(message):
    bot.send_message(message.chat.id, "🚀 **BOOST FLASH**\nPropulsez votre talent ! Tarif : 1000 FCFA.", reply_markup=back_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🎬 DÉCOUVRIR")
def discover(message):
    bot.send_message(message.chat.id, "🎬 **DÉCOUVRIR**\nVoici les artistes du moment...", reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "🔍 RECHERCHE")
def search(message):
    bot.send_message(message.chat.id, "🔍 **RECHERCHE**\nTapez le nom d'un artiste ou une catégorie.", reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "⚙️ PARAMÈTRES")
def settings(message):
    bot.send_message(message.chat.id, "⚙️ **PARAMÈTRES**\nModifiez vos infos de profil.", reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "💬 CONTACT ADMIN")
def contact(message):
    bot.send_message(message.chat.id, "💬 **CONTACT**\nÉcrivez-nous pour toute question.", reply_markup=back_menu())

# --- LANCEMENT ---
if __name__ == "__main__":
    keep_alive()
    # Le bot supprime d'abord les anciennes sessions pour éviter l'erreur rouge
    bot.remove_webhook()
    bot.polling(none_stop=True)
