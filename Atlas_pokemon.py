import os
import zipfile
import json
import re

# ================= CONFIGURATION =================
# Les dossiers à scanner
SOURCE_DIRS = ["mods", "datapacks"]
# Nom du fichier de sortie
OUTPUT_FILE = "ATLAS_POKEMON.txt"

# Pour ignorer les dossiers de backup ou les blockers si tu veux
# (Le script vérifie déjà "enabled": false, donc c'est une sécurité en plus)
IGNORE_PATHS = ["00_Total_Spawn_Blocker", "03_Legendary_Protection"]
# =================================================

pokedex = {}

def clean_name(name):
    """Rend le nom du Pokémon joli (ex: 'nidoran_m' -> 'Nidoran M')"""
    name = name.replace("cobblemon:", "")
    name = re.sub(r"^\d+_", "", name) # Enlève les nombres
    name = name.replace("_", " ").title()
    return name

def format_condition(rule):
    """Traduit les conditions techniques en texte lisible"""
    parts = []
    cond = rule.get("condition", {})
    
    # 1. Biomes
    biomes = cond.get("biomes", [])
    if biomes:
        # On nettoie les noms de biomes (enlever minecraft:, #, etc)
        clean_biomes = [b.split(":")[-1].replace("#", "").replace("is_", "").replace("_", " ").title() for b in biomes if b]
        if clean_biomes:
            parts.append(f"🌍 Biomes : {', '.join(clean_biomes)}")
    else:
        parts.append("🌍 Biomes : Partout (Global)")

    # 2. Temps
    time = cond.get("timeRange")
    if time == "night": parts.append("🌃 Nuit")
    elif time == "day": parts.append("☀️ Jour")
    elif time == "dusk": parts.append("🌅 Crépuscule")
    elif time == "dawn": parts.append("🌄 Aube")

    # 3. Position (Ciel / Sol / Eau)
    if cond.get("canSeeSky") == False:
        parts.append("🕳️ Souterrain/Grotte")
    if cond.get("canSeeSky") == True:
        parts.append("☁️ Surface uniquement")
        
    ctx = rule.get("context", "")
    if ctx == "submerged": parts.append("💧 Dans l'eau")
    if ctx == "air": parts.append("🕊️ En vol")

    # 4. Hauteur
    min_y = cond.get("minY")
    max_y = cond.get("maxY")
    if min_y is not None or max_y is not None:
        y_text = "↕️ Altitude :"
        if min_y is not None: y_text += f" min {min_y}"
        if max_y is not None: y_text += f" max {max_y}"
        parts.append(y_text)
        
    # 5. Météo
    weather = cond.get("weather")
    if weather == "rain": parts.append("🌧️ Pluie")
    if weather == "thunder": parts.append("⛈️ Orage")
    if weather == "clear": parts.append("☀️ Ciel dégagé")

    # 6. Rareté (Poids)
    weight = rule.get("weight", 0)
    rarity = "Commun"
    if weight < 1: rarity = "Ultra Rare"
    elif weight < 5: rarity = "Rare"
    elif weight < 10: rarity = "Peu Commun"
    
    parts.append(f"🎲 Rareté : {rarity} (Poids {weight})")

    return " | ".join(parts)

def process_file_content(content, filename):
    try:
        data = json.load(content)
    except: return

    # Si le fichier est désactivé (ex: par nos blockers), on l'ignore !
    if data.get("enabled") == False:
        return

    if "spawns" not in data or not isinstance(data["spawns"], list): return

    # Nom par défaut du fichier
    file_poke_name = filename.replace(".json", "")
    file_poke_name = re.sub(r"^\d+_", "", file_poke_name).replace("_", " ").title()

    for rule in data["spawns"]:
        # Le nom spécifique dans la règle (ex: "Rattata Alolan")
        raw_name = rule.get("pokemon", file_poke_name)
        nice_name = clean_name(raw_name)

        if nice_name not in pokedex:
            pokedex[nice_name] = []

        formatted_location = format_condition(rule)
        if formatted_location not in pokedex[nice_name]:
            pokedex[nice_name].append(formatted_location)

def scan_everything():
    print("--- 🗺️ Génération de l'Atlas Pokémon ---")
    cwd = os.getcwd()
    
    for folder in SOURCE_DIRS:
        # On saute les dossiers ignorés
        if any(ign in folder for ign in IGNORE_PATHS): continue
        
        target_dir = os.path.join(cwd, folder)
        if not os.path.exists(target_dir): continue

        for root, dirs, files in os.walk(target_dir):
            # On ignore les dossiers de blocker s'ils sont scannés par walk
            if any(ign in root for ign in IGNORE_PATHS): continue

            for file in files:
                full_path = os.path.join(root, file)
                
                # Archives
                if file.lower().endswith((".jar", ".zip")):
                    try:
                        with zipfile.ZipFile(full_path, 'r') as z:
                            for internal in z.namelist():
                                if "spawn_pool_world" in internal and internal.endswith(".json"):
                                    with z.open(internal) as f:
                                        process_file_content(f, os.path.basename(internal))
                    except: pass
                
                # Fichiers bruts
                elif file.endswith(".json") and "spawn_pool_world" in full_path:
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            process_file_content(f, file)
                    except: pass

def save_atlas():
    print(f"--- 📝 Écriture de {OUTPUT_FILE} ---")
    
    sorted_names = sorted(pokedex.keys())
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("==================================================\n")
        f.write("       ATLAS DE LOCALISATION DES POKÉMONS\n")
        f.write("==================================================\n\n")
        
        for name in sorted_names:
            locations = pokedex[name]
            f.write(f"📌 {name}\n")
            if not locations:
                f.write("   - ❓ Aucune donnée de spawn trouvée (ou désactivé)\n")
            else:
                for loc in locations:
                    f.write(f"   - {loc}\n")
            f.write("\n") # Saut de ligne entre chaque Pokémon

    print(f"✅ Atlas généré avec succès ! ({len(sorted_names)} espèces répertoriées)")
    print(f"👉 Ouvre le fichier '{OUTPUT_FILE}' pour voir où chasser.")

if __name__ == "__main__":
    scan_everything()
    save_atlas()