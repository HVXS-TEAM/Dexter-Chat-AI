# RESUME — Dexter Chat AI (état & mode de travail)

_Document de référence pour reprendre le travail à tout moment._

## 1. État actuel

- **Phase 0 (socle technique) : CRÉÉE et VÉRIFIÉE** — en attente de validation finale utilisateur
- **Mode de travail : NATIF (Voie B, TEMPORAIRE)** — Docker bloqué par un problème Windows
- MVP : **2 domaines** (Comptabilité + Finance) — vision produit : 7 domaines (ajout progressif)
- Détection de domaine et routage **génériques, pilotés par configuration** (pas de liste figée en dur)

## 2. Le point Docker / Windows (important)

- Docker Desktop ne peut pas s'installer sur cette machine : le pipeline de maintenance Windows (CBS)
  échoue au boot (`0x800f0922 CBS_E_INSTALLERS_FAILED`) et **annule toute activation de fonctionnalité**
  (WSL2) au redémarrage.
- Toute la procédure officielle de réparation a été tentée avec succès (file BITS nettoyée,
  `sfc /scannow` propre, `dism restorehealth` réussi, nettoyage, réinitialisation Windows Update) —
  Windows annule quand même à chaque boot.
- **Solution durable** (30-60 min, conserve fichiers + applications) :
  Paramètres → Système → Récupération → « Résoudre les problèmes à l'aide de Windows Update » →
  « Réinstaller maintenant ».
- Après réparation : installer Docker Desktop (installeur déjà téléchargé :
  `C:\DockerInstall\Docker Desktop Installer.exe`) → `docker compose up` fonctionnera **sans changement
  de code** (voir §4).

## 3. Lancer la stack NATIVE (aujourd'hui)

### Backend (FastAPI)
```
cd "E:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI\backend"
"E:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload
```
- Vérifier : http://127.0.0.1:8000/health → `{"status":"ok"}`
- Documentation auto (Swagger) : http://127.0.0.1:8000/docs

### Frontend (Vite)
```
cd "E:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI\frontend"
node node_modules\vite\bin\vite.js
```
- Vérifier : http://127.0.0.1:5173/

⚠️ **Ne pas utiliser `npm run dev` sur l'hôte** : le caractère `&` du chemin du projet
(`...\Chatbot & Calco\...`) casse les scripts npm (shims `.cmd`). Toujours utiliser
`node node_modules\vite\bin\vite.js` (vérifié). Alternative durable : renommer le dossier sans `&`.

## 4. Basculer vers Docker plus tard (zéro réécriture)

1. Réparer Windows (voir §2)
2. Installer Docker Desktop (installeur déjà sur `C:\DockerInstall\`)
3. Copier `.env.example` → `.env` et remplir les valeurs
4. **Changer UNE ligne dans `.env`** : `DB_URL` pointe vers `postgres` au lieu de `localhost`
   (natif : `@localhost:5432` — Docker : `@postgres:5432`)
5. `docker compose up` — même code, même base, aucun fichier à modifier

## 5. Structure du projet (créée en Phase 0)

- `backend/` : `app/main.py` (FastAPI + `GET /health`), `app/config.py` (Settings pydantic-settings),
  packages `auth/ models/ schemas/ routers/ services/ db/`, `requirements.txt`, `Dockerfile`
- `frontend/` : Vite React-TS (React 19, Vite 8, TS 6), react-router-dom + axios installés, `Dockerfile`
- Racine : `docker-compose.yml` (postgres `pgvector/pgvector:pg16`, backend, frontend),
  `.env.example`, `.gitignore`, `PROGRESS.md` (suivi d'état réel)

## 6. Points d'attention

1. PostgreSQL 16.10 + pgvector 0.8.6 natifs **installés et actifs** (base `dexter`, user `dexter`, port 5432) — `.env` créé avec valeurs de dev
2. Compte Windows « Invité » **activé** — à désactiver (sécurité, hors périmètre projet)
3. Redémarrer PostgreSQL après un reboot Windows :
   `"C:\Users\Edwin Jamel Kouokam\PostgreSQL\pgsql16\bin\pg_ctl.exe" -D "C:\Users\Edwin Jamel Kouokam\PostgreSQL\data" start`

## 7. Prochaines étapes

- [ ] **Phase MVP — Authentification** : inscription, connexion, profil étudiant/professeur, JWT
      (PRD §5.1 / §12.1)
- [ ] Détection de domaine générique (Comptabilité + Finance configurés)
- [ ] PostgreSQL + pgvector natif (quand la base est nécessaire)
- [ ] Réparation in situ Windows → retour à Docker (`docker compose up`)
