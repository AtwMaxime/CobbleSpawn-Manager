import discord
from discord.ext import commands
import re

# ================= CONFIGURATION =================
# ⚠️ REMETS TON TOKEN ICI AVANT DE LANCER
TOKEN = "" 
ATLAS_FILE = "ATLAS_POKEMON.txt"
# =================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
pokedex_data = {}

def load_atlas():
    """Charge le fichier texte en mémoire"""
    print("--- Chargement de l'Atlas... ---")
    current_poke = None
    try:
        with open(ATLAS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("📌"):
                    current_poke = line.replace("📌", "").strip().lower()
                    pokedex_data[current_poke] = []
                elif line.startswith("-") and current_poke:
                    clean_line = line.replace("- ", "").strip()
                    pokedex_data[current_poke].append(clean_line)
        print(f"✅ Atlas chargé : {len(pokedex_data)} Pokémons en mémoire.")
    except FileNotFoundError:
        print(f"❌ ERREUR : Le fichier {ATLAS_FILE} est introuvable.")

@bot.event
async def on_ready():
    load_atlas()
    print(f'🤖 Bot connecté en tant que {bot.user}')
    print("Commandes dispos : !find <nom>, !spawn <nom>")

# C'est ici que j'ai changé : nom de fonction 'find' + alias 'spawn'
@bot.command(aliases=['spawn'])
async def find(ctx, *, pokemon_name: str):
    """Cherche un Pokémon dans l'Atlas"""
    query = pokemon_name.lower().strip()
    
    # Recherche exacte
    if query in pokedex_data:
        matches = [query]
    else:
        # Recherche partielle
        matches = [name for name in pokedex_data.keys() if query in name]
    
    if not matches:
        await ctx.send(f"❌ Désolé, je n'ai aucune info sur **{pokemon_name}** dans l'Atlas.")
        return

    if len(matches) > 5:
        await ctx.send(f"⚠️ Trop de résultats ({len(matches)}) pour '{query}'. Soyez plus précis !")
        return

    for poke_key in matches:
        real_name = poke_key.title()
        infos = pokedex_data[poke_key]
        
        embed = discord.Embed(title=f"📌 Où trouver : {real_name}", color=0x00ff00)
        
        desc_text = ""
        for info in infos:
            parts = info.split("|")
            formatted_line = ""
            for part in parts:
                if "Biomes" in part:
                    formatted_line +=f"**{part.strip()}**\n"
                else:
                    formatted_line += f"└ {part.strip()}\n"
            desc_text += formatted_line + "\n"
            
        if not desc_text:
            desc_text = "❓ Aucune donnée de spawn précise (peut-être désactivé ou event)."
            
        embed.description = desc_text
        embed.set_footer(text="Atlas Pokejadou • Données extraites du serveur")
        
        await ctx.send(embed=embed)

if __name__ == "__main__":
    if TOKEN == "":
        print("❌ ERREUR : Veuillez configurer votre TOKEN Discord dans le script avant de lancer le bot.")
    else:
        bot.run(TOKEN)