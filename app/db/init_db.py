from app.db.base import Base
from app.db.session import engine
from sqlalchemy import inspect

# Import des modèles
from app.models.user import User
from app.models.chat_history import ChatHistory
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.simulation_result import SimulationResult
from app.models.monitoring_event import MonitoringEvent


def tables_exist():
    inspector = inspect(engine)
    return inspector.get_table_names()


def init_db():
    print("🚀 Initialisation de la base...")

    existing_tables = tables_exist()

    if existing_tables:
        print(f"📦 Tables déjà existantes : {existing_tables}")
    else:
        print("📭 Aucune table trouvée, création en cours...")

    Base.metadata.create_all(bind=engine)

    print("✅ Base prête (aucune destruction effectuée)")


if __name__ == "__main__":
    init_db()
