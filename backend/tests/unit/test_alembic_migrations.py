import inspect
import re
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

import app.models  # noqa: F401 - registers all models on Base.metadata
from app.database import Base


def _script_directory():
    backend_dir = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    return ScriptDirectory.from_config(cfg)


def test_migration_chain_has_single_head():
    script = _script_directory()
    assert script.get_heads() == ["0009"]


def test_migration_chain_has_single_base():
    script = _script_directory()
    assert script.get_bases() == ["0001"]


def test_migrations_cover_every_registered_table():
    script = _script_directory()
    revisions = {rev.revision: rev for rev in script.walk_revisions()}
    assert set(revisions) == {"0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009"}

    created_tables = set()
    for rev in revisions.values():
        source = inspect.getsource(rev.module.upgrade)
        created_tables.update(re.findall(r'op\.create_table\(\s*"([^"]+)"', source))

    assert created_tables == set(Base.metadata.tables)
