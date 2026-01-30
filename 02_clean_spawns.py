import os
import json
import copy

# ================= CONFIGURATION =================
# On prend en entrée le pack propre généré à l'étape précédente
INPUT_PACK_NAME = "01_Unified_Spawns"
INPUT_DIR = os.path.join(os.getcwd(), INPUT_PACK_NAME, "data", "cobblemon", "spawn_pool_world")

# Nouveau pack de sortie (Le Final)
OUTPUT_PACK_NAME = "03_Final_Cleaned_Spawns"
# =================================================

def calculate_specificity_score(rule):
    """Calcule à quel point une règle est 'restrictive'."""
    score = 0
    cond = rule.get("condition", {})
    anti = rule.get("anticondition", {})
    
    if "timeRange" in cond: score += 2
    if "weather" in cond: score += 2
    if "minY" in cond or "maxY" in cond: score += 2
    if "minSkyLight" in cond or "maxSkyLight" in cond: score += 1
    if "canSeeSky" in cond: score += 3 
    
    biomes = cond.get("biomes", [])
    if biomes and len(biomes) > 0:
        score += 1
        
    if anti: score += 1
    return score

def is_subset(specific_rule, general_rule):
    """Vérifie si 'specific_rule' est un cas particulier de 'general_rule'."""
    ctx_s = specific_rule.get("context", specific_rule.get("spawnablePositionType", "grounded"))
    ctx_g = general_rule.get("context", general_rule.get("spawnablePositionType", "grounded"))
    if ctx_s != ctx_g: return False

    cond_s = specific_rule.get("condition", {})
    cond_g = general_rule.get("condition", {})

    biomes_s = set(cond_s.get("biomes", []))
    biomes_g = set(cond_g.get("biomes", []))
    
    # Si General a des biomes, Specific doit être inclus dedans
    if biomes_g:
        if not biomes_s: return False 
        if not biomes_s.issubset(biomes_g): return False 

    # Vérification des Conditions (Temps, Météo...)
    keys = ["timeRange", "weather", "canSeeSky"]
    for k in keys:
        val_s = cond_s.get(k)
        val_g = cond_g.get(k)
        if val_g is not None:
            if val_s != val_g:
                return False 
    
    return True

def clean_rules(rules):
    """Nettoie la liste des règles en gardant les plus restrictives."""
    if not rules: return [], 0 
    
    kept_rules = []
    # Tri décroissant : les règles les plus complexes (score haut) en premier
    sorted_rules = sorted(rules, key=calculate_specificity_score, reverse=True)
    
    deleted_count = 0
    
    for candidate in sorted_rules:
        is_redundant_generalization = False
        
        for accepted in kept_rules:
            # Si une règle déjà acceptée (précise) couvre celle-ci (générale)
            if is_subset(accepted, candidate):
                is_redundant_generalization = True
                break
        
        if not is_redundant_generalization:
            kept_rules.append(candidate)
        else:
            deleted_count += 1
            
    return kept_rules, deleted_count

def process_files():
    print(f"--- 🧹 Démarrage du Nettoyage Restrictif (v3) ---")
    
    if not os.path.exists(INPUT_DIR):
        print(f"❌ ERREUR : Le dossier source '{INPUT_DIR}' n'existe pas.")
        print("Assure-toi d'avoir lancé le script 'step2_semantic_fusion_v5.py' avant.")
        return

    # Préparation dossier sortie
    output_base = os.path.join(os.getcwd(), OUTPUT_PACK_NAME)
    output_json_dir = os.path.join(output_base, "data", "cobblemon", "spawn_pool_world")
    os.makedirs(output_json_dir, exist_ok=True)
    
    with open(os.path.join(output_base, "pack.mcmeta"), "w") as f:
        json.dump({"pack": {"pack_format": 15, "description": "Cleaned Restrictive Spawns"}}, f, indent=4)

    total_removed = 0
    files_processed = 0

    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith(".json"): continue
        
        filepath = os.path.join(INPUT_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: continue

        if "spawns" not in data: continue
        
        original_rules = data["spawns"]
        
        # LE NETTOYAGE
        cleaned_rules, removed = clean_rules(original_rules)
        total_removed += removed
        
        # Réécriture des IDs (basé sur le nom du fichier déjà nettoyé par l'étape 2)
        poke_name = filename.replace(".json", "")
        for i, rule in enumerate(cleaned_rules):
            rule["id"] = f"{poke_name}-{i}"

        output_data = {
            "enabled": True,
            "neededInstalledMods": [],
            "spawns": cleaned_rules
        }
        
        # On garde le même nom de fichier (qui est déjà propre/aseptisé depuis l'étape 2)
        with open(os.path.join(output_json_dir, filename), "w") as f:
            json.dump(output_data, f, indent=2)
            
        files_processed += 1

    print("-" * 40)
    print(f"✅ TERMINÉ !")
    print(f"📂 Fichiers traités : {files_processed}")
    print(f"🗑️ Règles génériques supprimées : {total_removed}")
    print(f"📦 Nouveau Pack : '{OUTPUT_PACK_NAME}'")
    print("-" * 40)
    print("INSTALLATION :")
    print(f"1. Mets le dossier '{OUTPUT_PACK_NAME}' dans tes datapacks.")
    print(f"2. Active-le avec : /datapack enable \"file/{OUTPUT_PACK_NAME}\" after \"file/{INPUT_PACK_NAME}\"")
    print("   (Ou remplace carrément le 01 par le 05 si tu veux être radical).")

if __name__ == "__main__":
    process_files()