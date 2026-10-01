"""Interfaz de consola (CLI) que opera con los CRUD de cada entidad."""

import datetime
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, TypeVar

from book_manager.entities.entities import (
    CotizacionDolar, Editorial, Genero, Libro, Moneda, Precio, Stock,
    TipoCotizacion)
from book_manager.services.services import (
    ServicioCotizacion, ServicioCRUD, ServicioEditorial, ServicioGenero,
    ServicioLibro, ServicioMoneda, ServicioPrecio, ServicioReportes,
    ServicioStock, ServicioTipoCotizacion)

E = TypeVar('E')


@dataclass
class Servicios:
    """Agrupa los servicios que usa la interfaz."""

    genero: ServicioGenero
    editorial: ServicioEditorial
    moneda: ServicioMoneda
    tipo_cotizacion: ServicioTipoCotizacion
    libro: ServicioLibro
    precio: ServicioPrecio
    stock: ServicioStock
    cotizacion: ServicioCotizacion
    reportes: ServicioReportes


def imprimir_tabla(encabezados: Sequence[str],
                   filas: Sequence[Sequence[Any]]) -> None:
    """Muestra filas en columnas alineadas."""
    textos = [[str(c) for c in fila] for fila in filas]
    anchos = [max([len(e)] + [len(f[i]) for f in textos])
              for i, e in enumerate(encabezados)]
    linea = " | ".join(e.ljust(a) for e, a in zip(encabezados, anchos))
    print(linea)
    print("-" * len(linea))
    for fila in textos:
        print(" | ".join(c.ljust(a) for c, a in zip(fila, anchos)))
    print(f"({len(textos)} registros)")


def pedir_texto(mensaje: str, actual: Optional[str] = None) -> str:
    """Pide un texto; con Enter conserva el valor actual."""
    sufijo = f" [{actual}]" if actual is not None else ""
    valor = input(f"{mensaje}{sufijo}: ").strip()
    return actual if not valor and actual is not None else valor


def pedir_entero(mensaje: str, actual: Optional[int] = None) -> int:
    """Pide un número entero hasta que sea válido."""
    while True:
        valor = pedir_texto(mensaje, None if actual is None else str(actual))
        try:
            return int(valor)
        except ValueError:
            print("  Ingrese un número entero.")


def pedir_decimal(mensaje: str, actual: Optional[float] = None) -> float:
    """Pide un número decimal (acepta coma o punto)."""
    while True:
        valor = pedir_texto(mensaje, None if actual is None else str(actual))
        try:
            return float(valor.replace(",", "."))
        except ValueError:
            print("  Ingrese un número válido.")


def pedir_fecha(mensaje: str,
                actual: Optional[datetime.date] = None) -> datetime.date:
    """Pide una fecha en formato AAAA-MM-DD."""
    while True:
        valor = pedir_texto(f"{mensaje} (AAAA-MM-DD)",
                            None if actual is None else actual.isoformat())
        try:
            return datetime.date.fromisoformat(valor)
        except ValueError:
            print("  Formato de fecha inválido.")


def elegir(mensaje: str, opciones: List[E],
           actual: Optional[E] = None) -> E:
    """Muestra una lista numerada y devuelve la opción elegida."""
    for i, opcion in enumerate(opciones, 1):
        print(f"  {i}. {opcion}")
    posicion = opciones.index(actual) + 1 if actual in opciones else None
    while True:
        numero = pedir_entero(mensaje, posicion)
        if 1 <= numero <= len(opciones):
            return opciones[numero - 1]
        print("  Opción fuera de rango.")


def menu(titulo: str, opciones: Dict[str, Callable[[], None]]) -> None:
    """Muestra un menú hasta que se elija 0 (volver/salir)."""
    claves = list(opciones)
    while True:
        print(f"\n=== {titulo} ===")
        for i, clave in enumerate(claves, 1):
            print(f"{i}. {clave}")
        print("0. Volver" if titulo != "BOOK MANAGER" else "0. Salir")
        eleccion = input("Opción: ").strip()
        if eleccion == "0":
            return
        if not eleccion.isdigit() or not 1 <= int(eleccion) <= len(claves):
            print("Opción inválida.")
            continue
        try:
            opciones[claves[int(eleccion) - 1]]()
        except (ValueError, TypeError, ConnectionError) as error:
            print(f"Error: {error}")


class Consola:
    """Menús de la aplicación de consola."""

    def __init__(self, servicios: Servicios) -> None:
        """Recibe los servicios del sistema."""
        self._s = servicios

    def ejecutar(self) -> None:
        """Muestra el menú principal."""
        menu("BOOK MANAGER", {
            "Libros": self.menu_libros,
            "Géneros": self.menu_generos,
            "Editoriales": self.menu_editoriales,
            "Monedas": self.menu_monedas,
            "Tipos de cotización": self.menu_tipos_cotizacion,
            "Precios": self.menu_precios,
            "Stock": self.menu_stock,
            "Cotizaciones del dólar": self.menu_cotizaciones,
            "Reportes": self.menu_reportes,
        })
        print("¡Hasta luego!")

    def _menu_crud(self, titulo: str, servicio: ServicioCRUD,
                   listar: Callable[[], None], alta: Callable[[], Any],
                   modificar: Callable[[Any], Dict[str, Any]]) -> None:
        """Submenú estándar de alta, lectura, modificación y baja."""
        def hacer_alta() -> None:
            print(f"Creado: {servicio.crear(alta())}")

        def hacer_modificacion() -> None:
            entidad = servicio.obtener(pedir_entero("ID a modificar"))
            print("(Enter conserva el valor actual)")
            cambios = modificar(entidad)
            print(f"Modificado: {servicio.modificar(entidad.id, cambios)}")

        def hacer_baja() -> None:
            entidad = servicio.obtener(pedir_entero("ID a eliminar"))
            if pedir_texto(f"¿Eliminar '{entidad}'? (s/n)").lower() == "s":
                servicio.eliminar(entidad.id)
                print("Eliminado.")

        menu(titulo, {"Listar": listar, "Alta": hacer_alta,
                      "Modificar": hacer_modificacion, "Baja": hacer_baja})

    # ----- Géneros y tipos de cotización (nombre + descripción) -----

    def menu_generos(self) -> None:
        """CRUD de géneros."""
        self._menu_crud(
            "GÉNEROS", self._s.genero,
            lambda: imprimir_tabla(
                ["ID", "Nombre", "Descripción"],
                [(g.id, g.nombre, g.descripcion)
                 for g in self._s.genero.listar()]),
            lambda: Genero(pedir_texto("Nombre"), pedir_texto("Descripción")),
            lambda g: {"nombre": pedir_texto("Nombre", g.nombre),
                       "descripcion": pedir_texto("Descripción",
                                                  g.descripcion)})

    def menu_tipos_cotizacion(self) -> None:
        """CRUD de tipos de cotización."""
        self._menu_crud(
            "TIPOS DE COTIZACIÓN", self._s.tipo_cotizacion,
            lambda: imprimir_tabla(
                ["ID", "Nombre", "Descripción"],
                [(t.id, t.nombre, t.descripcion)
                 for t in self._s.tipo_cotizacion.listar()]),
            lambda: TipoCotizacion(pedir_texto("Nombre"),
                                   pedir_texto("Descripción")),
            lambda t: {"nombre": pedir_texto("Nombre", t.nombre),
                       "descripcion": pedir_texto("Descripción",
                                                  t.descripcion)})

    # ----- Editoriales -----

    def menu_editoriales(self) -> None:
        """CRUD de editoriales."""
        def formulario(e: Optional[Editorial] = None) -> Dict[str, Any]:
            print(f"  Condiciones IVA: {', '.join(Editorial.CONDICIONES_IVA)}")
            return {
                "nombre": pedir_texto("Nombre", e and e.nombre),
                "cuit": pedir_texto("CUIT", e and e.cuit),
                "condicion_iva": pedir_texto("Condición IVA",
                                             e and e.condicion_iva),
                "direccion": pedir_texto("Dirección", e and e.direccion),
                "email": pedir_texto("Email", e and e.email),
                "telefono": pedir_texto("Teléfono", e and e.telefono)}

        self._menu_crud(
            "EDITORIALES", self._s.editorial,
            lambda: imprimir_tabla(
                ["ID", "Nombre", "CUIT", "IVA", "Email"],
                [(e.id, e.nombre, e.cuit_formateado, e.condicion_iva, e.email)
                 for e in self._s.editorial.listar()]),
            lambda: Editorial(**formulario()),
            formulario)

    # ----- Monedas -----

    def menu_monedas(self) -> None:
        """CRUD de monedas."""
        def formulario(m: Optional[Moneda] = None) -> Dict[str, Any]:
            return {"codigo": pedir_texto("Código ISO", m and m.codigo),
                    "nombre": pedir_texto("Nombre", m and m.nombre),
                    "simbolo": pedir_texto("Símbolo", m and m.simbolo)}

        self._menu_crud(
            "MONEDAS", self._s.moneda,
            lambda: imprimir_tabla(
                ["ID", "Código", "Nombre", "Símbolo"],
                [(m.id, m.codigo, m.nombre, m.simbolo)
                 for m in self._s.moneda.listar()]),
            lambda: Moneda(**formulario()),
            formulario)

    # ----- Libros -----

    def listar_libros(self) -> None:
        """Muestra el catálogo."""
        imprimir_tabla(
            ["ID", "ISBN", "Título", "Autor", "Editorial", "Género"],
            [(libro.id, libro.isbn, libro.titulo, libro.autor,
              libro.editorial, libro.genero)
             for libro in self._s.libro.listar()])

    def menu_libros(self) -> None:
        """CRUD de libros."""
        def formulario(libro: Optional[Libro] = None) -> Dict[str, Any]:
            return {
                "isbn": pedir_texto("ISBN", libro and libro.isbn),
                "titulo": pedir_texto("Título", libro and libro.titulo),
                "autor": pedir_texto("Autor", libro and libro.autor),
                "editorial": elegir("Editorial", self._s.editorial.listar(),
                                    libro and libro.editorial),
                "genero": elegir("Género", self._s.genero.listar(),
                                 libro and libro.genero),
                "fecha_impresion": pedir_fecha(
                    "Fecha de impresión", libro and libro.fecha_impresion),
                "numero_impresion": pedir_entero(
                    "Número de impresión",
                    libro.numero_impresion if libro else 1)}

        self._menu_crud("LIBROS", self._s.libro, self.listar_libros,
                        lambda: Libro(**formulario()), formulario)

    # ----- Precios -----

    def menu_precios(self) -> None:
        """CRUD de precios."""
        def formulario(p: Optional[Precio] = None) -> Dict[str, Any]:
            return {
                "libro": elegir("Libro", self._s.libro.listar(),
                                p and p.libro),
                "moneda": elegir("Moneda", self._s.moneda.listar(),
                                 p and p.moneda),
                "valor": pedir_decimal("Valor", p and p.valor),
                "fecha": pedir_fecha("Fecha",
                                     p.fecha if p else datetime.date.today())}

        self._menu_crud(
            "PRECIOS", self._s.precio,
            lambda: imprimir_tabla(
                ["ID", "Libro", "Precio", "Fecha"],
                [(p.id, p.libro.titulo, p, p.fecha.isoformat())
                 for p in self._s.precio.listar()]),
            lambda: Precio(**formulario()),
            formulario)

    # ----- Stock -----

    def listar_stock(self) -> None:
        """Muestra el stock de cada libro."""
        imprimir_tabla(
            ["Libro ID", "Título", "Cantidad", "Mínimo", "Reponer"],
            [(s.libro_id, s.libro.titulo, s.cantidad, s.stock_minimo,
              "SÍ" if s.requiere_reposicion else "")
             for s in self._s.stock.listar()])

    def _elegir_stock(self) -> Stock:
        """Elige un registro de stock por libro."""
        return elegir("Libro", self._s.stock.listar())

    def menu_stock(self) -> None:
        """Operaciones de stock."""
        def alta() -> None:
            con_stock = {s.libro_id for s in self._s.stock.listar()}
            libres = [libro for libro in self._s.libro.listar()
                      if libro.id not in con_stock]
            if not libres:
                print("Todos los libros tienen stock registrado.")
                return
            stock = Stock(elegir("Libro", libres), pedir_entero("Cantidad"),
                          pedir_entero("Stock mínimo"))
            print(f"Creado: {self._s.stock.crear(stock)}")

        def modificar() -> None:
            s = self._elegir_stock()
            cantidad = pedir_entero("Cantidad", s.cantidad)
            minimo = pedir_entero("Stock mínimo", s.stock_minimo)
            stock = self._s.stock.modificar(s.libro_id, cantidad, minimo)
            print(f"Modificado: {stock}")

        def ingresar() -> None:
            s = self._elegir_stock()
            print(self._s.stock.ingresar(s.libro_id,
                                         pedir_entero("Unidades a ingresar")))

        def vender() -> None:
            s = self._elegir_stock()
            print(self._s.stock.vender(s.libro_id,
                                       pedir_entero("Unidades vendidas")))

        def baja() -> None:
            s = self._elegir_stock()
            if self._s.stock.eliminar(s.libro_id):
                print("Eliminado.")

        menu("STOCK", {"Listar": self.listar_stock, "Alta": alta,
                       "Modificar": modificar, "Baja": baja,
                       "Ingreso de mercadería": ingresar,
                       "Registrar venta": vender})

    # ----- Cotizaciones -----

    def listar_cotizaciones(self) -> None:
        """Muestra todas las cotizaciones."""
        imprimir_tabla(
            ["Tipo", "Fecha", "Compra", "Venta"],
            [(c.tipo, c.fecha.isoformat(), f"{c.compra:,.2f}",
              f"{c.venta:,.2f}") for c in self._s.cotizacion.listar()])

    def menu_cotizaciones(self) -> None:
        """CRUD de cotizaciones y actualización en línea."""
        def alta() -> None:
            cotizacion = CotizacionDolar(
                elegir("Tipo", self._s.tipo_cotizacion.listar()),
                pedir_fecha("Fecha", datetime.date.today()),
                pedir_decimal("Compra"), pedir_decimal("Venta"))
            print(f"Creada: {self._s.cotizacion.crear(cotizacion)}")

        def modificar() -> None:
            tipo = elegir("Tipo", self._s.tipo_cotizacion.listar())
            actual = self._s.cotizacion.obtener(tipo.id, pedir_fecha("Fecha"))
            print(self._s.cotizacion.modificar(
                tipo.id, actual.fecha, pedir_decimal("Compra", actual.compra),
                pedir_decimal("Venta", actual.venta)))

        def baja() -> None:
            tipo = elegir("Tipo", self._s.tipo_cotizacion.listar())
            if self._s.cotizacion.eliminar(tipo.id, pedir_fecha("Fecha")):
                print("Eliminada.")
            else:
                print("No existe esa cotización.")

        def en_linea() -> None:
            for cotizacion in self._s.cotizacion.actualizar_desde_api():
                print(cotizacion)

        menu("COTIZACIONES DEL DÓLAR", {
            "Listar": self.listar_cotizaciones, "Alta": alta,
            "Modificar": modificar, "Baja": baja,
            "Actualizar en línea (dolarapi.com)": en_linea})

    # ----- Reportes -----

    def _elegir_tipo(self) -> TipoCotizacion:
        """Pide el tipo de cotización para convertir dólares a pesos."""
        return elegir("Tipo de cotización para convertir USD",
                      self._s.tipo_cotizacion.listar())

    def reporte_inventario(self) -> None:
        """Inventario valorizado en pesos."""
        lineas = self._s.reportes.inventario_valorizado(self._elegir_tipo())
        imprimir_tabla(
            ["Título", "Precio", "Precio ARS", "Stock", "Subtotal ARS"],
            [(linea.libro.titulo, linea.precio or "-",
              "-" if linea.precio_ars is None
              else f"{linea.precio_ars:,.2f}",
              linea.cantidad, f"{linea.subtotal_ars:,.2f}")
             for linea in lineas])
        total = sum(linea.subtotal_ars for linea in lineas)
        print(f"Valor total del inventario: $ {total:,.2f}")

    def reporte_reposicion(self) -> None:
        """Libros por debajo del stock mínimo."""
        imprimir_tabla(
            ["Título", "Cantidad", "Mínimo", "A pedir"],
            [(s.libro.titulo, s.cantidad, s.stock_minimo,
              s.stock_minimo - s.cantidad)
             for s in self._s.reportes.libros_para_reponer()])

    def reporte_historico(self) -> None:
        """Evolución de un tipo de cotización."""
        tipo = elegir("Tipo", self._s.tipo_cotizacion.listar())
        historico = self._s.cotizacion.historico(tipo.id)
        imprimir_tabla(["Fecha", "Compra", "Venta", "Promedio"],
                       [(c.fecha.isoformat(), f"{c.compra:,.2f}",
                         f"{c.venta:,.2f}", f"{c.promedio:,.2f}")
                        for c in historico])
        if len(historico) > 1:
            variacion = (historico[-1].venta / historico[0].venta - 1) * 100
            print(f"Variación de la venta en el período: {variacion:.2f}%")

    def reporte_competencia(self) -> None:
        """Compara precios propios con Cúspide."""
        print("Consultando cuspide.com, puede demorar unos segundos...")
        filas = self._s.reportes.comparar_con_competencia(self._elegir_tipo())
        imprimir_tabla(
            ["Título", "Nuestro ARS", "Cúspide ARS", "Diferencia"],
            [(f.libro.titulo,
              "-" if f.precio_propio_ars is None
              else f"{f.precio_propio_ars:,.2f}",
              "no encontrado" if f.precio_competencia_ars is None
              else f"{f.precio_competencia_ars:,.2f}",
              "-" if f.diferencia_porcentual is None
              else f"{f.diferencia_porcentual:+.2f}%") for f in filas])

    def menu_reportes(self) -> None:
        """Menú de reportes."""
        menu("REPORTES", {
            "Inventario valorizado en pesos": self.reporte_inventario,
            "Libros para reponer": self.reporte_reposicion,
            "Histórico de cotizaciones": self.reporte_historico,
            "Comparación de precios con Cúspide": self.reporte_competencia})
