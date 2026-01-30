import os
import zipfile
import json
import re

# ================= CONFIGURATION =================
SOURCE_DIRS = ["mods", "datapacks"]
OUTPUT_PACK_NAME = "00_Total_Spawn_Blocker"

# Mots clés à ne PAS bloquer (NPCs, Structures...)
IGNORED_KEYWORDS = [
    "npc", "trainer", "structure", "village"
]
# =================================================

def sanitize_filename(path):
    """
    Nettoie le nom du fichier UNIQUEMENT (garde les dossiers intacts).
    Ex: data/cobblemon/raichu alolan.json -> data/cobblemon/raichu_alolan.json
    """
    directory, filename = os.path.split(path)
    
    # Nettoyage du nom de fichier (comme pour le pack 01)
    filename = filename.lower()
    filename = re.sub(r"[^a-z0-9\._-]", "_", filename)
    filename = re.sub(r"__+", "_", filename)
    
    return os.path.join(directory, filename)

def is_ignored(filename):
    name_lower = filename.lower()
    for keyword in IGNORED_KEYWORDS:
        if keyword in name_lower:
            return True
    return False

def create_blocker_file(relative_path):
    # --- FIX : ON ASEPTISE LE CHEMIN AVANT DE CRÉER ---
    safe_path = sanitize_filename(relative_path)
    # --------------------------------------------------

    output_path = os.path.join(os.getcwd(), OUTPUT_PACK_NAME, safe_path)
    
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write('{"enabled": false, "spawns": []}')
    except Exception as e:
        print(f"Erreur création fichier : {e}")

def process_everything():
    print("--- 🛡️ Génération du VRAI Blocker v3 (Sanitized) ---")
    
    cwd = os.getcwd()
    files_blocked = 0
    files_ignored = 0

    # Création du pack.mcmeta
    os.makedirs(os.path.join(cwd, OUTPUT_PACK_NAME), exist_ok=True)
    with open(os.path.join(cwd, OUTPUT_PACK_NAME, "pack.mcmeta"), "w") as f:
        json.dump({"pack": {"pack_format": 15, "description": "The True Blocker"}}, f, indent=4)

    for folder in SOURCE_DIRS:
        target_dir = os.path.join(cwd, folder)
        if not os.path.exists(target_dir): continue

        for root, dirs, files in os.walk(target_dir):
            for file in files:
                full_path = os.path.join(root, file)
                
                # CAS 1 : Archives
                if file.lower().endswith((".jar", ".zip")):
                    try:
                        with zipfile.ZipFile(full_path, 'r') as z:
                            for internal in z.namelist():
                                if "spawn_pool_world" in internal and internal.endswith(".json"):
                                    if is_ignored(internal):
                                        files_ignored += 1
                                        continue

                                    parts = internal.split("/")
                                    if "data" in parts:
                                        data_idx = parts.index("data")
                                        relative_path = "/".join(parts[data_idx:])
                                        create_blocker_file(relative_path)
                                        files_blocked += 1
                    except: pass

                # CAS 2 : Dossiers
                elif file.endswith(".json") and "spawn_pool_world" in full_path:
                    if is_ignored(file):
                        files_ignored += 1
                        continue

                    path_parts = full_path.replace("\\", "/").split("/")
                    if "data" in path_parts:
                        data_idx = path_parts.index("data")
                        relative_path = "/".join(path_parts[data_idx:])
                        create_blocker_file(relative_path)
                        files_blocked += 1

    print("-" * 40)
    print(f"✅ TERMINÉ !")
    print(f"📁 Fichiers bloqués (et renommés proprement) : {files_blocked}")
    print(f"🙈 Ignorés : {files_ignored}")
    print("-" * 40)
    print("Action : Supprime l'ancien dossier '00' et remplace-le par celui-ci.")

if __name__ == "__main__":
    process_everything()