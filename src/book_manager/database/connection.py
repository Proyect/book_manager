#@title Escritura de connection.py
"""Conexión a la base de datos de Book Manager.

Define la clase ConexionDB, única responsable de crear el engine de
SQLAlchemy y de entregar conexiones al resto del sistema, y el context
manager Transaccion, que confirma o deshace los cambios de un bloque de
código. Si se abre una transacción mientras otra está en curso sobre la
misma ConexionDB, la interna se suma a la externa (transacción compartida).
Por defecto se conecta a PostgreSQL en Supabase con las credenciales del
archivo .env; sin ellas, usa una base SQLite local.
"""
from pathlib import Path
from types import TracebackType
from typing import Any, Dict, Optional, Type

from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine, RootTransaction, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.sql import text

RUTA_BASE_POR_DEFECTO: Path = (
    Path(__file__).resolve().parent.parent / "data" / "book_manager.db"
)
URL_POR_DEFECTO: str = f"sqlite:///{RUTA_BASE_POR_DEFECTO}"
RUTA_ENV: Path = Path(__file__).resolve().parents[3] / ".env"
MARCADOR_CONTRASENA: str = "[YOUR-PASSWORD]"


def url_desde_env(ruta_env: Path = RUTA_ENV) -> str:
    """Arma la URL de la base a partir del archivo .env.

    Usa SQLALCHEMY_DATABASE_URL (con el marcador [YOUR-PASSWORD], como en
    la guía de la cátedra) y SUPABASE_DB_PASSWORD. La contraseña se inserta
    con make_url, que escapa los caracteres especiales.

    Args:
        ruta_env (Path): Ruta del archivo .env.

    Returns:
        str: La URL de Supabase con la contraseña, o la URL de la base
        SQLite local si el .env no define las dos variables.
    """
    if not ruta_env.is_file():
        return URL_POR_DEFECTO
    variables: Dict[str, Optional[str]] = dotenv_values(ruta_env)
    url: str = (variables.get("SQLALCHEMY_DATABASE_URL") or "").strip()
    contrasena: str = variables.get("SUPABASE_DB_PASSWORD") or ""
    if not url or not contrasena:
        return URL_POR_DEFECTO
    url_sin_marcador: str = url.replace(MARCADOR_CONTRASENA, "x")
    return make_url(url_sin_marcador).set(password=contrasena).render_as_string(
        hide_password=False
    )


class ConexionDB:
    """Administra el engine de SQLAlchemy y entrega conexiones.

    El engine es privado: la única forma de obtener una conexión es
    conectar(), que además activa las claves foráneas en SQLite. Para
    operar dentro de una transacción se usa transaccion().
    """

    def __init__(self, url: Optional[str] = None, echo: bool = False) -> None:
        """Crea el engine de la base de datos.

        Args:
            url (Optional[str]): URL de conexión de SQLAlchemy. Si es None,
                se arma desde el .env (Supabase) o, sin credenciales, se usa
                la base SQLite del proyecto en la carpeta data.
            echo (bool): Si es True, SQLAlchemy muestra cada sentencia SQL
                ejecutada (útil para depurar).

        Raises:
            TypeError: Si la URL no es un texto o echo no es booleano.
            ValueError: Si la URL está vacía o no es una URL válida.
        """
        if not isinstance(echo, bool):
            raise TypeError("El parámetro 'echo' debe ser de tipo bool.")
        self.__url: str = self._validar_url(
            url_desde_env() if url is None else url
        )
        self._crear_directorio_sqlite()
        opciones: Dict[str, Any] = {"echo": echo}
        if make_url(self.__url).get_backend_name() != "sqlite":
            opciones["pool_pre_ping"] = True
        self.__engine: Optional[Engine] = create_engine(self.__url, **opciones)
        self.__conexion_en_curso: Optional[Connection] = None

    @property
    def url(self) -> str:
        """URL de conexión con la contraseña oculta (solo lectura)."""
        return make_url(self.__url).render_as_string(hide_password=True)

    @property
    def dialecto(self) -> str:
        """Nombre del motor de la base ('sqlite' o 'postgresql')."""
        return make_url(self.__url).get_backend_name()

    @property
    def activa(self) -> bool:
        """Indica si el engine sigue disponible (no se llamó a cerrar)."""
        return self.__engine is not None

    @property
    def en_transaccion(self) -> bool:
        """Indica si hay una transacción en curso sobre esta conexión."""
        return self.__conexion_en_curso is not None

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
                "La URL de conexión no es válida."
            ) from error
        return url_limpia

    def _crear_directorio_sqlite(self) -> None:
        """Crea la carpeta del archivo SQLite si todavía no existe."""
        url_parseada = make_url(self.__url)
        archivo: Optional[str] = url_parseada.database
        if (url_parseada.get_backend_name() == "sqlite"
                and archivo not in (None, "", ":memory:")):
            Path(archivo).parent.mkdir(parents=True, exist_ok=True)

    def _conexion_compartida(self) -> Optional[Connection]:
        """Devuelve la conexión de la transacción en curso, si la hay.

        Uso interno de Transaccion.

        Returns:
            Optional[Connection]: La conexión en curso, o None.
        """
        return self.__conexion_en_curso

    def _registrar_conexion_en_curso(
        self, conexion: Optional[Connection]
    ) -> None:
        """Registra (o libera, con None) la conexión de la transacción.

        Uso interno de Transaccion.

        Args:
            conexion (Optional[Connection]): Conexión de la transacción
                externa que se inicia, o None cuando termina.
        """
        self.__conexion_en_curso = conexion

    def conectar(self) -> Connection:
        """Abre una conexión nueva a la base de datos.

        En SQLite ejecuta PRAGMA foreign_keys = ON, porque el motor no
        aplica las claves foráneas por defecto (PostgreSQL sí las aplica).

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

    def transaccion(self) -> "Transaccion":
        """Crea un context manager para operar dentro de una transacción.

        Uso:
            with conexion_db.transaccion() as conexion:
                conexion.execute(text("INSERT ..."), {...})

        Si ya hay una transacción en curso, la nueva se suma a ella.

        Returns:
            Transaccion: Context manager nuevo, de un solo uso.
        """
        return Transaccion(self)

    def cerrar(self) -> None:
        """Libera el engine y todas sus conexiones del pool."""
        if self.__engine is not None:
            self.__engine.dispose()
            self.__engine = None

    def __repr__(self) -> str:
        """Representación técnica de la conexión (sin la contraseña)."""
        estado: str = "activa" if self.activa else "cerrada"
        return f"ConexionDB(url={self.url!r}, {estado})"


class Transaccion:
    """Context manager que maneja una transacción completa.

    Al entrar abre una conexión e inicia la transacción. Al salir confirma
    los cambios si el bloque terminó bien o los deshace si hubo una
    excepción, y siempre cierra la conexión. La excepción se propaga.

    Si al entrar ya hay una transacción en curso sobre la misma ConexionDB,
    esta se suma a ella (transacción anidada): usa la misma conexión y deja
    que la transacción externa decida el commit o el rollback final.
    """

    def __init__(self, conexion_db: ConexionDB) -> None:
        """Prepara la transacción sobre una ConexionDB.

        Args:
            conexion_db (ConexionDB): Conexión de la que se obtiene la
                conexión para la transacción.

        Raises:
            TypeError: Si conexion_db no es una ConexionDB.
        """
        if not isinstance(conexion_db, ConexionDB):
            raise TypeError("La transacción requiere una ConexionDB.")
        self.__conexion_db: ConexionDB = conexion_db
        self.__conexion: Optional[Connection] = None
        self.__transaccion: Optional[RootTransaction] = None
        self.__usada: bool = False
        self.__anidada: bool = False

    @property
    def en_curso(self) -> bool:
        """Indica si la transacción está abierta (dentro del bloque with)."""
        return self.__conexion is not None

    @property
    def anidada(self) -> bool:
        """Indica si la transacción se sumó a otra que ya estaba en curso."""
        return self.__anidada

    def __enter__(self) -> Connection:
        """Abre la conexión e inicia la transacción, o se suma a la actual.

        Returns:
            Connection: Conexión sobre la que se ejecutan las sentencias.

        Raises:
            RuntimeError: Si la transacción ya fue utilizada.
        """
        if self.__usada:
            raise RuntimeError(
                "La transacción ya fue utilizada; pedir una nueva con "
                "transaccion()."
            )
        self.__usada = True

        compartida: Optional[Connection] = (
            self.__conexion_db._conexion_compartida()
        )
        if compartida is not None:
            self.__anidada = True
            self.__conexion = compartida
            return compartida

        self.__conexion = self.__conexion_db.conectar()
        try:
            self.__transaccion = self.__conexion.begin()
        except Exception:
            self.__conexion.close()
            self.__conexion = None
            raise
        self.__conexion_db._registrar_conexion_en_curso(self.__conexion)
        return self.__conexion

    def __exit__(
        self,
        tipo_error: Optional[Type[BaseException]],
        error: Optional[BaseException],
        traza: Optional[TracebackType],
    ) -> bool:
        """Confirma o deshace la transacción y cierra la conexión.

        Una transacción anidada no confirma ni deshace nada: solo libera su
        referencia y deja la decisión a la transacción externa, a la que le
        llega la excepción (si la hubo).

        Args:
            tipo_error (Optional[Type[BaseException]]): Tipo de la excepción
                ocurrida en el bloque, o None si terminó bien.
            error (Optional[BaseException]): Excepción ocurrida, o None.
            traza (Optional[TracebackType]): Traza de la excepción, o None.

        Returns:
            bool: Siempre False, para que la excepción (si la hubo) se
            propague a quien usó el bloque with.
        """
        if self.__anidada:
            self.__conexion = None
            return False
        try:
            if self.__transaccion is not None:
                if tipo_error is None:
                    self.__transaccion.commit()
                else:
                    self.__transaccion.rollback()
        finally:
            if self.__conexion is not None:
                self.__conexion.close()
            self.__conexion_db._registrar_conexion_en_curso(None)
            self.__conexion = None
            self.__transaccion = None
        return False
