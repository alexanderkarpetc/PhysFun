"""Render every concept sheet in `levels/` into Assets/GameConcepts/.

    python Assets/GameConcepts/Tools/build.py            # all of them
    python Assets/GameConcepts/Tools/build.py coldvault  # just one

Each scene module exposes build() and is otherwise independent, so a broken scene
does not stop the rest.
"""
import importlib
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def scene_names():
    d = os.path.join(HERE, "levels")
    return sorted(f[:-3] for f in os.listdir(d)
                  if f.endswith(".py") and not f.startswith("_"))


def main(argv):
    wanted = argv[1:] or scene_names()
    failed = []
    for name in wanted:
        try:
            importlib.import_module("levels." + name).build()
        except Exception:
            failed.append(name)
            traceback.print_exc()
    if failed:
        print("FAILED: " + ", ".join(failed))
        return 1
    print("%d sheet(s) up to date" % len(wanted))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
