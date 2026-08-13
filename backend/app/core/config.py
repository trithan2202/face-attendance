import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://face_user:face_password@localhost:5432/face_attendance"
    )

    CAMERA_INDEX = int(
        os.getenv("CAMERA_INDEX", "0")
    )

    FACE_SIMILARITY_THRESHOLD = float(
        os.getenv("FACE_SIMILARITY_THRESHOLD", "0.50")
    )


settings = Settings()