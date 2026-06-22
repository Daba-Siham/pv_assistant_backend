# PV Intelligent Assistant Backend

## 1. Description du projet

Ce backend fait partie d’un projet PFA intitulé **Assistant Intelligent pour le Dimensionnement et le Monitoring d’un Système Photovoltaïque**.

L’objectif du projet est de développer une application intelligente capable de :

- aider l’utilisateur à dimensionner une installation photovoltaïque ;
- estimer le nombre de panneaux, batteries et onduleurs nécessaires ;
- calculer le coût total et le retour sur investissement ;
- recommander des magasins ou fournisseurs proches ;
- simuler le fonctionnement du système photovoltaïque ;
- détecter des anomalies comme une panne, une batterie faible ou une surcharge ;
- fournir des explications simples à l’utilisateur via un chatbot intelligent.

Le backend est développé avec **FastAPI** et communique avec le frontend React à travers des routes API REST.

---

## 2. Technologies utilisées

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- JWT Authentication
- Pandas
- Scikit-learn
- RAG
- LLM
- Pytest

---

## 3. Rôle du backend

Le backend est responsable de :

- gérer les routes API ;
- gérer l’authentification des utilisateurs ;
- stocker les données dans PostgreSQL ;
- gérer l’historique des conversations ;
- exécuter les calculs photovoltaïques ;
- récupérer les données solaires ;
- exécuter l’agent intelligent ;
- gérer le chatbot et le RAG ;
- simuler le monitoring ;
- détecter les anomalies ;
- générer les alertes ;
- retourner les résultats au frontend.

---

## 4. Architecture du backend

```text
backend/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── chat.py
│   │       ├── agent.py
│   │       ├── calculation.py
│   │       ├── monitoring.py
│   │       ├── solar.py
│   │       └── stores.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── agent.py
│   │   ├── calculation.py
│   │   ├── monitoring.py
│   │   ├── solar.py
│   │   └── store.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── chat_history.py
│   │   ├── simulation_result.py
│   │   └── monitoring_event.py
│   │
│   ├── services/
│   │   ├── auth/
│   │   ├── llm/
│   │   ├── rag/
│   │   ├── agent/
│   │   ├── calculation/
│   │   ├── monitoring/
│   │   └── shared/
│   │
│   ├── tools/
│   │   ├── get_solar_data.py
│   │   ├── estimate_panels.py
│   │   ├── estimate_batteries.py
│   │   ├── estimate_inverter.py
│   │   ├── estimate_cost.py
│   │   ├── calculate_roi.py
│   │   ├── find_stores.py
│   │   ├── simulate_system.py
│   │   ├── detect_anomalies.py
│   │   └── predict_energy.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── init_db.py
│   │
│   └── core/
│       ├── security.py
│       ├── exceptions.py
│       └── middleware.py
│
├── data/
│   ├── solar/
│   ├── materials/
│   ├── stores/
│   ├── simulations/
│   └── rag_docs/
│
├── tests/
│   ├── test_chat.py
│   ├── test_agent.py
│   ├── test_calculation.py
│   └── test_monitoring.py
│
├── requirements.txt
├── .env
└── README.md
````

---

## 5. Description des dossiers

### `app/api`

Ce dossier contient toutes les routes API du backend.

Exemples :

* `/auth` : authentification ;
* `/chat` : chatbot ;
* `/agent` : agent intelligent ;
* `/calculation` : calcul photovoltaïque ;
* `/monitoring` : monitoring simulé ;
* `/solar` : données solaires ;
* `/stores` : magasins et fournisseurs.

---

### `app/schemas`

Ce dossier contient les modèles Pydantic utilisés pour valider les données entrantes et sortantes.

Exemple :

* données envoyées par l’utilisateur ;
* résultats de calcul ;
* réponses du chatbot ;
* résultats du monitoring ;
* données d’authentification.

---

### `app/models`

Ce dossier contient les modèles SQLAlchemy correspondant aux tables PostgreSQL.

Tables principales :

* `users`
* `chat_histories`
* `simulation_results`
* `monitoring_events`

---

### `app/services`

Ce dossier contient la logique métier du backend.

Il contient plusieurs modules :

* `auth` : inscription, connexion, JWT ;
* `llm` : chatbot et génération de réponse ;
* `rag` : recherche documentaire ;
* `agent` : agent intelligent et décision ;
* `calculation` : calcul photovoltaïque ;
* `monitoring` : simulation, anomalies et alertes ;
* `shared` : fonctions communes, constantes et logger.

---

### `app/tools`

Ce dossier contient les outils appelés par l’agent intelligent.

Exemples :

* récupérer les données solaires ;
* estimer les panneaux ;
* estimer les batteries ;
* calculer le ROI ;
* détecter les anomalies ;
* prédire l’énergie ;
* chercher des magasins.

---

### `app/db`

Ce dossier gère la connexion à PostgreSQL.

Il contient :

* `session.py` : session SQLAlchemy ;
* `base.py` : base des modèles ;
* `init_db.py` : création des tables.

---

### `app/core`

Ce dossier contient les éléments transversaux du backend :

* sécurité ;
* gestion des exceptions ;
* middlewares ;
* logs.

---

### `data`

Ce dossier contient les fichiers de référence du projet.

Il ne contient pas les demandes utilisateurs.

Les demandes utilisateurs sont stockées dans PostgreSQL.

Exemples de fichiers :

* données solaires ;
* références panneaux ;
* références batteries ;
* références onduleurs ;
* prix ;
* magasins ;
* exemples de monitoring ;
* documents RAG.

---

## 6. Installation du projet

### 6.1 Cloner le projet

```bash
git clone <url-du-repository>
cd backend
```

---

### 6.2 Créer un environnement virtuel

Sur Windows :

```bash
python -m venv venv
venv\Scripts\activate
```

Sur Linux / Mac :

```bash
python -m venv venv
source venv/bin/activate
```

---

### 6.3 Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## 7. Configuration du fichier `.env`

Créer un fichier `.env` à la racine du backend.

Exemple :

```env
PROJECT_NAME=PV Intelligent Assistant API
PROJECT_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=True

FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000

DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/pv_assistant

SECRET_KEY=change-this-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

LLM_PROVIDER=ollama
LLM_MODEL=llama3
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1000

OPENAI_API_KEY=
GROQ_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434

NSRDB_API_KEY=

DEFAULT_PERFORMANCE_RATIO=0.75
DEFAULT_BATTERY_DOD=0.8
DEFAULT_BATTERY_EFFICIENCY=0.9
DEFAULT_INVERTER_MARGIN=1.25
DEFAULT_ELECTRICITY_PRICE=1.5
DEFAULT_SYSTEM_LOSSES=0.14
DEFAULT_SHADE_FACTOR=1.0

LOG_LEVEL=INFO
```

---

## 8. Préparation de la base de données

Créer une base PostgreSQL :

```sql
CREATE DATABASE pv_assistant;
```

Puis créer les tables :

```bash
python -m app.db.init_db
```

---

## 9. Lancer le backend

```bash
uvicorn app.main:app --reload
```

Le backend sera disponible sur :

```text
http://localhost:8000
```

Documentation Swagger :

```text
http://localhost:8000/docs
```

Health check :

```text
http://localhost:8000/health
```

---

## 10. Routes principales

### Authentification

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

---

### Chatbot

```text
POST   /api/v1/chat/
GET    /api/v1/chat/history
DELETE /api/v1/chat/history
```

---

### Agent intelligent

```text
POST /api/v1/agent/run
POST /api/v1/agent/execute-tool
GET  /api/v1/agent/tools
```

---

### Calcul photovoltaïque

```text
POST /api/v1/calculation/
POST /api/v1/calculation/panels
POST /api/v1/calculation/batteries
POST /api/v1/calculation/inverter
POST /api/v1/calculation/cost
POST /api/v1/calculation/roi
```

---

### Données solaires

```text
POST /api/v1/solar/data
GET  /api/v1/solar/cities
GET  /api/v1/solar/city/{city_name}
```

---

### Monitoring

```text
POST /api/v1/monitoring/simulate
GET  /api/v1/monitoring/status/{simulation_id}
POST /api/v1/monitoring/detect-anomalies
GET  /api/v1/monitoring/alerts
POST /api/v1/monitoring/predict
```

---

### Magasins

```text
POST /api/v1/stores/nearby
GET  /api/v1/stores/
GET  /api/v1/stores/{store_id}
```

---

## 11. Exemple de test API

### 11.1 Inscription

Route :

```text
POST /api/v1/auth/register
```

Body :

```json
{
  "full_name": "Test User",
  "email": "test@example.com",
  "password": "123456"
}
```

---

### 11.2 Connexion

Route :

```text
POST /api/v1/auth/login
```

Body :

```json
{
  "email": "test@example.com",
  "password": "123456"
}
```

---

### 11.3 Calcul photovoltaïque complet

Route :

```text
POST /api/v1/calculation/
```

Body :

```json
{
  "daily_consumption_kwh": 8,
  "city": "Nador",
  "latitude": 35.1688,
  "longitude": -2.9335,
  "available_area_m2": 30,
  "budget": 30000,
  "autonomy_days": 1,
  "installation_type": "hybride",
  "orientation": "sud",
  "tilt_angle": 30,
  "shade_factor": 0.9,
  "roof_type": "terrasse",
  "distance_to_load_m": 15
}
```

---

### 11.4 Simulation monitoring

Route :

```text
POST /api/v1/monitoring/simulate
```

Body :

```json
{
  "daily_consumption_kwh": 8,
  "panel_count": 6,
  "total_power_kwp": 2.7,
  "battery_capacity_kwh": 5,
  "scenario": "normal",
  "duration_hours": 24
}
```

---

### 11.5 Agent intelligent

Route :

```text
POST /api/v1/agent/run
```

Body :

```json
{
  "user_message": "Je veux dimensionner une installation solaire pour ma maison",
  "session_id": "test-session",
  "user_inputs": {
    "daily_consumption_kwh": 8,
    "city": "Nador",
    "latitude": 35.1688,
    "longitude": -2.9335,
    "available_area_m2": 30,
    "budget": 30000,
    "autonomy_days": 1,
    "installation_type": "hybride",
    "orientation": "sud",
    "tilt_angle": 30,
    "shade_factor": 0.9,
    "roof_type": "terrasse",
    "distance_to_load_m": 15
  }
}
```

---

## 12. Fonctionnement du dimensionnement

Le dimensionnement utilise une logique hybride :

```text
calcul physique + modèle ML déjà entraîné
```

Dans la version actuelle, le backend utilise surtout les calculs physiques.

Le modèle ML peut être ajouté ensuite dans un dossier séparé :

```text
ml/
├── training/
├── models/
└── notebooks/
```

Le backend ne doit pas réentraîner le modèle à chaque requête.
Il doit seulement charger un modèle déjà entraîné et l’utiliser pour prédire ou optimiser les résultats.

---

## 13. Fonctionnement du monitoring

Le monitoring est simulé.

Il permet de générer :

* production solaire ;
* consommation ;
* niveau de batterie ;
* température ;
* statut système ;
* alertes.

Scénarios possibles :

```text
normal
panne
surcharge
meteo_defavorable
ombrage
```

---

## 14. Fonctionnement du chatbot

Le chatbot utilise :

* un service LLM ;
* un prompt système ;
* un historique de conversation ;
* un contexte RAG.

Le chatbot doit expliquer les résultats de manière simple, mais il ne doit pas inventer les résultats techniques.

Les calculs doivent venir des services backend.

---

## 15. Fonctionnement du RAG

Le RAG utilise des documents stockés dans :

```text
data/rag_docs/
```

Exemples :

```text
guide_installation.md
conseils_batteries.md
guide_panneaux.md
faq_photovoltaique.md
```

Le RAG permet au chatbot de répondre avec un contexte technique plus fiable.

---

## 16. Fonctionnement de l’agent intelligent

L’agent intelligent suit ce flux :

```text
1. recevoir la demande utilisateur
2. analyser l’intention
3. choisir le bon outil
4. exécuter l’outil
5. retourner le résultat
6. proposer des recommandations
```

Exemples :

```text
demande de dimensionnement → calculate_pv_system
demande de données solaires → get_solar_data
demande de panne → detect_anomalies
demande de monitoring → simulate_system
demande de magasins → find_stores
```

---

## 17. Tests

Les tests sont dans le dossier :

```text
tests/
```

Pour lancer tous les tests :

```bash
pytest
```

Pour lancer avec détails :

```bash
pytest -v
```

---

## 18. Dépendances principales

Exemple de `requirements.txt` :

```txt
fastapi
uvicorn
sqlalchemy
psycopg2-binary
pydantic
pydantic-settings
requests
pandas
scikit-learn
pypdf
python-jose
passlib[bcrypt]
python-multipart
email-validator
pytest
httpx
```

---

## 19. Règles de développement

Pour garder le backend propre :

* les routes API ne doivent pas contenir beaucoup de logique ;
* la logique métier doit être dans `services/` ;
* les données entrantes doivent passer par `schemas/` ;
* les tables doivent être définies dans `models/` ;
* les appels de l’agent doivent passer par `tools/` ;
* les données utilisateurs doivent être stockées dans PostgreSQL ;
* les fichiers CSV servent seulement de données de référence ;
* le LLM ne doit pas inventer les résultats techniques ;
* chaque fonctionnalité importante doit être testée.

---

## 20. Organisation Git conseillée

Branches proposées :

```text
main
develop
feature/auth
feature/calculation
feature/monitoring
feature/agent
feature/chatbot
feature/rag
feature/frontend-integration
```

Règles :

* ne pas travailler directement sur `main` ;
* créer une branche par fonctionnalité ;
* faire une Pull Request vers `develop` ;
* tester avant de merger.

---

## 21. Améliorations futures

Fonctionnalités à ajouter plus tard :

* intégration du vrai modèle ML entraîné ;
* chargement d’un fichier `.pkl` ;
* connexion réelle à l’API NSRDB ;
* génération de devis PDF ;
* amélioration du RAG avec FAISS ;
* amélioration du choix automatique du matériel ;
* ajout d’un dashboard admin ;
* ajout de Docker ;
* connexion complète avec le frontend React ;
* notifications email ou temps réel.

---

## 22. Résumé final

Ce backend est organisé en plusieurs couches :

```text
Routes API
   ↓
Schemas
   ↓
Services
   ↓
Tools / Agent / LLM / RAG
   ↓
Base de données / Datasets
```

Cette architecture permet d’avoir un backend :

* clair ;
* organisé ;
* évolutif ;
* testable ;
* facile à partager avec l’équipe.

```
```

**************partMer
# PV Intelligent Assistant - Guide d'installation et d'exécution

## 1. Cloner le projet depuis GitHub

### Backend

```bash
git clone LinK
```

### Frontend

```bash
git clone Link
```

Ou bien :

```bash
git clone Link
```

si le projet contient frontend et backend dans le même dépôt.

---

# 2. Structure du projet

```text
solarAssistant/
│
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

# 3. Configuration du Backend

## Création de l'environnement virtuel

Depuis le dossier backend :

```cmd
python -m venv .venv
```

Activation :

```cmd
.venv\Scripts\activate
```

---

## Installation des dépendances

```cmd
pip install -r requirements.txt
```

Vérification :

```cmd
pip list
```

---

# 4. Configuration de PostgreSQL

## Vérification de PostgreSQL

Vérifier que le service PostgreSQL est démarré :

```powershell
Get-Service *postgres*
```

Vérifier l'emplacement de psql :

```cmd
dir "C:\Program Files\PostgreSQL" /s /b | findstr psql.exe
```

Connexion à PostgreSQL :

```cmd
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres
```

---

## Création de la base de données

Dans PostgreSQL :

```sql
CREATE DATABASE pv_assistant;
```

Vérification :

```sql
SELECT datname FROM pg_database WHERE datname = 'pv_assistant';
```

Connexion à la base :

```sql
\c pv_assistant
```

---

## Configuration du fichier .env

Créer un fichier :

```env
DATABASE_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@localhost:5432/pv_assistant

SECRET_KEY=votre_secret_key

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

# 5. Migrations Alembic

Génération des migrations :

```cmd
alembic revision --autogenerate -m "create tables"
```

Application :

```cmd
alembic upgrade head
```

---

## Vérification des tables

Connexion PostgreSQL :

```cmd
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres
```

Puis :

```sql
\c pv_assistant
\dt
```

Résultat attendu :

```text
alembic_version
users
chat_histories
simulation_results
monitoring_events
```

---

# 6. Mise à jour du projet

Si des modifications locales existent :

```cmd
git stash -u
git pull
git stash pop
```

Vérifier :

```cmd
git status
```

---

# 7. Lancement du Backend

Depuis le dossier backend :

```cmd
uvicorn app.main:app --reload
```

ou :

```cmd
python -m uvicorn app.main:app --reload
```

Backend disponible sur :

```text
http://localhost:8000
```

Documentation Swagger :

```text
http://localhost:8000/docs
```

---

# 8. Configuration du Frontend

Se placer dans le dossier frontend :

```cmd
cd frontend
```

Installer les dépendances :

```cmd
npm install
```

ou :

```cmd
npm install --legacy-peer-deps
```

si nécessaire.

---

# 9. Lancement du Frontend

```cmd
npm run dev
```

Application disponible sur :

```text
http://localhost:5173
```

---

# 10. Vérification complète

Backend :

```text
http://localhost:8000/docs
```

Frontend :

```text
http://localhost:5173
```

Tester :

* Inscription
* Connexion
* Assistant IA
* Génération de rapport photovoltaïque
* Monitoring
* Historique

---

# Résultat final

Le projet est correctement installé lorsque :

✅ PostgreSQL fonctionne

✅ La base pv_assistant existe

✅ Les migrations Alembic sont appliquées

✅ Les tables sont créées

✅ Le backend FastAPI démarre

✅ Le frontend React/Vite démarre

✅ L'application est accessible depuis le navigateur

Tables attendues :

* users
* chat_histories
* simulation_results
* monitoring_events
* alembic_version

L'équipe peut désormais développer et exécuter le projet localement.
