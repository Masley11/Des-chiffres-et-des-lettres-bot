import logging
import random
import os
import pickle
import time
from collections import defaultdict
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from simpleeval import simple_eval
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constantes
CREATOR = "🎮 Game Master X"
DATA_FILE = "game_data.pkl"
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

# Questions de culture générale
culture_generale_questions = [
    {"question": "Quelle est la capitale de la France ?", "reponse": "Paris", "theme": "Géographie"},
    {"question": "Qui a peint la Joconde ?", "reponse": "Léonard de Vinci", "theme": "Art"},
    {"question": "Combien de continents sur Terre ?", "reponse": "7", "theme": "Géographie"},
    {"question": "Quelle est la formule de l'eau ?", "reponse": "H2O", "theme": "Science"},
    {"question": "En quelle année a eu lieu la Révolution française ?", "reponse": "1789", "theme": "Histoire"},
]

themes_disponibles = list(set(q["theme"] for q in culture_generale_questions))

# Chargement des données
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'rb') as f:
        game_data = pickle.load(f)
    user_scores = game_data.get('user_scores', defaultdict(lambda: {"chiffres": 0, "lettres": 0, "culture": 0, "total": 0, "games_played": 0}))
    challenges = game_data.get('challenges', {})
else:
    user_scores = defaultdict(lambda: {"chiffres": 0, "lettres": 0, "culture": 0, "total": 0, "games_played": 0})
    challenges = {}

def save_data():
    with open(DATA_FILE, 'wb') as f:
        pickle.dump({'user_scores': user_scores, 'challenges': challenges}, f)

def get_encouragement():
    return random.choice(ENCOURAGEMENTS)

# Commandes du bot
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

async def themes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    liste = '\n'.join(f"- {theme}" for theme in themes_disponibles)
    await update.message.reply_text(f"📚 Thèmes disponibles :\n{liste}")

async def culture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if not args:
        await update.message.reply_text("Veuillez préciser un thème. Exemple : /culture Histoire\n\nThèmes disponibles : " + ", ".join(themes_disponibles))
        return

    theme = " ".join(args).capitalize()
    questions = [q for q in culture_generale_questions if q["theme"] == theme]

    if not questions:
        await update.message.reply_text(f"Aucune question trouvée pour le thème '{theme}'. Essayez avec : " + ", ".join(themes_disponibles))
        return

    question = random.choice(questions)
    await update.message.reply_text(f"🧠 Question ({theme}) : {question['question']}")

    # Stocker les données pour vérification
    context.user_data['expected_answer'] = question['reponse'].lower()
    context.user_data['question_theme'] = theme
    context.user_data['user_id'] = update.effective_user.id

async def chiffres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_scores[user_id]["games_played"] += 1

    numbers = [random.randint(1, 9) for _ in range(5)]
    target = random.randint(100, 999)
    
    await update.message.reply_text(f"🎯 Trouvez un calcul avec : {numbers}\nObjectif : {target}")
    
    context.user_data['chiffres_data'] = {
        'numbers': numbers,
        'target': target,
        'user_id': user_id
    }

async def lettres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_scores[user_id]["games_played"] += 1

    lettres_tirage = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=8))
    await update.message.reply_text(f"🔠 Formez un mot avec ces lettres : {lettres_tirage}")
    
    context.user_data['lettres_data'] = {
        'lettres': lettres_tirage,
        'user_id': user_id
    }

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_text = update.message.text.strip()
    
    # Réponse à une question de culture
    if 'expected_answer' in context.user_data and context.user_data['user_id'] == user_id:
        correct_answer = context.user_data['expected_answer']
        
        if user_text.lower() == correct_answer:
            user_scores[user_id]["culture"] += 1
            user_scores[user_id]["total"] += 1
            await update.message.reply_text(f"✅ Bonne réponse, {user_name} !\n{get_encouragement()}")
        else:
            await update.message.reply_text(f"❌ Mauvaise réponse. La bonne réponse était : {correct_answer}")
        
        context.user_data.pop('expected_answer', None)
        context.user_data.pop('question_theme', None)
        return
    
    # Réponse au jeu des chiffres
    elif 'chiffres_data' in context.user_data and context.user_data['user_id'] == user_id:
        try:
            numbers = context.user_data['chiffres_data']['numbers']
            target = context.user_data['chiffres_data']['target']
            
            value = simple_eval(user_text)
            used_numbers = [int(x) for x in user_text if x.isdigit()]
            
            if sorted(used_numbers) <= sorted(numbers * 2) and abs(value - target) <= 5:
                user_scores[user_id]["chiffres"] += 1
                user_scores[user_id]["total"] += 1
                await update.message.reply_text(f"✅ Bravo {user_name} ! Résultat : {value}\n{get_encouragement()}")
            else:
                await update.message.reply_text(f"❌ Pas accepté ({value}). Cible : {target}")
        except:
            await update.message.reply_text("❌ Erreur dans votre calcul.")
        finally:
            context.user_data.pop('chiffres_data', None)
        return
    
    # Réponse au jeu des lettres
    elif 'lettres_data' in context.user_data and context.user_data['user_id'] == user_id:
        try:
            lettres_tirage = context.user_data['lettres_data']['lettres']
            mot = user_text.upper()
            
            if all(mot.count(c) <= lettres_tirage.count(c) for c in mot):
                if len(mot) >= 3:
                    user_scores[user_id]["lettres"] += 1
                    user_scores[user_id]["total"] += 1
                    await update.message.reply_text(f"✅ Bien joué {user_name} ! Mot : {mot}\n{get_encouragement()}")
                else:
                    await update.message.reply_text("❌ Mot trop court (minimum 3 lettres).")
            else:
                await update.message.reply_text("❌ Lettres non valides.")
        except:
            await update.message.reply_text("❌ Erreur dans votre réponse.")
        finally:
            context.user_data.pop('lettres_data', None)
        return

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

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Le token Telegram n'est pas configuré!")
        return

    application = Application.builder().token(token).build()

    # Commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("classement", classement))
    application.add_handler(CommandHandler("themes", themes))
    application.add_handler(CommandHandler("culture", culture))
    application.add_handler(CommandHandler("chiffres", chiffres))
    application.add_handler(CommandHandler("lettres", lettres))

    # Handler pour toutes les réponses textuelles
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    try:
        logger.info("Bot en cours d'exécution...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Erreur: {e}")
    finally:
        save_data()

if __name__ == "__main__":
    main()
