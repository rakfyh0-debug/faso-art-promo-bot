import os
import sqlite3
import time
import hmac
import hashlib
import json
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import telebot

# ==============================
# 🔷 CONFIGURATION
# ==============================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID") # Ton ID Telegram (ex: 12345678)
BASE_URL = os.getenv("BASE_URL") # Ton URL Render (ex: https://ton-app.onrender.com)

if not TOKEN or not ADMIN_ID or not BASE_URL:
    print("❌ ERREUR: Variables d'environnement manquantes sur Render (BOT_TOKEN, ADMIN_ID, BASE_URL)")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==============================
# 🔷 DATABASE (SQLite)
# ==============================

def get_db():
    conn = sqlite3.connect("faso_art.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            tg_id INTEGER PRIMARY KEY,
            name TEXT,
            status TEXT DEFAULT 'GRATUIT',
            score INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            created_at INTEGER
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS transactions(
            trans_id TEXT PRIMARY KEY,
            user_id INTEGER,
            timestamp INTEGER
        )""")
        conn.commit()

init_db()

# ==============================
# 🔷 WEBHOOK & TELEGRAM AUTH
# ==============================

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/set_webhook")
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{BASE_URL}/{TOKEN}")
    return "✅ Webhook configuré avec succès !"

def verify_telegram(init_data: str):
    """ Vérifie que les données viennent bien de Telegram (HMAC SHA256) """
    try:
        parsed = dict(x.split("=", 1) for x in init_data.split("&"))
        hash_received = parsed.pop("hash")
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

        # HMAC recommandé par Telegram
        secret_key = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash != hash_received:
            return None
            
        # Vérification expiration (1 heure)
        if time.time() - int(parsed.get("auth_date", 0)) > 3600:
            return None

        return json.loads(parsed["user"])
    except:
        return None

# ==============================
# 🔷 ROUTES WEB APP (API)
# ==============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/auth", methods=["POST"])
def auth():
    init_data = request.json.get("initData")
    user = verify_telegram(init_data)
    if not user: return jsonify({"success": False})

    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (tg_id, name, created_at) VALUES (?, ?, ?)", 
                  (user["id"], user.get("first_name", "Artiste"), int(time.time())))
        conn.commit()
    return jsonify({"success": True, "user_id": user["id"]})

@app.route("/dashboard", methods=["POST"])
def dashboard():
    init_data = request.json.get("initData")
    user = verify_telegram(init_data)
    if not user: return jsonify({"success": False})

    with get_db() as conn:
        row = conn.execute("SELECT status, score, views FROM users WHERE tg_id=?", (user["id"],)).fetchone()
        if row:
            return jsonify({"success": True, "status": row['status'], "score": row['score'], "views": row['views']})
    return jsonify({"success": False})

@app.route("/upload_proof", methods=["POST"])
def upload_proof():
    try:
        init_data = request.form.get("initData")
        trans_id = request.form.get("trans_id", "").strip().upper()
        file = request.files.get("file")

        user = verify_telegram(init_data)
        if not user or not trans_id or not file:
            return jsonify({"success": False, "error": "Données invalides"})

        with get_db() as conn:
            c = conn.cursor()
            # Anti-fraude : transaction déjà existante
            if c.execute("SELECT 1 FROM transactions WHERE trans_id=?", (trans_id,)).fetchone():
                return jsonify({"success": False, "error": "Code déjà utilisé !"})

            filename = secure_filename(f"PAY_{user['id']}_{trans_id}.jpg")
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)

            c.execute("INSERT INTO transactions VALUES (?, ?, ?)", (trans_id, user["id"], int(time.time())))
            conn.commit()

        # Notification Admin
        with open(path, "rb") as photo:
            bot.send_photo(ADMIN_ID, photo, caption=f"💰 <b>NOUVEAU PAIEMENT</b>\nArtiste: <code>{user['id']}</code>\nTrans ID: <code>{trans_id}</code>\n\nApprouver: `/valid {user['id']}`")
        
        os.remove(path) # Nettoyage disque
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==============================
# 🔷 GESTION ADMIN (TELEGRAM)
# ==============================

@bot.message_handler(commands=["start"])
def welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🚀 OUVRIR L'AGENCE", web_app=telebot.types.WebAppInfo(url=BASE_URL)))
    bot.send_message(message.chat.id, "🇧🇫 <b>FASO ART PROMO</b>\nBienvenue dans votre espace pro.", reply_markup=markup)

@bot.message_handler(commands=["valid"])
def valid(message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    try:
        target_id = int(message.text.split()[1])
        with get_db() as conn:
            conn.execute("UPDATE users SET status='PREMIUM' WHERE tg_id=?", (target_id,))
            conn.commit()
        bot.send_message(target_id, "💎 <b>FÉLICITATIONS !</b> Votre statut PREMIUM est activé.")
        bot.reply_to(message, f"✅ Artiste {target_id} validé.")
    except:
        bot.reply_to(message, "Usage: `/valid ID_UTILISATEUR`")

# ==============================
# 🚀 LANCEMENT
# ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
