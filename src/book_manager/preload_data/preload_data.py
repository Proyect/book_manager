"""Carga inicial de datos desde los archivos CSV de migrations/csv.

Los archivos de migración se leen con los mismos repositorios del sistema,
de modo que cada registro se valida al construir su entidad. Si todos son
válidos, se escriben como datos de trabajo en la carpeta ``data``.
"""

from pathlib import Path
from typing import Dict

from book_manager.repositories.repositories import (
    DIRECTORIO_DATOS, ArchivoCSV, RepositorioCotizacionDolar,
    RepositorioEditorial, RepositorioGenero, RepositorioLibro,
    RepositorioMoneda, RepositorioPrecio, RepositorioStock,
    RepositorioTipoCotizacion)

DIRECTORIO_MIGRACIONES = (Path(__file__).resolve().parent.parent
                          / "migrations" / "csv")


def importar_datos(origen: Path = DIRECTORIO_MIGRACIONES,
                   destino: Path = DIRECTORIO_DATOS) -> Dict[str, int]:
    """Valida los CSV de migración y los copia como datos del sistema.

    Args:
        origen (Path): Carpeta con los CSV de migración.
        destino (Path): Carpeta de datos de trabajo del sistema.

    Returns:
        Dict[str, int]: Cantidad de registros importados por archivo.

    Raises:
        ValueError: Si algún registro no es válido.
    """
    generos = RepositorioGenero(origen)
    editoriales = RepositorioEditorial(origen)
    monedas = RepositorioMoneda(origen)
    tipos = RepositorioTipoCotizacion(origen)
    libros = RepositorioLibro(editoriales, generos, origen)
    precios = RepositorioPrecio(libros, monedas, origen)
    stock = RepositorioStock(libros, origen)
    cotizaciones = RepositorioCotizacionDolar(tipos, origen)

    repositorios = {
        RepositorioGenero.NOMBRE_ARCHIVO: (generos, generos.CAMPOS),
        RepositorioEditorial.NOMBRE_ARCHIVO: (editoriales,
                                              editoriales.CAMPOS),
        RepositorioMoneda.NOMBRE_ARCHIVO: (monedas, monedas.CAMPOS),
        RepositorioTipoCotizacion.NOMBRE_ARCHIVO: (tipos, tipos.CAMPOS),
        RepositorioLibro.NOMBRE_ARCHIVO: (libros, libros.CAMPOS),
        RepositorioPrecio.NOMBRE_ARCHIVO: (precios, precios.CAMPOS),
        "stock.csv": (stock, stock.CAMPOS),
        "cotizaciones_dolar.csv": (cotizaciones, cotizaciones.CAMPOS),
    }
    resumen = {}
    for nombre, (repositorio, campos) in repositorios.items():
        registros = [r.to_dict() for r in repositorio.leer_todos()]
        ArchivoCSV(nombre, campos, destino).escribir(registros)
        resumen[nombre] = len(registros)
    return resumen


def hay_datos(destino: Path = DIRECTORIO_DATOS) -> bool:
    """Indica si ya existen datos de trabajo cargados."""
    return (destino / RepositorioLibro.NOMBRE_ARCHIVO).exists()
