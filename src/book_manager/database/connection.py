"""Conexión a la base de datos relacional mediante el ORM SQLAlchemy.

La URL de la base se toma de la variable ``DATABASE_URL`` del archivo
``.env``; si no está definida se usa una base SQLite local dentro de la
carpeta ``data`` del paquete.
"""

import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
DIRECTORIO_DATOS = Path(__file__).resolve().parents[1] / "data"
URL_POR_DEFECTO = f"sqlite:///{DIRECTORIO_DATOS / 'book_manager.db'}"

load_dotenv(RAIZ_PROYECTO / ".env")


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos ORM."""


def _activar_claves_foraneas(conexion_dbapi: Any, _registro: Any) -> None:
    """Habilita el control de claves foráneas en SQLite."""
    cursor = conexion_dbapi.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class ConexionDB:
    """Administra el engine y la creación de sesiones de SQLAlchemy."""

    def __init__(self, url: Optional[str] = None, echo: bool = False) -> None:
        """Crea el engine a partir de la URL indicada o la del .env.

        Args:
            url (Optional[str]): URL de conexión. Si es None se usa
                DATABASE_URL del .env o, en su defecto, SQLite local.
            echo (bool): Si es True muestra las sentencias SQL ejecutadas.
        """
        self._url = url or os.getenv("DATABASE_URL") or URL_POR_DEFECTO
        if self._url.startswith("sqlite"):
            DIRECTORIO_DATOS.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(self._url, echo=echo)
        if self._engine.dialect.name == "sqlite":
            event.listen(self._engine, "connect", _activar_claves_foraneas)
        self._fabrica = sessionmaker(bind=self._engine,
                                     expire_on_commit=False)

    @property
    def url(self) -> str:
        """URL de conexión (sin mostrar la contraseña)."""
        return self._engine.url.render_as_string(hide_password=True)

    @property
    def engine(self) -> Engine:
        """Engine de SQLAlchemy."""
        return self._engine

    def nueva_sesion(self) -> Session:
        """Devuelve una sesión nueva (quien la usa debe cerrarla)."""
        return self._fabrica()

    def probar_conexion(self) -> bool:
        """Ejecuta una consulta simple para verificar la conexión."""
        with self._engine.connect() as conexion:
            conexion.execute(text("SELECT 1"))
        return True

    def crear_tablas(self) -> None:
        """Crea las tablas de los modelos que todavía no existen."""
        import book_manager.models.models  # noqa: F401  (registra modelos)
        Base.metadata.create_all(self._engine)

    def eliminar_tablas(self) -> None:
        """Elimina todas las tablas de los modelos."""
        import book_manager.models.models  # noqa: F401  (registra modelos)
        Base.metadata.drop_all(self._engine)

    def existe_tabla(self, nombre: str) -> bool:
        """Indica si la tabla existe en la base de datos."""
        return inspect(self._engine).has_table(nombre)

    def cerrar(self) -> None:
        """Libera las conexiones del engine."""
        self._engine.dispose()

    def __repr__(self) -> str:
        """Representación técnica de la conexión."""
        return f"ConexionDB(url={self.url!r})"
