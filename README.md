# 🧭 PDWM v1 — Perception-Driven World Model
A minimal single-agent world simulation prototype.

PDWM simulates a world entirely from the player’s perspective using three layers:
- **Visible World** — what the player currently perceives  
- **Latent World** — hidden regions evolving in the background  
- **Cognitive Core** — fusing logs, memory, updates, and collapse logic  

Core mechanisms: **Latent Tick → Collapse on Entry → NPC Dialogue**

---

## 🚀 Features
- World initialization from high-level config  
- Latent-world incremental updates (LLM-driven structured diffs)  
- Collapse & realization when entering a space  
- NPC state updates + contextual dialogue  
- Persistent world logs (JSONL)

---

## 📁 Directory Structure
```
engine/       Core logic (updates, collapse, dialogue, LLM calls)
prompts/      Prompt templates
data/         Runtime world state + logs
main.py       Command-line interface
config.yaml   Global model & world settings
```

---

## 🔧 Usage

### Initialize world
```bash
python main.py init
```

### Latent-world update
```bash
python main.py tick
```

### Collapse & enter a space
```bash
python main.py enter dorm
```

### NPC dialogue
```bash
python main.py talk roommate_A "How are you?"
```

---

## 🧩 System Flow
1. **Tick**: LLM updates background regions via structured diffs  
2. **Enter**: latent_state collapses into visible_state and becomes frozen  
3. **Talk**: NPC updates internal memory/state and generates a reply  

---

## 📝 License
MIT License

