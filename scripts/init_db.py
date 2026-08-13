from backend.app.core.database import Base, engine
import backend.app.models


def main():
    Base.metadata.create_all(
        bind=engine
    )

    print("[OK] Database tables created")


if __name__ == "__main__":
    main()