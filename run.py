import os
import sys
import uvicorn

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

if __name__ == "__main__":
    # Ensure current directory is in sys.path
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    if curr_dir not in sys.path:
        sys.path.insert(0, curr_dir)

    print("\n" + "=" * 65)
    print(" 🏗️  BTP PUBLIC TENDER ANALYZER (Analyseur d'Appels d'Offres)")
    print("     Spécial Artisans & PME du BTP - Prêt à l'emploi")
    print("=" * 65)
    print(" 🚀 Serveur démarré sur : http://127.0.0.1:8000")
    print(" 📂 Dashboard web       : http://localhost:8000")
    print(" 📖 Documentation API   : http://localhost:8000/docs")
    print("=" * 65 + "\n")

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
