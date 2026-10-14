"""Migración de los datos del TP1 (archivos CSV) a la base de datos.

Por cada tabla se lee su CSV, se convierten los valores al tipo de cada
columna, se genera un archivo ``.sql`` con las sentencias INSERT y se
insertan los registros en la base. Las tablas se procesan respetando las
relaciones (primero las que no tienen claves foráneas).
"""

import csv
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import Date, Integer, Numeric, insert
from sqlalchemy.schema import Column, CreateTable

from book_manager.database.connection import Base, ConexionDB
from book_manager.models.models import (
    CotizacionDolarModel, EditorialModel, GeneroModel, LibroModel,
    MonedaModel, PrecioModel, StockModel, TipoCotizacionModel)

DIRECTORIO_MIGRACIONES = Path(__file__).resolve().parent
CARPETA_CSVS = DIRECTORIO_MIGRACIONES / "csv"
CARPETA_SQLS = DIRECTORIO_MIGRACIONES / "sql"

# Orden de carga: cada tabla después de las tablas a las que referencia.
ORDEN_DE_CARGA: List[Type[Base]] = [
    GeneroModel, EditorialModel, MonedaModel, TipoCotizacionModel,
    LibroModel, PrecioModel, StockModel, CotizacionDolarModel]


def _convertir(columna: Column, valor: str) -> Any:
    """Convierte el texto del CSV al tipo de la columna."""
    if valor == "" and columna.nullable:
        return None
    if isinstance(columna.type, Integer):
        return int(valor)
    if isinstance(columna.type, Numeric):
        return float(valor)
    if isinstance(columna.type, Date):
        return datetime.date.fromisoformat(valor)
    return valor


def leer_csv(modelo: Type[Base], carpeta_csvs: Path) -> List[Dict[str, Any]]:
    """Lee el CSV de una tabla y devuelve sus filas con los tipos correctos.

    Args:
        modelo (Type[Base]): Modelo ORM de la tabla.
        carpeta_csvs (Path): Carpeta con los archivos CSV.

    Returns:
        List[Dict[str, Any]]: Filas listas para insertar.
    """
    columnas = modelo.__table__.columns
    ruta = carpeta_csvs / f"{modelo.__tablename__}.csv"
    with open(ruta, newline="", encoding="utf-8") as archivo:
        return [{nombre: _convertir(columnas[nombre], valor)
                 for nombre, valor in fila.items()}
                for fila in csv.DictReader(archivo)]


def generar_sql_insercion(modelo: Type[Base], filas: List[Dict[str, Any]],
                          conexion: ConexionDB) -> str:
    """Devuelve las sentencias INSERT de las filas en el dialecto de la base.

    Args:
        modelo (Type[Base]): Modelo ORM de la tabla.
        filas (List[Dict[str, Any]]): Filas a insertar.
        conexion (ConexionDB): Conexión cuyo dialecto se usa.

    Returns:
        str: Script SQL con una sentencia por fila.
    """
    sentencias = [
        str(insert(modelo.__table__).values(**fila).compile(
            conexion.engine, compile_kwargs={"literal_binds": True})) + ";"
        for fila in filas]
    return (f"-- Datos de la tabla {modelo.__tablename__} "
            f"({len(filas)} registros)\n" + "\n".join(sentencias) + "\n")


def generar_sql_esquema(conexion: ConexionDB) -> str:
    """Devuelve las sentencias CREATE TABLE de todas las tablas."""
    sentencias = [str(CreateTable(modelo.__table__).compile(conexion.engine))
                  .strip() + ";" for modelo in ORDEN_DE_CARGA]
    return ("-- Esquema de la base de datos Book Manager\n"
            f"-- Dialecto: {conexion.engine.dialect.name}\n\n"
            + "\n\n".join(sentencias) + "\n")


def migrar_datos(carpeta_csvs: str = str(CARPETA_CSVS),
                 carpeta_sqls: str = str(CARPETA_SQLS),
                 conexion: Optional[ConexionDB] = None) -> Dict[str, int]:
    """Función encargada de la migración de datos de csv a sql.

    Se encarga de leer los archivos csv y crear los archivos sql
    para la inserción en la base de datos. Además inserta los datos en la
    base dentro de una única transacción: si una fila no es válida no se
    guarda ninguna.

    Args:
        carpeta_csvs (str): Carpeta donde se encuentran los archivos csv de
            origen.
        carpeta_sqls (str): Carpeta donde se deben guardar los archivos sql
            generados.
        conexion (Optional[ConexionDB]): Conexión a la base. Si es None se
            crea una con la configuración del .env.

    Returns:
        Dict[str, int]: Cantidad de registros migrados por tabla.
    """
    conexion = conexion or ConexionDB()
    conexion.crear_tablas()
    origen = Path(carpeta_csvs)
    destino = Path(carpeta_sqls)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "00_esquema.sql").write_text(generar_sql_esquema(conexion),
                                            encoding="utf-8")
    resumen = {}
    with conexion.transaccion() as sesion:
        for numero, modelo in enumerate(ORDEN_DE_CARGA, 1):
            filas = leer_csv(modelo, origen)
            archivo_sql = destino / f"{numero:02d}_{modelo.__tablename__}.sql"
            archivo_sql.write_text(
                generar_sql_insercion(modelo, filas, conexion),
                encoding="utf-8")
            if filas:
                sesion.execute(insert(modelo.__table__), filas)
            resumen[modelo.__tablename__] = len(filas)
    return resumen
