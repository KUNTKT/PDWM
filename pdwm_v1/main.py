# main.py
import argparse
from engine.config import load_config
from engine.init_world import run_init
from engine.latent_update import run_latent_tick
from engine.collapse import run_collapse
from engine.dialog import run_dialog

def cmd_show_config():
    cfg = load_config()
    print("[PDWM] model:", cfg.model)
    print("temperature:", cfg.temperature, "max_tokens:", cfg.max_tokens)
    print("init:", cfg.init)

if __name__ == "__main__":
    p = argparse.ArgumentParser("PDWM v1")
    p.add_argument("cmd", choices=["show-config","init","tick","enter","talk"])
    p.add_argument("arg", nargs="?", help="space_id for enter, npc_id for talk")
    p.add_argument("rest", nargs="*", help="player utterance for talk")
    args = p.parse_args()

    if args.cmd == "show-config":
        cmd_show_config()

    elif args.cmd == "init":
        run_init()

    elif args.cmd == "tick":
        run_latent_tick()

    elif args.cmd == "enter":
        if not args.arg:
            print("用法: python main.py enter <space_id>")
        else:
            run_collapse(args.arg)

    elif args.cmd == "talk":
        if not args.arg or not args.rest:
            print('用法: python main.py talk <npc_id> "<玩家说的话>"')
        else:
            npc_id = args.arg
            player_input = " ".join(args.rest)
            run_dialog(npc_id, player_input)
