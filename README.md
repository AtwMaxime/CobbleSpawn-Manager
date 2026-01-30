# CobbleSpawn Manager

**CobbleSpawn Manager** is a suite of Python tools designed for **Cobblemon (Fabric 1.21+)** Minecraft server administrators.

It helps to:
- Clean up spawn files  
- Fix empty biome tags (automatic replacement with `#is_overworld`)  
- Resolve spawn condition conflicts  
- Block legendary spawns effectively across **all namespaces**  
- Generate a comprehensive **Location Atlas** for players  

---

## Features

### Biome Extractor
Scans all mods and datapacks to extract every biome key and biome group.  
Creates a local `biome_database.json` to ensure other scripts use correct biome IDs.

### Legendary Blocker
Deep-scans all `.jar` files (mods) and datapacks to detect and disable legendary spawns, regardless of namespace or hidden location.

### Spawn Cleaner
Merges spawn files, fixes invalid biome references, and performs restrictive cleanup to keep only the most accurate spawn rules.

### Atlas Generator
Parses all active files to generate a human-readable `ATLAS_POKEMON.txt`, listing exactly where to find every Pokémon:
- Biomes  
- Time  
- Rarity  
- Altitude  

### Discord Bot
A ready-to-use bot allowing players to query the Atlas directly from Discord:
```
!find Pikachu
```

---

## Required Structure

Place the scripts in a root folder containing:

```
/mods        # Your server mod files (.jar archives are scanned)
/datapacks   # Your server datapacks (zipped or folders)
```

---

## How to Use

### Requirements
- Python **3.11+**

---

## 1. Preparing the Data

Before generating spawns, you must map the biomes of your modpack:

```
python extract_biomes.py
```

This creates `biome_database.json`, required for the Atlas and spawn scripts to understand custom biomes.

---

## 2. Cleaning and Generating Datapacks

Run the scripts **in this exact order**:

```
python 00_full_block.py
```
*(Optional)* Generates a pack that blocks all world spawns to start from a clean slate.

```
python 01_unified_spawns.py
```
Analyzes all mods/datapacks and generates a unified, fixed spawn pack.

```
python 02_clean_spawns.py
```
Restrictive cleanup that removes redundant general rules and keeps specific ones.

```
python 03_legendary_blocker.py
```
**CRITICAL** — Generates the *Legendary Protection* pack.  
This pack **must be loaded last** to ensure no legendary Pokémon spawn naturally.

Move the generated folders (`01_...`, `02_...`, `03_...`) into:

```
world/datapacks/
```

---

## 3. Generating the Atlas (Player Wiki)

Run:

```
python Atlas_pokemon.py
```

This generates `ATLAS_POKEMON.txt`, containing every spawn detail from your current modpack.

---

## 4. Running the Discord Bot

Install the dependency:

```
pip install discord.py
```

Open `run_pokedex_bot.py` and insert your **Bot Token** (from the Discord Developer Portal).

Run:

```
python run_pokedex_bot.py
```

### Discord Commands
```
!find <pokemon>
!spawn <pokemon>
```

---

## Load Order (Server)

To ensure full protection, datapack priority should be (bottom → top):

1. Default Mods / Datapacks  
2. `00_Total_Spawn_Blocker` *(Low Priority)*  
3. `02_Final_Cleaned_Spawns` *(Your cleaned spawns)*  
4. `03_Legendary_Protection` **(MAXIMUM Priority / LAST)**  

---

## Requirements Summary

- Python **3.11+**
- Python module: `discord.py` *(only required for the bot)*

---

Developed to stabilize and document spawns for the **Pokejadou** server.
