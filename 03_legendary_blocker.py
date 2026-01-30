import os
import zipfile
import json
import re

# ================= CONFIGURATION =================
SOURCE_DIRS = ["mods", "datapacks"]
OUTPUT_PACK_NAME = "03_Legendary_Protection"

# La liste des cibles à abattre
LEGENDARIES = [
    "articuno", "zapdos", "moltres", "mewtwo", "mew",
    "raikou", "entei", "suicune", "lugia", "hooh", "celebi",
    "regirock", "regice", "registeel", "latias", "latios", "kyogre", "groudon", "rayquaza", "jirachi", "deoxys",
    "uxie", "mesprit", "azelf", "dialga", "palkia", "heatran", "regigigas", "giratina", "cresselia", "phione", "manaphy", "darkrai", "shaymin", "arceus",
    "victini", "cobalion", "terrakion", "virizion", "tornadus", "thundurus", "reshiram", "zekrom", "landorus", "kyurem", "keldeo", "meloetta", "genesect",
    "xerneas", "yveltal", "zygarde", "diancie", "hoopa", "volcanion",
    "typenull", "silvally", "tapukoko", "tapulele", "tapubulu", "tapufini", "cosmog", "cosmoem", "solgaleo", "lunala", "nihilego", "buzzwole", "pheromosa", "xurkitree", "celesteela", "kartana", "guzzlord", "necrozma", "magearna", "marshadow", "poipole", "naganadel", "stakataka", "blacephalon", "zeraora", "meltan", "melmetal",
    "zacian", "zamazenta", "eternatus", "kubfu", "urshifu", "zarude", "regieleki", "regidrago", "glastrier", "spectrier", "calyrex", "enamorus",
    "koraidon", "miraidon", "walkingwake", "ironleaves", "okidogi", "munkidori", "fezandipiti", "ogerpon", "terapagos", 
    "roaringmoon", "ironvaliant", "greattusk", "screamtail", "brutebonnet", "fluttermane", "sandyshocks", "ironbundle", "ironhands", "ironjugulis", "ironmoth", "ironthorns", "gougeingfire", "ragingbolt", "ironboulder", "ironcrown"
]
# =================================================

def sanitize_filename(path):
    """Nettoie le chemin pour éviter les crashs (espaces, =, etc)"""
    directory, filename = os.path.split(path)
    filename = filename.lower()
    filename = re.sub(r"[^a-z0-9\._-]", "_", filename)
    filename = re.sub(r"__+", "_", filename)
    return os.path.join(directory, filename)

def is_legendary_file(content_bytes, filename):
    """
    Analyse le contenu (ou le nom) pour voir s'il s'agit d'un légendaire.
    """
    try:
        # 1. Check rapide sur le nom de fichier
        clean_name = filename.lower()
        for leg in LEGENDARIES:
            if leg in clean_name:
                return True, leg

        # 2. Check profond sur le contenu JSON
        data = json.loads(content_bytes)
        if "spawns" in data and isinstance(data["spawns"], list):
            for rule in data["spawns"]:
                if "pokemon" in rule:
                    poke = rule["pokemon"].replace("cobblemon:", "").lower()
                    for leg in LEGENDARIES:
                        if leg in poke:
                            return True, leg
    except:
        pass
    return False, None

def create_blocker_file(relative_path, culprit_name):
    # On aseptise le chemin de sortie
    safe_path = sanitize_filename(relative_path)
    output_path = os.path.join(os.getcwd(), OUTPUT_PACK_NAME, safe_path)
    
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write('{"enabled": false, "spawns": []}')
        return True
    except Exception as e:
        print(f"⚠️ Erreur écriture {output_path}: {e}")
        return False

def process_everything():
    print(f"--- 🛡️ Génération du {OUTPUT_PACK_NAME} ---")
    print("Stratégie : Scan profond (Contenu + Namespaces) + Aseptisation")
    
    cwd = os.getcwd()
    files_blocked = 0
    namespaces_found = set()

    # Création du pack.mcmeta
    os.makedirs(os.path.join(cwd, OUTPUT_PACK_NAME), exist_ok=True)
    with open(os.path.join(cwd, OUTPUT_PACK_NAME, "pack.mcmeta"), "w") as f:
        json.dump({"pack": {"pack_format": 15, "description": "Ultimate Legendary Blocker"}}, f, indent=4)

    for folder in SOURCE_DIRS:
        target_dir = os.path.join(cwd, folder)
        if not os.path.exists(target_dir): continue

        for root, dirs, files in os.walk(target_dir):
            for file in files:
                full_path = os.path.join(root, file)
                
                # CAS 1 : Archives (.jar / .zip)
                if file.lower().endswith((".jar", ".zip")):
                    try:
                        with zipfile.ZipFile(full_path, 'r') as z:
                            for internal in z.namelist():
                                if "spawn_pool_world" in internal and internal.endswith(".json"):
                                    with z.open(internal) as f:
                                        content = f.read()
                                        is_leg, name = is_legendary_file(content, internal)
                                        
                                        if is_leg:
                                            # On récupère le chemin relatif à partir de "data/"
                                            parts = internal.split("/")
                                            if "data" in parts:
                                                data_idx = parts.index("data")
                                                relative_path = "/".join(parts[data_idx:])
                                                
                                                if create_blocker_file(relative_path, name):
                                                    files_blocked += 1
                                                    if len(parts) > data_idx + 1:
                                                        namespaces_found.add(parts[data_idx+1])
                    except: pass

                # CAS 2 : Fichiers dézippés
                elif file.endswith(".json") and "spawn_pool_world" in full_path:
                    try:
                        with open(full_path, 'rb') as f:
                            content = f.read()
                            is_leg, name = is_legendary_file(content, file)
                            
                            if is_leg:
                                path_parts = full_path.replace("\\", "/").split("/")
                                if "data" in path_parts:
                                    data_idx = path_parts.index("data")
                                    relative_path = "/".join(path_parts[data_idx:])
                                    
                                    if create_blocker_file(relative_path, name):
                                        files_blocked += 1
                                        if len(path_parts) > data_idx + 1:
                                            namespaces_found.add(path_parts[data_idx+1])
                    except: pass

    print("-" * 40)
    print(f"✅ TERMINÉ !")
    print(f"🔒 Fichiers bloqués : {files_blocked}")
    print(f"🌐 Namespaces touchés : {namespaces_found}")
    print("-" * 40)
    print("INSTALLATION :")
    print(f"1. Copie '{OUTPUT_PACK_NAME}' dans tes datapacks.")
    print("2. Lance la commande en jeu pour le charger EN DERNIER (priorité max) :")
    print(f"   /datapack enable \"file/{OUTPUT_PACK_NAME}\" last")
    print("3. Fais /reload")

if __name__ == "__main__":
    process_everything()