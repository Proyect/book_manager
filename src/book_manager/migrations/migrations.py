#@title Escritura de migrations.py
"""Migración de los datos del Sprint 1 a la base de datos.

Lee los CSV de migrations/csv y genera en migrations/sql un archivo .sql por
tabla con las sentencias de inserción. Ofrece además la ejecución de un
archivo .sql sobre una conexión y el ajuste de las secuencias de ids, que
usa la carga de datos de preload_data. Funciona sobre SQLite y sobre
PostgreSQL (Supabase).
"""
import csv
from pathlib import Path
from typing import Dict, FrozenSet, List, Tuple

from sqlalchemy.engine import Connection
from sqlalchemy.sql import text


class TablaMigracion:
    """Configuración de la migración de una tabla."""

    def __init__(self, tabla: str, columnas: Tuple[str, ...],
                 numericas: Tuple[str, ...]) -> None:
        """Define qué columnas tiene la tabla y cuáles son numéricas.

        Args:
            tabla (str): Nombre de la tabla (y del CSV, sin extensión).
            columnas (Tuple[str, ...]): Columnas esperadas, en orden.
            numericas (Tuple[str, ...]): Columnas que se escriben sin
                comillas en el SQL.

        Raises:
            ValueError: Si una columna numérica no está entre las columnas.
        """
        if not set(numericas) <= set(columnas):
            raise ValueError(
                f"Columnas numéricas desconocidas en la tabla '{tabla}'."
            )
        self.__tabla: str = tabla
        self.__columnas: Tuple[str, ...] = columnas
        self.__numericas: FrozenSet[str] = frozenset(numericas)

    @property
    def tabla(self) -> str:
        """Nombre de la tabla."""
        return self.__tabla

    @property
    def columnas(self) -> Tuple[str, ...]:
        """Columnas de la tabla, en el orden del INSERT."""
        return self.__columnas

    @property
    def archivo_csv(self) -> str:
        """Nombre del archivo CSV de origen."""
        return f"{self.__tabla}.csv"

    def es_numerica(self, columna: str) -> bool:
        """Indica si una columna se escribe como número en el SQL.

        Args:
            columna (str): Nombre de la columna.

        Returns:
            bool: True si la columna es numérica.
        """
        return columna in self.__numericas


# Mismo orden que las tablas del esquema (Ejercicio 04): primero las tablas
# sin dependencias, después las que las referencian.
TABLAS_MIGRACION: List[TablaMigracion] = [
    TablaMigracion("generos", ("id", "nombre", "descripcion"), ("id",)),
    TablaMigracion(
        "editoriales",
        ("id", "nombre", "cuit", "condicion_iva", "direccion", "email",
         "telefono"),
        ("id",),
    ),
    TablaMigracion("monedas", ("id", "codigo", "nombre", "simbolo"),
                   ("id",)),
    TablaMigracion("tipos_cotizacion", ("id", "nombre", "descripcion"),
                   ("id",)),
    TablaMigracion(
        "libros",
        ("id", "isbn", "titulo", "autor", "editorial_id", "genero_id",
         "fecha_impresion", "numero_impresion"),
        ("id", "editorial_id", "genero_id", "numero_impresion"),
    ),
    TablaMigracion(
        "precios",
        ("id", "libro_id", "moneda_id", "valor", "fecha"),
        ("id", "libro_id", "moneda_id", "valor"),
    ),
    TablaMigracion(
        "stock",
        ("libro_id", "cantidad", "stock_minimo"),
        ("libro_id", "cantidad", "stock_minimo"),
    ),
    TablaMigracion(
        "cotizaciones_dolar",
        ("tipo_id", "fecha", "compra", "venta"),
        ("tipo_id", "compra", "venta"),
    ),
]


def nombre_archivo_sql(posicion: int, tabla: str) -> str:
    """Arma el nombre del archivo .sql de una tabla.

    Args:
        posicion (int): Posición de la tabla en el orden de migración.
        tabla (str): Nombre de la tabla.

    Returns:
        str: Nombre con prefijo numérico, por ejemplo '05_libros.sql'.
    """
    return f"{posicion:02d}_{tabla}.sql"


def _formatear_valor(valor: str, numerica: bool) -> str:
    """Convierte un valor del CSV en un literal SQL.

    Args:
        valor (str): Valor leído del CSV.
        numerica (bool): Si la columna es numérica.

    Returns:
        str: El número sin comillas, o el texto entre comillas simples con
        las comillas internas duplicadas.

    Raises:
        ValueError: Si una columna numérica tiene un valor no numérico.
    """
    if numerica:
        numero: str = valor.strip()
        try:
            float(numero)
        except ValueError as error:
            raise ValueError(
                f"Se esperaba un número y se encontró '{valor}'."
            ) from error
        return numero
    return "'" + valor.replace("'", "''") + "'"


def _leer_csv(ruta: Path, config: TablaMigracion) -> List[Dict[str, str]]:
    """Lee un CSV y verifica que tenga las columnas esperadas.

    Args:
        ruta (Path): Ruta del archivo CSV.
        config (TablaMigracion): Configuración de la tabla.

    Returns:
        List[Dict[str, str]]: Filas del archivo.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si las columnas no coinciden con las esperadas.
    """
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo {ruta}.")
    with open(ruta, newline="", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        encabezado: Tuple[str, ...] = tuple(lector.fieldnames or ())
        if set(encabezado) != set(config.columnas):
            raise ValueError(
                f"El archivo {ruta.name} tiene las columnas "
                f"{list(encabezado)}; se esperaban {list(config.columnas)}."
            )
        return list(lector)


def _generar_insert(config: TablaMigracion, fila: Dict[str, str]) -> str:
    """Genera la sentencia INSERT de una fila.

    Args:
        config (TablaMigracion): Configuración de la tabla.
        fila (Dict[str, str]): Fila leída del CSV.

    Returns:
        str: Sentencia INSERT en una línea, terminada en punto y coma.
    """
    columnas: str = ", ".join(config.columnas)
    valores: str = ", ".join(
        _formatear_valor(fila[columna], config.es_numerica(columna))
        for columna in config.columnas
    )
    return f"INSERT INTO {config.tabla} ({columnas}) VALUES ({valores});"


def migrar_datos(carpeta_csvs: str, carpeta_sqls: str) -> None:
    """Función encargada de la migración de datos de csv a sql.

    Se encarga de leer los archivos csv y crear los archivos sql para la
    inserción en la base de datos. Primero valida todos los CSV y recién
    después escribe los archivos, así un CSV inválido no deja archivos a
    medio generar.

    Args:
        carpeta_csvs (str): Carpeta donde se encuentran los archivos csv de
            origen.
        carpeta_sqls (str): Carpeta donde se deben guardar los archivos sql
            generados.

    Raises:
        FileNotFoundError: Si no existe la carpeta o alguno de los CSV.
        ValueError: Si un CSV tiene columnas o valores inválidos.
    """
    origen: Path = Path(carpeta_csvs)
    destino: Path = Path(carpeta_sqls)
    if not origen.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de CSV {origen}.")

    contenidos: Dict[str, str] = {}
    for posicion, config in enumerate(TABLAS_MIGRACION, start=1):
        filas: List[Dict[str, str]] = _leer_csv(
            origen / config.archivo_csv, config
        )
        lineas: List[str] = [
            f"-- Inserción de datos en la tabla {config.tabla}",
            f"-- Origen: {config.archivo_csv} ({len(filas)} registros)",
        ]
        lineas.extend(_generar_insert(config, fila) for fila in filas)
        contenidos[nombre_archivo_sql(posicion, config.tabla)] = (
            "\n".join(lineas) + "\n"
        )

    destino.mkdir(parents=True, exist_ok=True)
    for nombre, contenido in contenidos.items():
        with open(destino / nombre, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)


def _leer_sentencias(ruta: Path) -> List[str]:
    """Lee las sentencias de un archivo .sql (una por línea).

    Args:
        ruta (Path): Ruta del archivo .sql.

    Returns:
        List[str]: Sentencias, sin líneas vacías ni comentarios.
    """
    with open(ruta, encoding="utf-8") as archivo:
        return [
            linea.strip() for linea in archivo
            if linea.strip() and not linea.strip().startswith("--")
        ]


def ejecutar_archivo_sql(conexion: Connection, ruta: Path) -> int:
    """Ejecuta las sentencias de un archivo .sql sobre una conexión abierta.

    Los dos puntos de los datos se escapan para que text() no los tome como
    parámetros. La transacción la maneja quien llama.

    Args:
        conexion (Connection): Conexión de la transacción en curso.
        ruta (Path): Ruta del archivo .sql (una sentencia por línea).

    Returns:
        int: Cantidad de sentencias ejecutadas.

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo {ruta}.")
    sentencias: List[str] = _leer_sentencias(ruta)
    for sentencia in sentencias:
        conexion.execute(text(sentencia.replace(":", "\\:")))
    return len(sentencias)


def ajustar_secuencias(conexion: Connection) -> None:
    """Ajusta los contadores de ids de PostgreSQL al id máximo + 1.

    Los INSERT de la migración incluyen el id, y eso no avanza la columna
    IDENTITY. Sin este ajuste, la primera alta nueva repetiría el id 1. En
    SQLite no hace falta, porque el id siguiente sale del máximo existente.

    Args:
        conexion (Connection): Conexión de la transacción de migración.
    """
    if conexion.dialect.name != "postgresql":
        return
    for config in TABLAS_MIGRACION:
        if "id" in config.columnas:
            conexion.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{config.tabla}', "
                f"'id'), COALESCE(MAX(id), 0) + 1, false) "
                f"FROM {config.tabla}"
            ))
