import os
import json
import zipfile
import re
import statistics
import copy

# ================= CONFIGURATION =================
SOURCE_DIRS = ["mods", "datapacks"]
BIOME_DB_FILE = "biome_database.json"

PACK_00_NAME = "00_Total_Spawn_Blocker"
PACK_01_NAME = "01_Unified_Spawns"
PACK_02_NAME = "02_Legendary_Protection"

# Mots clés légendaires
LEGENDARY_KEYWORDS = [
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

resolved_tags = {}
try:
    with open(BIOME_DB_FILE, 'r') as f:
        db = json.load(f)
        resolved_tags = db.get("tags", {})
    print("✅ Base de données biomes chargée.")
except:
    print("⚠️ Base de données biomes non trouvée.")

files_to_block = set()
raw_spawns = {}

def sanitize_filename(name):
    name = name.lower()
    name = re.sub(r"[^a-z0-9\._-]", "_", name)
    name = re.sub(r"__+", "_", name)
    return name

def extract_pokemon_name(filename):
    name = filename.replace(".json", "")
    name = re.sub(r"^\d+_", "", name) 
    return name.lower()

def is_legendary(poke_name):
    clean_name = poke_name.lower().replace("cobblemon:", "")
    for leg in LEGENDARY_KEYWORDS:
        if leg in clean_name:
            return True
    return False

# --- ETAPE 1 : COLLECTION ---
def collect_rule(content, filename):
    try: data = json.load(content)
    except: return
    if "spawns" not in data or not isinstance(data["spawns"], list): return

    files_to_block.add(filename)

    poke_name = extract_pokemon_name(filename)
    if len(data["spawns"]) > 0 and "pokemon" in data["spawns"][0]:
        poke_name = data["spawns"][0]["pokemon"].replace("cobblemon:", "")

    if poke_name not in raw_spawns: raw_spawns[poke_name] = []

    for rule in data["spawns"]:
        if "spawnablePositionType" in rule:
            rule["context"] = rule.pop("spawnablePositionType")
        raw_spawns[poke_name].append(rule)

def scan_everything():
    print("--- 🔍 Phase 1 : Extraction ---")
    cwd = os.getcwd()
    for folder in SOURCE_DIRS:
        target_dir = os.path.join(cwd, folder)
        if not os.path.exists(target_dir): continue
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                full_path = os.path.join(root, file)
                if file.endswith(".json") and "spawn_pool_world" in root:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        collect_rule(f, file)
                elif file.lower().endswith((".zip", ".jar")):
                    try:
                        with zipfile.ZipFile(full_path, 'r') as z:
                            for internal in z.namelist():
                                if "cobblemon/spawn_pool_world" in internal and internal.endswith(".json"):
                                    with z.open(internal) as f:
                                        collect_rule(f, os.path.basename(internal))
                    except: pass

# --- ETAPE 2 : FUSION ---

def get_core_signature(rule):
    r = copy.deepcopy(rule)
    ignore = ["id", "_comment", "weight", "q", "bucket_weight"]
    for k in ignore: r.pop(k, None)
    if "condition" in r:
        r["condition"].pop("biomes", None)
        for k, v in r["condition"].items():
            if isinstance(v, list): r["condition"][k] = sorted(v)
    if "anticondition" in r:
        for k, v in r["anticondition"].items():
            if isinstance(v, list): r["anticondition"][k] = sorted(v)
    return json.dumps(r, sort_keys=True)

def is_overworld_tag(biome_id):
    b = biome_id if ":" in biome_id else f"minecraft:{biome_id}"
    return b in ["minecraft:is_overworld", "cobblemon:is_overworld", "#minecraft:is_overworld", "#cobblemon:is_overworld"]

def process_and_merge():
    print("--- 🧠 Phase 2 : Fusion & Sauvetage ---")
    final_spawns = {}
    
    count_legendaries_blocked = 0

    for pokemon, rules in raw_spawns.items():
        if is_legendary(pokemon):
            count_legendaries_blocked += 1
            continue

        flat_rules = []
        for rule in rules:
            biomes = rule.get("condition", {}).get("biomes", [])
            
            # --- FIX V5 : Remplacement intelligent ---
            if biomes:
                corrected_biomes = []
                for b in biomes:
                    if not b or b.strip() == "":
                        # C'est ici qu'on sauve Altaria !
                        # On remplace le vide par Overworld
                        corrected_biomes.append("#cobblemon:is_overworld")
                    else:
                        corrected_biomes.append(b)
                
                # On applique la correction
                for b in corrected_biomes:
                    new_r = copy.deepcopy(rule)
                    new_r["condition"]["biomes"] = [b]
                    flat_rules.append(new_r)
            else:
                # Pas de biomes du tout (Global Rule), on garde tel quel
                flat_rules.append(rule)
        
        groups = {}
        for r in flat_rules:
            sig = get_core_signature(r)
            if sig not in groups: groups[sig] = []
            groups[sig].append(r)
            
        merged_rules = []
        for sig, group_rules in groups.items():
            biomes_in_group = set()
            has_overworld = False
            for gr in group_rules:
                b_list = gr.get("condition", {}).get("biomes", [])
                b = b_list[0] if b_list else ""
                
                if b: 
                    biomes_in_group.add(b)
                    if is_overworld_tag(b): has_overworld = True
            
            filtered_rules = []
            if has_overworld and len(biomes_in_group) > 1:
                for gr in group_rules:
                    b_list = gr.get("condition", {}).get("biomes", [])
                    b = b_list[0] if b_list else ""
                    if not is_overworld_tag(b): filtered_rules.append(gr)
            else: filtered_rules = group_rules
            
            if not filtered_rules: continue

            final_biomes = set()
            weights = []
            template = copy.deepcopy(filtered_rules[0])
            for fr in filtered_rules:
                b_list = fr.get("condition", {}).get("biomes", [])
                if b_list: final_biomes.add(b_list[0])
                weights.append(fr.get("weight", 1.0))
            
            avg_weight = round(statistics.mean(weights), 2)
            template["weight"] = avg_weight
            
            if final_biomes:
                if "condition" not in template: template["condition"] = {}
                template["condition"]["biomes"] = sorted(list(final_biomes))
            
            template["id"] = f"{pokemon}-{len(merged_rules)}"
            merged_rules.append(template)
            
        final_spawns[pokemon] = merged_rules

    print(f"🚫 {count_legendaries_blocked} Pokémon Légendaires exclus.")
    return final_spawns

# --- ETAPE 3 : ECRITURE ---
def write_packs(content):
    print("--- 💾 Phase 3 : Génération ---")
    
    path_01 = os.path.join(PACK_01_NAME, "data", "cobblemon", "spawn_pool_world")
    os.makedirs(path_01, exist_ok=True)
    with open(os.path.join(PACK_01_NAME, "pack.mcmeta"), "w") as f:
        json.dump({"pack": {"pack_format": 15, "description": "Unified Spawns"}}, f, indent=4)
    
    for pokemon, rules in content.items():
        clean_filename = sanitize_filename(pokemon) + ".json"
        with open(os.path.join(path_01, clean_filename), "w") as f:
            json.dump({"enabled": True, "neededInstalledMods": [], "spawns": rules}, f, indent=2)

    print("✅ Pack 01 généré.")

if __name__ == "__main__":
    scan_everything()
    final_data = process_and_merge()
    write_packs(final_data)