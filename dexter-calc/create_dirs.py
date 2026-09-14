"""Create directories for dexter-calc."""
import os

base = r"E:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI\dexter-calc\dexter_calc"
for d in ["finance", "banque"]:
    os.makedirs(os.path.join(base, d), exist_ok=True)
    open(os.path.join(base, d, "__init__.py"), "w").close()
    print("DONE", d)
