"""Aplica las políticas RLS (backend/sql/rls_policies.sql) a la base.

Usa el engine async del backend (mismo DATABASE_URL + SSL de Supabase). El SQL
es idempotente, así que se puede correr varias veces sin efectos secundarios.

Uso:  python -m scripts.apply_rls
"""

import asyncio
import pathlib
import re

from sqlalchemy import text

from app.database import engine

SQL_FILE = pathlib.Path(__file__).resolve().parent.parent / "sql" / "rls_policies.sql"


def split_statements(sql: str) -> list[str]:
    """Quita comentarios de línea y divide en sentencias por ';'."""
    no_comments = "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    )
    return [s.strip() for s in re.split(r";\s*\n", no_comments) if s.strip()]


async def main() -> None:
    statements = split_statements(SQL_FILE.read_text(encoding="utf-8"))
    print(f"Aplicando {len(statements)} sentencias de {SQL_FILE.name}...\n")

    async with engine.begin() as conn:
        for i, stmt in enumerate(statements, 1):
            label = " ".join(stmt.split())[:70]
            await conn.exec_driver_sql(stmt)
            print(f"  [{i:2}/{len(statements)}] OK  {label}")

    # Verificación: listar políticas creadas.
    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "select tablename, policyname, cmd from pg_policies "
                    "where schemaname = 'public' order by tablename, policyname"
                )
            )
        ).all()

    print(f"\nPolíticas activas en public ({len(rows)}):")
    for table, policy, cmd in rows:
        print(f"  - {table:14} {cmd:6} {policy}")

    await engine.dispose()
    print("\nListo. RLS habilitado.")


if __name__ == "__main__":
    asyncio.run(main())
