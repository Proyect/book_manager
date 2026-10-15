#@title Escritura de connection.py
"""Conexión a la base de datos de Book Manager.

Define la clase ConexionDB, única responsable de crear el engine de
SQLAlchemy y de entregar conexiones al resto del sistema. Se usa SQLite
con la notación vista en la cursada: create_engine, connect y text().
"""
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.sql import text

RUTA_BASE_POR_DEFECTO: Path = (
    Path(__file__).resolve().parent.parent / "data" / "book_manager.db"
)
URL_POR_DEFECTO: str = f"sqlite:///{RUTA_BASE_POR_DEFECTO}"


class ConexionDB:
    """Administra el engine de SQLAlchemy y entrega conexiones.

    El engine es privado: la única forma de obtener una conexión es
    conectar(), que además activa las claves foráneas en SQLite.
    """

    def __init__(self, url: Optional[str] = None, echo: bool = False) -> None:
        """Crea el engine de la base de datos.

        Args:
            url (Optional[str]): URL de conexión de SQLAlchemy. Si es None,
                se usa la base SQLite del proyecto en la carpeta data.
            echo (bool): Si es True, SQLAlchemy muestra cada sentencia SQL
                ejecutada (útil para depurar).

        Raises:
            TypeError: Si la URL no es un texto o echo no es booleano.
            ValueError: Si la URL está vacía o no es una URL válida.
        """
        if not isinstance(echo, bool):
            raise TypeError("El parámetro 'echo' debe ser de tipo bool.")
        self.__url: str = self._validar_url(
            URL_POR_DEFECTO if url is None else url
        )
        self._crear_directorio_sqlite()
        self.__engine: Optional[Engine] = create_engine(self.__url, echo=echo)

    @property
    def url(self) -> str:
        """URL de conexión a la base de datos (solo lectura)."""
        return self.__url

    @property
    def activa(self) -> bool:
        """Indica si el engine sigue disponible (no se llamó a cerrar)."""
        return self.__engine is not None

    @staticmethod
    def _validar_url(url: str) -> str:
        """Valida que la URL sea un texto no vacío con formato válido.

        Args:
            url (str): URL de conexión a validar.

        Returns:
            str: La URL sin espacios al principio ni al final.

        Raises:
            TypeError: Si la URL no es de tipo str.
            ValueError: Si la URL está vacía o SQLAlchemy no la reconoce.
        """
        if not isinstance(url, str):
            raise TypeError("La URL de conexión debe ser de tipo str.")
        url_limpia: str = url.strip()
        if not url_limpia:
            raise ValueError("La URL de conexión no puede estar vacía.")
        try:
            make_url(url_limpia)
        except ArgumentError as error:
            raise ValueError(
                f"La URL de conexión no es válida: {url_limpia}"
            ) from error
        return url_limpia

    def _crear_directorio_sqlite(self) -> None:
        """Crea la carpeta del archivo SQLite si todavía no existe."""
        url_parseada = make_url(self.__url)
        archivo: Optional[str] = url_parseada.database
        if (url_parseada.get_backend_name() == "sqlite"
                and archivo not in (None, "", ":memory:")):
            Path(archivo).parent.mkdir(parents=True, exist_ok=True)

    def conectar(self) -> Connection:
        """Abre una conexión nueva a la base de datos.

        En SQLite ejecuta PRAGMA foreign_keys = ON, porque el motor no
        aplica las claves foráneas por defecto.

        Returns:
            Connection: Conexión lista para usar. Quien la pide es
            responsable de cerrarla.

        Raises:
            RuntimeError: Si la conexión ya fue cerrada con cerrar().
        """
        if self.__engine is None:
            raise RuntimeError("La conexión a la base de datos fue cerrada.")
        conexion: Connection = self.__engine.connect()
        if self.__engine.dialect.name == "sqlite":
            conexion.execute(text("PRAGMA foreign_keys = ON"))
            conexion.commit()
        return conexion

    def cerrar(self) -> None:
        """Libera el engine y todas sus conexiones del pool."""
        if self.__engine is not None:
            self.__engine.dispose()
            self.__engine = None

    def __repr__(self) -> str:
        """Representación técnica de la conexión."""
        estado: str = "activa" if self.activa else "cerrada"
        return f"ConexionDB(url={self.__url!r}, {estado})"
