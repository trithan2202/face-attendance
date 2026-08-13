"""Legacy helper kept to point developers to the migration workflow."""


def main():
    raise RuntimeError(
        "Không dùng create_all nữa. Hãy chạy scripts/migrate.ps1 hoặc "
        "python -m alembic upgrade head."
    )


if __name__ == "__main__":
    main()
