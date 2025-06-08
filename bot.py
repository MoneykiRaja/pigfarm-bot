import os
#from dotenv import load_dotenv

#load_dotenv()
TOKEN = os.getenv("7757528486:AAGzef6JGBch7XUnaqRrtSU_BdRYzPpxf5U")

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import random
from datetime import datetime, timedelta, timezone

# 🐷 Trigger rebuild

#import os
#TOKEN = os.getenv("7757528486:AAGzef6JGBch7XUnaqRrtSU_BdRYzPpxf5U")
#TOKEN = '7757528486:AAGzef6JGBch7XUnaqRrtSU_BdRYzPpxf5U'

#start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    data = load_data()

    # Optional: Referrer check
    referrer_id = context.args[0] if context.args else None

    if user_id not in data:
        # New user: create record
        data[user_id] = {
            "username": user.username or user.first_name,
            "coins": 0,
            "streak": 0,
            "piglets": []
        }

        # Reward user for joining
        data[user_id]["coins"] += 2

        # ✅ Handle referral bonus
        if referrer_id and referrer_id in data and referrer_id != user_id:
            data[referrer_id]["coins"] += 5
            data[referrer_id]["referrals"] = data[referrer_id].get("referrals", 0) + 1  # ✅ Track count
            await update.message.reply_text("🎉 You joined with a referral! +2 coins for you 🐽")
            try:
                await context.bot.send_message(
                    chat_id=int(referrer_id),
                    text=f"🎉 Someone joined using your referral link! You earned 5 coins 🐷"
                )
            except:
                pass
        else:
            await update.message.reply_text("🐷 Welcome to Pig Farm! Feed your pig and grow your farm.")

        save_data(data)

    else:
        await update.message.reply_text("👋 You’re already part of the farm. Let’s grow some pigs!")



import json
#import os

DATA_FILE = "players.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Task list - Admin-defined daily tasks
TASKS = {
    "join1": {
        "type": "telegram",
        "description": "Join our TON group 🪙",
        "url": "https://t.me/YourGroup",
        "reward": 3
    },
    "view1": {
        "type": "url",
        "description": "View sponsor page 🖼️",
        "url": "https://example.com/ad",
        "reward": 2
    },
    "share1": {
        "type": "manual",
        "description": "Share a pig meme in a group 🐷",
        "url": None,
        "reward": "special_feed"
    }
 }



MARKET = [
    {"type": "normal", "price": 2},
    {"type": "spotted", "price": 4},
    {"type": "golden", "price": 7}
]

def refresh_market():
    import random
    return random.choices(MARKET, k=3)  # 3 random offer



#buy

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    data = load_data()
    today = datetime.now(timezone.utc).date().strftime("%Y-%m-%d")

    if user_id in data and "pig" in data[user_id]:
        await update.message.reply_text("😅 You already own a pig!")
        return

    # Set up a full pig object
    new_pig = {
        "birth_date": today,
        "fed_dates": [],
        "pregnant": False,
        "pregnant_date": None
    }

    data[user_id] = data.get(user_id, {})  # If new user, create base
    data[user_id]["username"] = user.username or user.first_name
    data[user_id]["pig"] = new_pig
    data[user_id]["coins"] = data[user_id].get("coins", 0)
    data[user_id]["streak"] = 0
    save_data(data)

    await update.message.reply_text("🎉 You just bought your first pig 🐖!\nTake good care of it and it might give you piglets!")


#// feeding //

async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    data = load_data()
    today = datetime.now(timezone.utc).date()
    today_str = today.strftime("%Y-%m-%d")

    if user_id not in data or "pig" not in data[user_id]:
        await update.message.reply_text("🐷 You don't have a pig! Use /buy to start.")
        return

    pig = data[user_id]["pig"]
    fed_dates = pig.get("fed_dates", [])

    # Check if already fed today
    if today_str in fed_dates:
        await update.message.reply_text("🍽 You already fed your pig today!")
        return

    # Append today's feed date
    fed_dates.append(today_str)
    pig["fed_dates"] = fed_dates

    # Streak logic (based on last 2 days)
    last_3_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 4)]
    streak = data[user_id].get("streak", 0)

    if all(day in fed_dates for day in last_3_days):
        streak += 1
        data[user_id]["coins"] = data[user_id].get("coins", 0) + 1
        streak_msg = f"🔥 Streak continues! (+1 coin)"
    else:
        streak = 1
        streak_msg = "🍽 Pig fed! Streak restarted."

    data[user_id]["streak"] = streak
    save_data(data)

    await update.message.reply_text(
        f"✅ Your pig enjoyed the meal!\n{streak_msg}\n💰 Coins: {data[user_id]['coins']}\n🔥 Streak: {streak}"
    )


# my farm check

async def myfarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    data = load_data()

    if user_id not in data or "pig" not in data[user_id]:
        await update.message.reply_text("😢 You don’t have a pig yet. Use /buy to start your farm!")
        return

    user_data = data[user_id]
    pig = user_data["pig"]
    today = datetime.now(timezone.utc).date()

    # Core info
    today = datetime.now(timezone.utc).date()
    birth_date = datetime.strptime(pig["birth_date"], "%Y-%m-%d").date()
    age = (today - birth_date).days
    streak = user_data.get("streak", 0)
    coins = user_data.get("coins", 0)


    # Mood check
    last_fed = pig["fed_dates"][-1] if pig["fed_dates"] else "Never"
    days_missed = (today - datetime.strptime(last_fed, "%Y-%m-%d").date()).days if last_fed != "Never" else 999
    if days_missed == 0:
        mood = "😊 Happy"
    elif days_missed == 1:
        mood = "😐 Hungry"
    elif days_missed < 4:
        mood = "😟 Sad"
    else:
        mood = "🏃 Ran Away"

    # Pregnancy check
    pregnant_msg = ""
    if pig.get("pregnant"):
        preg_date = datetime.strptime(pig["pregnant_date"], "%Y-%m-%d").date()
        days_pregnant = (today - preg_date).days
        if days_pregnant >= 3:
            pregnant_msg = "🍼 Ready to give birth! Use /checkbreed to collect piglets."
        else:
            remaining = 3 - days_pregnant
            pregnant_msg = f"🤰 Pregnant ({days_pregnant} days in). {remaining} day(s) until birth."

    # Piglet info
    piglet_count = len(user_data.get("piglets", []))

    await update.message.reply_text(
        f"🏡 Welcome to your farm!\n"
        f"👤 Owner: {user_data.get('username', 'Farmer')}\n"
        f"🐖 Pig Age: {age} days\n"
        f"🔥 Streak: {streak} days\n"
        f"💰 Coins: {coins}\n"
        f"❤️ Mood: {mood}\n"
        f"🐽 Piglets: {piglet_count}\n"
        f"{pregnant_msg}"
    )

# breed
async def breed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    today = datetime.now(timezone.utc).date()

    if user_id not in data or "pig" not in data[user_id]:
        await update.message.reply_text("🐷 You don’t own any pigs to breed!")
        return

    pig = data[user_id]["pig"]

    # 🐖 Age Check
    birth_date_str = pig.get("birth_date")
    if not birth_date_str:
        await update.message.reply_text("❌ Pig birth date missing.")
        return

    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    age_days = (today - birth_date).days
    if age_days < 1:
        await update.message.reply_text("🍼 Your pig must be at least 30 days old to breed.")
        return

    # 🍽 Feeding Check (last 3 days)
    fed_dates = pig.get("fed_dates", [])
    last_3 = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 4)]
    if not all(day in fed_dates for day in last_3):
        await update.message.reply_text("🍽 Your pig must be well-fed (last 3 days) to breed.")
        return

    # 💰 Coin Check
    coins = data[user_id].get("coins", 0)
    if coins < 1:
        await update.message.reply_text("💰 You need at least 1 coin to breed.")
        return

    # ✅ BREED: deduct coin and set pregnancy
    data[user_id]["coins"] -= 1
    pig["pregnant"] = True
    pig["pregnant_date"] = today.strftime("%Y-%m-%d")
    save_data(data)

    await update.message.reply_text("💘 Your pig is now pregnant! Come back in 3 days to check for piglets.")



#checkbreed

async def checkbreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    today = datetime.now(timezone.utc).date()

    if user_id not in data or "pig" not in data[user_id]:
        await update.message.reply_text("🐷 You don't have a pig yet!")
        return

    pig = data[user_id]["pig"]

    # Check if pig is pregnant
    if not pig.get("pregnant", False):
        await update.message.reply_text("🤰 Your pig is not pregnant right now.")
        return

    # Check how many days since pregnancy
    preg_date = pig.get("pregnant_date")
    if not preg_date:
        await update.message.reply_text("⚠️ Pregnancy date missing.")
        return

    preg_date = datetime.strptime(preg_date, "%Y-%m-%d").date()
    days_pregnant = (today - preg_date).days

    if days_pregnant < 3:
        remaining = 3 - days_pregnant
        await update.message.reply_text(f"🍼 Not yet! Your pig needs {remaining} more day(s) to give birth.")
        return

    # Birth time! Generate piglets
    coins_used = pig.get("breed_spent", 1)
    min_pigs = coins_used
    max_pigs = coins_used * 3
    piglets_count = random.randint(min_pigs, max_pigs) 
    piglets = []
    for _ in range(piglets_count):
        roll = random.randint(1, 100)
        if roll <= 5:
            piglets.append({"type": "golden", "age": 0})
        elif roll <= 20:
            piglets.append({"type": "spotted", "age": 0})
        else:
            piglets.append({"type": "normal", "age": 0})

    pig["pregnant"] = False
    pig["pregnant_date"] = None
    pig["breed_spent"] = 0
    data[user_id]["piglets"] = data[user_id].get("piglets", []) + piglets
    save_data(data)

    # Summary message
    summary = {}
    for p in piglets:
        summary[p["type"]] = summary.get(p["type"], 0) + 1

    summary_msg = "\n".join([f"🐽 {typ.title()}: {count}" for typ, count in summary.items()])
    await update.message.reply_text(f"🎉 Your pig gave birth to {piglets_count} piglet(s)!\n{summary_msg}")


#sellpiglets
async def sellpiglet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data or not data[user_id].get("piglets"):
        await update.message.reply_text("😢 You don’t have any piglets to sell.")
        return

    # Validate input
    try:
        index = int(context.args[0]) - 1
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Use: /sellpiglet <number>\nExample: /sellpiglet 2")
        return

    piglets = data[user_id]["piglets"]

    if index < 0 or index >= len(piglets):
        await update.message.reply_text("❌ Invalid piglet number.")
        return

    # Get piglet and assign value
    piglet = piglets.pop(index)
    pig_type = piglet["type"]

    if pig_type == "golden":
        coins_earned = 5
    elif pig_type == "spotted":
        coins_earned = 3
    else:
        coins_earned = 1

    # Update user coins and save
    data[user_id]["coins"] += coins_earned
    save_data(data)

    await update.message.reply_text(
        f"💰 Sold your {pig_type} piglet for {coins_earned} coin(s)!\n"
        f"🐖 Remaining piglets: {len(piglets)}"
    )

#market display
async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    offers = refresh_market()
    context.user_data["market"] = offers
   # update.market_offers = offers  # temp save for session

    msg = "🛒 Piglet Market — Buy with your coins!\n\n"
    for i, offer in enumerate(offers, 1):
        msg += f"{i}. {offer['type'].title()} piglet — {offer['price']} coins\n"

    msg += "\nUse /buymarket <number> to buy."
    context.user_data["market"] = offers  # store offers per user

    await update.message.reply_text(msg)

#user buy from market

async def buymarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get(user_id, {})
    coins = user_data.get("coins", 0)
    offers = context.user_data.get("market")

    if not offers:
        await update.message.reply_text("❌ No market offers. Use /market first.")
        return

    try:
        index = int(context.args[0]) - 1
        offer = offers[index]
    except:
        await update.message.reply_text("⚠️ Use: /buymarket <number>")
        return

    if coins < offer["price"]:
        await update.message.reply_text("💸 Not enough coins!")
        return

    # Deduct coins & add piglet
    user_data["coins"] -= offer["price"]
    user_data["piglets"] = user_data.get("piglets", [])
    user_data["piglets"].append({"type": offer["type"], "age": 0})

    save_data(data)
    await update.message.reply_text(
        f"✅ You bought a {offer['type']} piglet!\n💰 Coins left: {user_data['coins']}"
    )

#referrals
async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get(user_id, {})
    referral_count = user_data.get("referrals", 0)

    await update.message.reply_text(
        f"📣 Share this link to earn 5 coins for every friend who joins!\n"
        f"🔗 https://t.me/YourPigBot?start={user_id}\n\n"
        f"👥 Total referrals: {referral_count}"
    )


#tasks

async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📋 Daily Piggy Tasks:\n\n"

    for code, task in TASKS.items():
        msg += f"🔹 {task['description']}\n"
        if task["url"]:
            msg += f"🔗 {task['url']}\n"
        reward_text = f"{task['reward']} coins" if isinstance(task['reward'], int) else task['reward']
        msg += f"🏆 Reward: {reward_text}\n"
        msg += f"➡️ Type `/claim {code}` to receive reward\n\n"
    
    await update.message.reply_text(msg)

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get(user_id, {})

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /claim <taskcode>")
        return

    task_code = context.args[0]
    task = TASKS.get(task_code)

    if not task:
        await update.message.reply_text("❌ Invalid task code.")
        return

    # Prevent duplicate claiming
    claimed = user_data.get("claimed_tasks", [])
    if task_code in claimed:
        await update.message.reply_text("🙅 You've already claimed this task.")
        return

    # Reward
    if isinstance(task["reward"], int):
        user_data["coins"] = user_data.get("coins", 0) + task["reward"]
        reward_msg = f"💰 You earned {task['reward']} coins!"
    else:
        # Handle special reward like 'special_feed'
        reward_msg = f"🎁 You received a reward: {task['reward']}! (Feature coming soon)"

    claimed.append(task_code)
    user_data["claimed_tasks"] = claimed
    data[user_id] = user_data
    save_data(data)
    await update.message.reply_text(reward_msg)




app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("feed", feed))
app.add_handler(CommandHandler("myfarm", myfarm))
app.add_handler(CommandHandler("breed", breed))
app.add_handler(CommandHandler("checkbreed", checkbreed))
app.add_handler(CommandHandler("sellpiglet", sellpiglet))
app.add_handler(CommandHandler("market", market))
app.add_handler(CommandHandler("buymarket", buymarket))
app.add_handler(CommandHandler("referral", referral))
app.add_handler(CommandHandler("tasks", tasks))
app.add_handler(CommandHandler("claim", claim))

print("🐷 Bot is running...")
app.run_polling()
