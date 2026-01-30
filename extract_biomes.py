import os
import json
import zipfile
import re

# ================= CONFIGURATION =================
SOURCE_DIRS = ["mods", "datapacks"] 
OUTPUT_FILE = "biome_database.json"
# =================================================

raw_tags = {} # Stocke le contenu brut des fichiers JSON trouvés
resolved_tags = {} # Stocke la liste finale des biomes par tag
unique_biomes_found = set() # Liste de tous les biomes concrets rencontrés

def normalize_id(resource_id):
    """Ajoute minecraft: si absent"""
    if ":" not in resource_id: return f"minecraft:{resource_id}"
    return resource_id

def scan_archives():
    print("--- 🕵️‍♂️ Phase 1 : Scan des fichiers de Tags ---")
    cwd = os.getcwd()
    
    files_scanned = 0
    
    for folder in SOURCE_DIRS:
        target_dir = os.path.join(cwd, folder)
        if not os.path.exists(target_dir): continue

        for root, dirs, files in os.walk(target_dir):
            for file in files:
                full_path = os.path.join(root, file)
                
                # On traite les .jar et .zip
                if file.lower().endswith((".zip", ".jar")):
                    try:
                        with zipfile.ZipFile(full_path, 'r') as z:
                            for internal_file in z.namelist():
                                # On cherche spécifiquement les tags de BIOMES
                                if "tags/worldgen/biome" in internal_file and internal_file.endswith(".json"):
                                    # Extraction de l'ID du tag depuis le chemin
                                    # Format: data/<namespace>/tags/worldgen/biome/<path>.json
                                    parts = internal_file.split("/")
                                    try:
                                        if "data" in parts:
                                            data_idx = parts.index("data")
                                            namespace = parts[data_idx+1]
                                            # On recupère tout ce qui est après "biome/"
                                            if "biome" in parts:
                                                biome_idx = parts.index("biome")
                                                tag_path = parts[biome_idx+1:]
                                                tag_name = "/".join(tag_path).replace(".json", "")
                                                
                                                tag_id = f"{namespace}:{tag_name}"
                                                
                                                with z.open(internal_file) as f:
                                                    content = json.load(f)
                                                    # Le format standard contient une liste "values"
                                                    if "values" in content:
                                                        if tag_id not in raw_tags:
                                                            raw_tags[tag_id] = []
                                                        # On étend la liste (car plusieurs mods peuvent ajouter au même tag)
                                                        raw_tags[tag_id].extend(content["values"])
                                                        files_scanned += 1
                                    except Exception as e:
                                        # print(f"Erreur parsing chemin {internal_file}: {e}")
                                        pass
                    except Exception as e:
                        print(f"⚠️ Impossible de lire {file}: {e}")

    print(f"✅ Scan terminé. {files_scanned} fichiers de tags analysés.")
    print(f"📋 {len(raw_tags)} Tags uniques identifiés (ex: cobblemon:is_overworld).")

def resolve_all_tags():
    print("--- 🧠 Phase 2 : Résolution des Inclusions ---")
    
    # Fonction récursive pour aplatir les tags
    def resolve_recursive(tag_id, stack):
        # Si on l'a déjà résolu, on retourne le résultat mis en cache
        if tag_id in resolved_tags:
            return resolved_tags[tag_id]
        
        # Si le tag n'est pas défini dans nos fichiers, c'est probablement un biome concret
        # ou un tag vide/inexistant.
        if tag_id not in raw_tags:
            # Si ça ne commence pas par #, c'est un biome
            if not tag_id.startswith("#"):
                unique_biomes_found.add(tag_id)
                return {tag_id}
            return set()

        # Protection boucle infinie (Tag A contient Tag B qui contient Tag A)
        if tag_id in stack:
            return set()

        stack.add(tag_id)
        final_biomes = set()
        
        for entry in raw_tags[tag_id]:
            val = entry
            # Parfois c'est un dict {"id": "...", "required": false}
            if isinstance(entry, dict):
                val = entry.get("id", "")
            
            val = normalize_id(val)
            
            if val.startswith("#"):
                # C'est un tag -> Récursion
                sub_tag_id = val[1:]
                resolved = resolve_recursive(sub_tag_id, stack)
                final_biomes.update(resolved)
            else:
                # C'est un biome direct
                unique_biomes_found.add(val)
                final_biomes.add(val)
        
        stack.remove(tag_id)
        resolved_tags[tag_id] = final_biomes
        return final_biomes

    # On lance la résolution pour chaque tag trouvé
    for tag_id in list(raw_tags.keys()):
        resolve_recursive(tag_id, set())

    print(f"✅ Résolution terminée.")
    print(f"🌍 {len(unique_biomes_found)} Biomes uniques trouvés au total.")

def save_database():
    print("--- 💾 Phase 3 : Sauvegarde de la Base de Données ---")
    
    # On convertit les sets en listes triées pour le JSON
    output_data = {
        "stats": {
            "total_tags": len(resolved_tags),
            "total_biomes": len(unique_biomes_found)
        },
        "biomes": sorted(list(unique_biomes_found)),
        "tags": {}
    }
    
    for tag, biomes in resolved_tags.items():
        output_data["tags"][tag] = sorted(list(biomes))
        
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"✅ Fichier '{OUTPUT_FILE}' généré avec succès !")
    print("Tu peux l'ouvrir pour vérifier que les tags contiennent bien les bons biomes.")

if __name__ == "__main__":
    scan_archives()
    resolve_all_tags()
    save_database()