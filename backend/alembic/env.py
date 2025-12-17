from __future__ import annotations

import os
from logging.config import fileConfig

from alembic.operations import ops
from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.core.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _contains_drop_operations(migration_ops: ops.MigrateOperation) -> bool:
    if isinstance(
        migration_ops,
        (
            ops.DropTableOp,
            ops.DropColumnOp,
            ops.DropIndexOp,
            ops.DropConstraintOp,
        ),
    ):
        return True

    nested = getattr(migration_ops, "ops", None)
    if nested:
        return any(_contains_drop_operations(op) for op in nested)

    return False


def _prevent_unintended_drops(_context: context.MigrationContext, _revision, directives) -> None:
    if os.environ.get("ALLOW_ALEMBIC_DROPS") == "1":
        return

    if not directives:
        return

    script = directives[0]
    upgrade_ops = getattr(script, "upgrade_ops", None)
    if upgrade_ops is None:
        return

    if _contains_drop_operations(upgrade_ops):
        raise SystemExit(
            "Refusing to autogenerate a revision with drop_* operations. "
            "Ensure ORM models match the existing DB schema, or set "
            "ALLOW_ALEMBIC_DROPS=1 if you really intend to drop objects."
        )


def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    config.set_main_option("DATABASE_URL", url)
    config.set_main_option("sqlalchemy.url", url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        process_revision_directives=_prevent_unintended_drops,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    config.set_main_option("DATABASE_URL", settings.DATABASE_URL)
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            process_revision_directives=_prevent_unintended_drops,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
