from services.migration_service import MigrationService


def get_migration_service() -> MigrationService:
    return MigrationService()
