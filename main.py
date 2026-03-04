import telebot
from telebot import types
import os
import sqlite3
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
    Thread(target=run_web_server).start()

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID') 
bot = telebot.TeleBot(TOKEN)

# --- MENU PRINCIPAL (Réutilisable) ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚀 BOOST FLASH", "✨ VITRINE PREMIUM")
    markup.add("🎬 DÉCOUVRIR", "🔍 RECHERCHE")
    markup.add("⚙️ PARAMÈTRES", "💬 CONTACT ADMIN")
    return markup

# --- BOUTON RETOUR ---
def back_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⬅️ RETOUR AU MENU")
    return markup

# --- GESTION DES COMMANDES ---

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔵 [ DÉMARRER ]"))
    bot.send_message(message.chat.id, "📂 **FASO ART PROMO (V.2026)**\nBienvenue sur la plateforme des artistes !", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🔵 [ DÉMARRER ]" or m.text == "⬅️ RETOUR AU MENU")
def show_main(message):
    bot.send_message(message.chat.id, "🌟 **TABLEAU DE BORD**\nChoisissez une option ci-dessous :", reply_markup=main_menu(), parse_mode='Markdown')

# 🚀 GESTION DU BOOST
@bot.message_handler(func=lambda m: m.text == "🚀 BOOST FLASH")
def boost(message):
    msg = "🚀 **BOOST FLASH**\n\nAugmentez la visibilité de votre dernière vidéo pendant 24h !\n\n💰 Prix : **1000 FCFA**"
    bot.send_message(message.chat.id, msg, reply_markup=back_button(), parse_mode='Markdown')

# 🎬 GESTION DÉCOUVRIR
@bot.message_handler(func=lambda m: m.text == "🎬 DÉCOUVRIR")
def discover(message):
    bot.send_message(message.chat.id, "🎬 **ESPACE DÉCOUVERTE**\nRegardez les talents du moment !", reply_markup=back_button())

# ✨ VITRINE PREMIUM
@bot.message_handler(func=lambda m: m.text == "✨ VITRINE PREMIUM")
def premium(message):
    bot.send_message(message.chat.id, "💎 **MODE PREMIUM**\nAccès illimité et badge certifié.", reply_markup=back_button())

# ⚙️ PARAMÈTRES
@bot.message_handler(func=lambda m: m.text == "⚙️ PARAMÈTRES")
def settings(message):
    bot.send_message(message.chat.id, "⚙️ **VOS PARAMÈTRES**\nModifiez votre profil ou vos infos de paiement.", reply_markup=back_button())

# 💬 CONTACT ADMIN
@bot.message_handler(func=lambda m: m.text == "💬 CONTACT ADMIN")
def contact(message):
    bot.send_message(message.chat.id, f"💬 Besoin d'aide ? Contactez-nous ici : @VOTRE_NOM_UTILISATEUR", reply_markup=back_button())

# --- LANCEMENT ---
if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
