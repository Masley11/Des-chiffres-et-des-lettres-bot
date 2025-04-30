import logging

# Configurer le logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import random
import asyncio
import os
import pickle
from collections import defaultdict
from simpleeval import simple_eval

CREATOR = "🎮 Game Master X"
DATA_FILE = "game_data.pkl"

# Charger les données si elles existent
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'rb') as f:
        game_data = pickle.load(f)
    user_scores = game_data.get('user_scores', defaultdict(lambda: {"chiffres": 0, "lettres": 0, "culture": 0, "total": 0, "games_played": 0}))
    challenges = game_data.get('challenges', {})
else:
    user_scores = defaultdict(lambda: {"chiffres": 0, "lettres": 0, "culture": 0, "total": 0, "games_played": 0})
    challenges = {}

active_games = {}

ENCOURAGEMENTS = [
    "💪 Vous êtes sur la bonne voie!",
    "🚀 Vous progressez à vitesse grand V!",
    "🧠 Votre intelligence m'impressionne!",
    "🏆 Champion(ne) en devenir!",
    "🔥 Vous êtes en feu aujourd'hui!",
    "👑 Future star des jeux télévisés!",
    "🤯 Vous cassez les scores!",
    "🎯 Précision chirurgicale!",
    "🤩 Quel talent!",
    "✨ La magie opère!"
]

culture_generale_questions = [
    {"question": "Quelle est la capitale de la France ?", "reponse": "Paris", "theme": "Géographie"},
    {"question": "Qui a peint la Joconde ?", "reponse": "Léonard de Vinci", "theme": "Art"},
    {"question": "Combien de continents sur Terre ?", "reponse": "7", "theme": "Géographie"},
    {"question": "Quelle est la formule de l'eau ?", "reponse": "H2O", "theme": "Science"},
    {"question": "En quelle année a eu lieu la Révolution française ?", "reponse": "1789", "theme": "Histoire"},
]

themes_disponibles = list(set(q["theme"] for q in culture_generale_questions))

def save_data():
    with open(DATA_FILE, 'wb') as f:
        pickle.dump({'user_scores': user_scores, 'challenges': challenges}, f)

def get_encouragement():
    return random.choice(ENCOURAGEMENTS)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    presentation = (
        f"👋 Bonjour {update.effective_user.first_name} !\n\n"
        "Je suis votre bot pour jouer aux **Chiffres et aux Lettres**.\n\n"
        f"Créé par {CREATOR}\n\n"
        "🎮 **Modes de jeu** :\n"
        "1️⃣ Solo :\n"
        "- /chiffres : Jeu des chiffres\n"
        "- /lettres : Jeu des lettres\n"
        "- /culture [thème] : Culture générale\n"
        "- /themes : Liste des thèmes disponibles\n\n"
        "2️⃣ Multijoueur :\n"
        "- /challenge @username : Défier un ami\n"
        "- /accept : Accepter un défi\n\n"
        "📊 Statistiques :\n"
        "- /stats : Vos performances\n"
        "- /classement : Top 10 des joueurs\n\n"
        f"{get_encouragement()} Amusez-vous bien ! 🎉"
    )
    await update.message.reply_text(presentation)

async def monid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ton ID Telegram est : `{update.effective_user.id}`", parse_mode="Markdown")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    scores = user_scores[user_id]
    total_games = scores["games_played"]
    win_rate = (scores["total"] / total_games * 100) if total_games > 0 else 0
    
    stats_text = (
        f"📊 **Statistiques de {user_name}**\n\n"
        f"🎯 Score total: {scores['total']}\n"
        f"🔢 Chiffres: {scores['chiffres']} victoires\n"
        f"🔠 Lettres: {scores['lettres']} victoires\n"
        f"🧠 Culture: {scores['culture']} victoires\n\n"
        f"📈 Taux de réussite: {win_rate:.1f}%\n"
        f"🎮 Parties jouées: {total_games}\n\n"
        f"{get_encouragement()}"
    )
    await update.message.reply_text(stats_text)

async def classement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_players = sorted(
        [(user_id, data['total']) for user_id, data in user_scores.items() if data['total'] > 0],
        key=lambda x: x[1],
        reverse=True
    )[:10]

    if not top_players:
        await update.message.reply_text("🏆 Le classement est vide pour le moment!")
        return
    
    classement_text = "🏆 **Classement Global** 🏆\n\n"
    for idx, (user_id, score) in enumerate(top_players, 1):
        try:
            user = await context.bot.get_chat(user_id)
            username = user.first_name or f"Joueur {user_id}"
            classement_text += f"{idx}. {username} - {score} pts\n"
        except:
            classement_text += f"{idx}. Joueur #{user_id} - {score} pts\n"
    
    classement_text += f"\n{get_encouragement()}"
    await update.message.reply_text(classement_text)

# /themes – Liste des thèmes disponibles
async def themes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    liste = '\n'.join(f"- {theme}" for theme in themes_disponibles)
    await update.message.reply_text(f"📚 Thèmes disponibles :\n{liste}")

# /culture [thème] – Question de culture générale
async def culture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    args = context.args

    if not args:
        await update.message.reply_text("Veuillez préciser un thème. Exemple : /culture Histoire")
        return

    theme = " ".join(args).capitalize()
    questions = [q for q in culture_generale_questions if q["theme"] == theme]

    if not questions:
        await update.message.reply_text("Aucune question trouvée pour ce thème.")
        return

    question = random.choice(questions)
    await update.message.reply_text(f"🧠 {question['question']}")
    
    def check(msg: Update):
        return msg.from_user.id == user_id
    
    try:
        user_scores[user_id]["games_played"] += 1
        response = await context.bot.wait_for_message(filters.TEXT & filters.USER(user_id), timeout=15)
        if response.text.strip().lower() == question['reponse'].lower():
            user_scores[user_id]["culture"] += 1
            user_scores[user_id]["total"] += 1
            await response.reply_text(f"✅ Bonne réponse, {user_name} !\n{get_encouragement()}")
        else:
            await response.reply_text(f"❌ Mauvaise réponse, {user_name}.\nLa bonne réponse était : {question['reponse']}")
    except asyncio.TimeoutError:
        await update.message.reply_text("⏰ Temps écoulé !")

# /chiffres – Jeu des chiffres
async def chiffres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_scores[user_id]["games_played"] += 1

    numbers = [random.randint(1, 9) for _ in range(5)]
    target = random.randint(100, 999)

    await update.message.reply_text(f"🎯 Trouvez un calcul avec : {numbers}\nObjectif : {target}")

    try:
        response = await context.bot.wait_for_message(filters.TEXT & filters.USER(user_id), timeout=20)
        expr = response.text.strip()
        value = simple_eval(expr)
        if sorted([int(x) for x in expr if x.isdigit()]) <= sorted(numbers) and abs(value - target) <= 5:
            user_scores[user_id]["chiffres"] += 1
            user_scores[user_id]["total"] += 1
            await response.reply_text(f"✅ Bravo {user_name} ! Résultat : {value}\n{get_encouragement()}")
        else:
            await response.reply_text(f"❌ Pas accepté ({value}). Cible : {target}")
    except:
        await update.message.reply_text("❌ Erreur ou délai dépassé.")

# /lettres – Jeu des lettres
async def lettres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import requests

    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_scores[user_id]["games_played"] += 1

    lettres_tirage = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=8))
    await update.message.reply_text(f"🔠 Formez un mot avec ces lettres : {lettres_tirage}")

    try:
        response = await context.bot.wait_for_message(filters.TEXT & filters.USER(user_id), timeout=20)
        mot = response.text.strip().upper()
        if all(mot.count(c) <= lettres_tirage.count(c) for c in mot):
            # Simulation d'un dictionnaire de mots
            if len(mot) >= 3:
                user_scores[user_id]["lettres"] += 1
                user_scores[user_id]["total"] += 1
                await response.reply_text(f"✅ Bien joué {user_name} ! Mot : {mot}\n{get_encouragement()}")
            else:
                await response.reply_text("❌ Mot trop court.")
        else:
            await response.reply_text("❌ Lettres non valides.")
    except asyncio.TimeoutError:
        await update.message.reply_text("⏰ Temps écoulé !")
def main():
    token = "7587523536:AAGWnpQAmf6-Z5SVuT_EH27soEjVDfUc8gQ"  # Remplace par ton vrai token
    application = Application.builder().token(token).build()

    # Commandes principales
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("classement", classement))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("themes", themes))
    application.add_handler(CommandHandler("culture", culture))
    application.add_handler(CommandHandler("chiffres", chiffres))
    application.add_handler(CommandHandler("lettres", lettres))

    # Ajoute d'autres handlers ici si tu implémentes /challenge, /accept, etc.

    # Démarrage
    try:
        print("Bot en cours d'exécution...")
        application.run_polling()
    finally:
        save_data()

if __name__ == "__main__":
    main()
