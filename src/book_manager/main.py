#@title Escritura de main.py
"""Punto de entrada del sistema Book Manager.

Arma la conexión a la base de datos, los repositorios y los servicios, carga
los datos iniciales si hace falta (o crea las tablas nuevas en una base
existente) e inicia la consola. La URL de la API de cotizaciones se lee del
archivo .env. Todos los servicios registran sus operaciones en la tabla de
auditoría.
"""

from typing import Dict, Optional

from sqlalchemy.exc import OperationalError

from book_manager.database.connection import URL_POR_DEFECTO, ConexionDB
from book_manager.models.models import EsquemaDB
from book_manager.preload_data.preload_data import hay_datos, importar_datos
from book_manager.repositories.repositories import (
    RepositorioAuditoria, RepositorioCotizacionDolar, RepositorioEditorial,
    RepositorioGenero, RepositorioLibro, RepositorioMoneda, RepositorioPrecio,
    RepositorioPrecioWeb, RepositorioStock, RepositorioTipoCotizacion)
from book_manager.services.services import (
    ServicioAuditable, ServicioAuditoria, ServicioCotizacionDolar,
    ServicioEditorial, ServicioGenero, ServicioLibro, ServicioMoneda,
    ServicioPrecio, ServicioReportes, ServicioScraping, ServicioStock,
    ServicioTipoCotizacion, cargar_url_api)
from book_manager.ui.console import Consola, Servicios


def crear_servicios(conexion_db: ConexionDB,
                    url_api: Optional[str] = None) -> Servicios:
    """Construye repositorios y servicios con sus dependencias.

    Args:
        conexion_db (ConexionDB): Conexión que comparten todos los
            repositorios del sistema.
        url_api (Optional[str]): URL de la API de cotizaciones. Si es None,
            se lee del archivo .env.

    Returns:
        Servicios: Servicios listos para la consola, con la auditoría
        asignada.

    Raises:
        ValueError: Si url_api es None y el .env no define API_URL.
    """
    repo_genero = RepositorioGenero(conexion_db)
    repo_editorial = RepositorioEditorial(conexion_db)
    repo_moneda = RepositorioMoneda(conexion_db)
    repo_tipo = RepositorioTipoCotizacion(conexion_db)
    repo_libro = RepositorioLibro(conexion_db, repo_editorial, repo_genero)
    repo_precio = RepositorioPrecio(conexion_db, repo_libro, repo_moneda)
    repo_stock = RepositorioStock(conexion_db, repo_libro)
    repo_cotizacion = RepositorioCotizacionDolar(conexion_db, repo_tipo)
    repo_precio_web = RepositorioPrecioWeb(conexion_db, repo_libro)

    libro = ServicioLibro(repo_libro, repo_precio, repo_stock, conexion_db)
    precio = ServicioPrecio(repo_precio)
    stock = ServicioStock(repo_stock, repo_libro)
    cotizacion = ServicioCotizacionDolar(
        repo_cotizacion, repo_tipo, conexion_db,
        url_api if url_api is not None else cargar_url_api())
    scraping = ServicioScraping(libro, repo_precio_web, conexion_db)
    reportes = ServicioReportes(libro, precio, stock, cotizacion, scraping)
    servicios = Servicios(
        genero=ServicioGenero(repo_genero, repo_libro),
        editorial=ServicioEditorial(repo_editorial, repo_libro),
        moneda=ServicioMoneda(repo_moneda, repo_precio),
        tipo_cotizacion=ServicioTipoCotizacion(repo_tipo, repo_cotizacion),
        libro=libro, precio=precio, stock=stock, cotizacion=cotizacion,
        reportes=reportes, scraping=scraping,
        auditoria=ServicioAuditoria(RepositorioAuditoria(conexion_db)))
    for servicio in vars(servicios).values():
        if isinstance(servicio, ServicioAuditable):
            servicio.asignar_auditoria(servicios.auditoria)
    return servicios


def conectar_base() -> ConexionDB:
    """Conecta con la base del .env o, si no responde, con la SQLite local.

    Returns:
        ConexionDB: Conexión a la base configurada en el .env (Supabase);
        si no se puede conectar (por ejemplo, el proyecto de Supabase no
        existe más), a la base SQLite local del proyecto.
    """
    conexion: ConexionDB = ConexionDB()
    if conexion.dialecto == "sqlite":
        return conexion
    try:
        EsquemaDB(conexion).tablas_existentes()
    except OperationalError:
        print(f"No se pudo conectar a la base {conexion.url}; se usa la "
              f"base SQLite local.")
        conexion.cerrar()
        return ConexionDB(URL_POR_DEFECTO)
    return conexion


def main(import_default_data: bool = True,
         conexion_db: Optional[ConexionDB] = None) -> None:
    """Inicia la aplicación de consola.

    Args:
        import_default_data (bool): Si es True, recrea la base y la carga
            con los archivos .sql de migrations/sql. Si es False, usa la
            base existente; si la base no existe o está vacía, igual
            importa los datos.
        conexion_db (Optional[ConexionDB]): Conexión a usar. Si es None,
            se usa la base configurada en el .env (o la SQLite local, si
            aquella no responde) y se cierra al salir.
    """
    conexion_propia: bool = conexion_db is None
    conexion: ConexionDB = conectar_base() if conexion_propia else conexion_db
    try:
        resumen: Optional[Dict[str, int]] = None
        if import_default_data or not hay_datos(conexion):
            resumen = importar_datos(conexion)
            print("Datos iniciales importados en la base:")
            for tabla, cantidad in resumen.items():
                print(f"  {tabla}: {cantidad} registros")
        else:
            EsquemaDB(conexion).crear_tablas()
        servicios: Servicios = crear_servicios(conexion)
        if resumen is not None:
            servicios.auditoria.registrar(
                "IMPORTACIÓN datos iniciales",
                ", ".join(f"{t}: {n}" for t, n in resumen.items()))
        Consola(servicios).ejecutar()
    finally:
        if conexion_propia:
            conexion.cerrar()


if __name__ == "__main__":
    main()
