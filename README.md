# SolarAI Backend

## Vue d'ensemble

Ce projet est le backend FastAPI de **SolarAI**, une plateforme de dimensionnement et de monitoring photovoltaique.

Le backend expose les API pour :

- l authentification des utilisateurs ;
- la recommandation photovoltaique ;
- la generation de rapports PDF ;
- le chat assistant et son historique ;
- le monitoring et les alertes ;
- les notifications web push ;
- le formulaire de contact et les messages admin ;
- la recuperation des donnees solaires ;
- la persistance des donnees en base.

## Fonctionnalites principales

### Modules implementes

| Module | Description |
| --- | --- |
| Authentification | Inscription, connexion et recuperation du profil courant avec JWT. |
| Gestion utilisateur | Utilisateur courant, roles admin, et donnees de session. |
| Recommendation PV | Calcul et formatage des recommandations photovoltaques. |
| PDF | Generation de rapports PDF pour les recommandations et les rapports sauvegardes. |
| Rapports sauvegardes | Liste, consultation et telechargement des rapports de simulation. |
| Chat | Endpoint de chat, historique de conversation, sessions et suppression des sessions. |
| Monitoring | Simulation, statut de systeme, detection d anomalies, alertes et confirmation. |
| Notifications | Preferences, abonnement/desabonnement web push, lecture et test de notifications. |
| Contact | Formulaire de contact avec sauvegarde en base et envoi email si SMTP est configure. |
| Admin contact | Consultation, mise a jour du statut et suppression des messages de contact. |
| Donnees solaires | Recuperation des donnees PVGIS pour la carte solaire et les pages de calcul. |
| Base de donnees | SQLAlchemy pour les modeles et la persistance PostgreSQL. |
| Migrations | Alembic est present pour les migrations de schema. |

### Utilitaires supplementaires

Le projet contient aussi un module de recherche de magasins base sur un jeu de donnees local. Il est separe de la fonctionnalite retiree de magasins solaires/Geoapify.

## Structure du projet

| Dossier | Rôle |
| --- | --- |
| `app/api/routes` | Routes FastAPI exposees par le backend. |
| `app/models` | Modeles SQLAlchemy. |
| `app/schemas` | Schemas Pydantic pour les entrees et sorties API. |
| `app/services` | Logique metier. |
| `app/core` | Fonctions transversales comme la securite, les exceptions et les middlewares. |
| `app/config.py` | Configuration de l application et variables d environnement. |
| `app/db` | Session SQLAlchemy, base declarative et initialisation de la base. |
| `pdf` | Generation des rapports PDF. |
| `alembic` | Migrations de base de donnees. |
| `data` | Fichiers de reference et jeux de donnees. |
| `tests` | Tests automatises. |
| `generated_reports` | PDFs generes au runtime. |

## Endpoints principaux

### Routes sous `/api/v1`

| Groupe | Endpoints |
| --- | --- |
| Auth | `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me` |
| Recommendation | `POST /api/v1/recommendation/pv`, `POST /api/v1/recommendation/pdf`, `POST /api/v1/recommendation/save`, `GET /api/v1/recommendation/latest-saved` |
| Reports | `GET /api/v1/reports/my-reports`, `GET /api/v1/reports/{report_id}`, `GET /api/v1/reports/{report_id}/pdf` |
| Monitoring | `POST /api/v1/monitoring/simulate`, `GET /api/v1/monitoring/status/{simulation_id}`, `POST /api/v1/monitoring/detect-anomalies`, `POST /api/v1/monitoring/notify-current-alert`, `GET /api/v1/monitoring/alerts`, `POST /api/v1/monitoring/predict`, `GET /api/v1/monitoring/my-simulation`, `POST /api/v1/monitoring/confirm` |
| Notifications | `GET /api/v1/notifications/preferences`, `PUT /api/v1/notifications/preferences`, `POST /api/v1/notifications/subscribe`, `POST /api/v1/notifications/unsubscribe`, `GET /api/v1/notifications`, `POST /api/v1/notifications/{notification_id}/read`, `POST /api/v1/notifications/test` |
| Contact | `POST /api/v1/contact` |
| Admin | `GET /api/v1/admin/contact-messages`, `GET /api/v1/admin/contact-messages/{message_id}`, `PATCH /api/v1/admin/contact-messages/{message_id}/status`, `DELETE /api/v1/admin/contact-messages/{message_id}` |
| Solar data | `GET /api/v1/solar-data` |
| Agent | `POST /api/v1/agent/run`, `POST /api/v1/agent/execute-tool`, `GET /api/v1/agent/tools` |
| Chat | `POST /api/v1/chat/`, `GET /api/v1/chat/history`, `POST /api/v1/chat/messages`, `DELETE /api/v1/chat/history`, `GET /api/v1/chat/sessions`, `GET /api/v1/chat/sessions/{session_id}/messages`, `DELETE /api/v1/chat/sessions/{session_id}`, `DELETE /api/v1/chat/sessions` |
| Stores | `POST /api/v1/stores/nearby`, `GET /api/v1/stores/`, `GET /api/v1/stores/{store_id}` |

### Routes definies dans `app/main.py`

| Endpoint | Description |
| --- | --- |
| `GET /` | Page d accueil simple de l API. |
| `GET /health` | Health check. |
| `POST /calculate` | Calcul solaire legacy/compatibilite. |
| `POST /chat` | Endpoint de chat utilise par le floating chat. |
| `GET /chat/sessions` | Liste des sessions de chat. |
| `GET /chat/sessions/{session_id}/messages` | Messages d une session de chat. |
| `DELETE /chat/sessions/{session_id}` | Suppression d une session de chat. |
| `DELETE /chat/sessions` | Suppression de toutes les sessions. |
| `GET /chat/history` | Historique de chat. |
| `POST /chat/messages` | Sauvegarde d un message de chat. |
| `DELETE /chat/history` | Nettoyage de l historique de chat. |
| `POST /generate-pdf` | Generation PDF legacy. |
| `GET /download-pdf/{file_name}` | Telechargement du PDF legacy. |
| `POST /monitoring/simulate` | Simulation monitoring legacy. |

## Variables d environnement

Le backend lit les variables suivantes depuis `app/config.py`.

### Application et infrastructure

| Variable | Usage |
| --- | --- |
| `PROJECT_NAME` | Nom de l API. |
| `PROJECT_VERSION` | Version exposee par l application. |
| `API_PREFIX` | Prefix global des routes API. |
| `ENVIRONMENT` | Environnement courant. |
| `DEBUG` | Mode debug. |
| `FRONTEND_URL` | URL du frontend. |
| `BACKEND_URL` | URL du backend. |
| `CORS_ORIGINS` | Origines CORS autorisees. |
| `LOG_LEVEL` | Niveau de log. |

### Base de donnees et securite

| Variable | Usage |
| --- | --- |
| `DATABASE_URL` | Connexion PostgreSQL. |
| `SECRET_KEY` | Cle JWT / securite. |
| `ALGORITHM` | Algorithme JWT. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duree de vie des tokens. |

### LLM et assistant

| Variable | Usage |
| --- | --- |
| `LLM_PROVIDER` | Fournisseur LLM. |
| `LLM_MODEL` | Modele LLM. |
| `LLM_TEMPERATURE` | Temperature de generation. |
| `LLM_MAX_TOKENS` | Limite de tokens LLM. |
| `OPENAI_API_KEY` | Cle OpenAI si utilisee. |
| `GROQ_API_KEY` | Cle Groq si utilisee. |
| `OLLAMA_BASE_URL` | URL du service Ollama. |

### Donnees solaires et reference

| Variable | Usage |
| --- | --- |
| `NSRDB_API_KEY` | Cle NSRDB si utilisee. |
| `NSRDB_BASE_URL` | Base URL NSRDB. |
| `DEFAULT_NSRDB_YEAR` | Annee par defaut NSRDB. |
| `NSRDB_TIMEOUT_SECONDS` | Timeout NSRDB. |
| `NSRDB_INTERVAL_MINUTES` | Intervalle NSRDB. |
| `PVGIS_BASE_URL` | Base URL PVGIS. |
| `PVGIS_TIMEOUT_SECONDS` | Timeout PVGIS. |
| `PANELS_DATA_PATH` | Fichier CSV panneaux. |
| `BATTERIES_DATA_PATH` | Fichier CSV batteries. |
| `INVERTERS_DATA_PATH` | Fichier CSV onduleurs. |
| `PRICES_DATA_PATH` | Fichier CSV prix. |
| `STORES_DATA_PATH` | Fichier CSV magasins. |
| `SOLAR_DATA_DIR` | Dossier des donnees solaires. |
| `SIMULATION_DATA_PATH` | Donnees de simulation monitoring. |
| `RAG_DOCS_DIR` | Documents RAG. |
| `VECTOR_STORE_DIR` | Repertoire du vector store. |
| `PV_RECOMMENDATION_MODEL_PATH` | Modele de recommandation PV. |

### Parametres metier

| Variable | Usage |
| --- | --- |
| `DEFAULT_PERFORMANCE_RATIO` | Hypothese par defaut. |
| `DEFAULT_BATTERY_DOD` | Profondeur de decharge par defaut. |
| `DEFAULT_BATTERY_EFFICIENCY` | Rendement batterie par defaut. |
| `DEFAULT_INVERTER_MARGIN` | Marge onduleur par defaut. |
| `DEFAULT_ELECTRICITY_PRICE` | Prix de l electricite par defaut. |
| `DEFAULT_SYSTEM_LOSSES` | Pertes systeme par defaut. |
| `DEFAULT_SHADE_FACTOR` | Facteur d ombrage par defaut. |
| `EXPOSE_RAW_ML_RESPONSE` | Exposition de la reponse ML brute. |

### Notifications et contact

| Variable | Usage |
| --- | --- |
| `WEB_PUSH_VAPID_PRIVATE_KEY` | Cle privee VAPID. |
| `WEB_PUSH_VAPID_PUBLIC_KEY` | Cle publique VAPID. |
| `WEB_PUSH_VAPID_EMAIL` | Contact associe aux notifications web push. |
| `SMTP_HOST` | Serveur SMTP. |
| `SMTP_PORT` | Port SMTP. |
| `SMTP_USER` | Utilisateur SMTP. |
| `SMTP_PASSWORD` | Mot de passe SMTP. |
| `SMTP_FROM_EMAIL` | Adresse expediteur. |
| `CONTACT_RECEIVER_EMAIL` | Adresse recevant les messages de contact. |

## Installation et execution

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Base de donnees

Le projet utilise PostgreSQL.

Etapes recommandees:

```sql
CREATE DATABASE pv_assistant;
```

Puis appliquer les migrations Alembic:

```bash
alembic upgrade head
```

Le fichier `app/main.py` appelle aussi `Base.metadata.create_all(...)` au demarrage, mais Alembic reste la voie a privilegier pour gerer le schema.

## Rapports PDF

- Les rapports PDF sont generes dans `generated_reports/`.
- Les PDFs de recommandations sont crees par `/api/v1/recommendation/pdf`.
- Les rapports sauvegardes peuvent stocker `report_pdf_path` et `report_pdf_filename` pour etre telecharges plus tard via `/api/v1/reports/{report_id}/pdf`.
- Le module `pdf/` contient la logique de generation des pages PDF.

## Contact SMTP

- Les messages du formulaire de contact sont enregistres en base.
- Si `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` et `SMTP_FROM_EMAIL` sont renseignes, le backend peut aussi envoyer un email de notification.
- Si Gmail est utilise comme SMTP, un mot de passe d application est requis.

## Tests

Le dossier `tests/` est present.

Pour lancer les tests:

```bash
pytest
```

