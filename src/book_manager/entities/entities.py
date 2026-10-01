"""Entidades del dominio del sistema Book Manager.

Libro, Genero, Editorial, Moneda, TipoCotizacion, Precio, Stock y
CotizacionDolar.
"""

import abc
import datetime
from typing import Any, Dict, Optional


class EntidadBase(abc.ABC):
    """Clase base de las entidades identificadas por un ID numérico."""

    def __init__(self, id: Optional[int] = None) -> None:
        """Inicializa la entidad con un ID opcional (lo asigna el repo)."""
        self._id = id

    @property
    def id(self) -> Optional[int]:
        """ID único de la entidad."""
        return self._id

    @id.setter
    def id(self, valor: Optional[int]) -> None:
        if valor is not None and (not isinstance(valor, int) or valor <= 0):
            raise ValueError("El ID debe ser un entero positivo.")
        self._id = valor

    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Devuelve la entidad como diccionario plano (para persistencia)."""

    @staticmethod
    def _validar_texto(valor: str, campo: str) -> str:
        """Valida que un texto no esté vacío y lo devuelve sin espacios."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"El campo '{campo}' no puede estar vacío.")
        return valor.strip()

    def __eq__(self, otro: object) -> bool:
        """Dos entidades son iguales si son del mismo tipo e ID."""
        if not isinstance(otro, self.__class__) or self.id is None:
            return NotImplemented
        return self.id == otro.id

    def __hash__(self) -> int:
        """Hash basado en el tipo y el ID."""
        return hash((self.__class__.__name__, self.id))


class Genero(EntidadBase):
    """Categoría literaria a la que pertenece un libro."""

    def __init__(self, nombre: str, descripcion: str = "",
                 id: Optional[int] = None) -> None:
        """Crea un género literario."""
        super().__init__(id)
        self.nombre = nombre
        self.descripcion = descripcion

    @property
    def nombre(self) -> str:
        """Nombre del género."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = self._validar_texto(valor, "nombre")

    @property
    def descripcion(self) -> str:
        """Descripción del género."""
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor: str) -> None:
        self._descripcion = (valor or "").strip()

    def to_dict(self) -> Dict[str, Any]:
        """Devuelve el género como diccionario."""
        return {"id": self.id, "nombre": self.nombre,
                "descripcion": self.descripcion}

    def __str__(self) -> str:
        """Representación legible del género."""
        return self.nombre

    def __repr__(self) -> str:
        """Representación técnica del género."""
        return f"Genero(id={self.id}, nombre={self.nombre!r})"


class Editorial(EntidadBase):
    """Proveedor/distribuidora que provee los libros a la librería."""

    CONDICIONES_IVA = ("Responsable Inscripto", "Monotributista", "Exento",
                       "Consumidor Final")

    def __init__(self, nombre: str, cuit: str, condicion_iva: str,
                 direccion: str = "", email: str = "", telefono: str = "",
                 id: Optional[int] = None) -> None:
        """Crea una editorial con sus datos fiscales y de contacto."""
        super().__init__(id)
        self.nombre = nombre
        self.cuit = cuit
        self.condicion_iva = condicion_iva
        self.direccion = direccion
        self.email = email
        self.telefono = telefono

    @property
    def nombre(self) -> str:
        """Razón social / nombre de la editorial."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = self._validar_texto(valor, "nombre")

    @property
    def cuit(self) -> str:
        """CUIT de la empresa, guardado sólo con dígitos (11)."""
        return self._cuit

    @cuit.setter
    def cuit(self, valor: str) -> None:
        digitos = "".join(c for c in str(valor) if c.isdigit())
        if not self.cuit_es_valido(digitos):
            raise ValueError("El CUIT no es válido.")
        self._cuit = digitos

    @property
    def cuit_formateado(self) -> str:
        """CUIT con el formato XX-XXXXXXXX-X."""
        return f"{self.cuit[:2]}-{self.cuit[2:10]}-{self.cuit[10]}"

    @staticmethod
    def cuit_es_valido(digitos: str) -> bool:
        """Verifica largo y dígito verificador del CUIT (módulo 11)."""
        if len(digitos) != 11 or not digitos.isdigit():
            return False
        pesos = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
        suma = sum(int(d) * p for d, p in zip(digitos[:10], pesos))
        verificador = 11 - suma % 11
        if verificador == 11:
            verificador = 0
        elif verificador == 10:
            verificador = 9
        return verificador == int(digitos[10])

    @property
    def condicion_iva(self) -> str:
        """Condición frente al IVA."""
        return self._condicion_iva

    @condicion_iva.setter
    def condicion_iva(self, valor: str) -> None:
        valor = self._validar_texto(valor, "condicion_iva")
        for condicion in self.CONDICIONES_IVA:
            if condicion.lower() == valor.lower():
                self._condicion_iva = condicion
                return
        raise ValueError(
            "Condición de IVA inválida. Opciones: "
            f"{', '.join(self.CONDICIONES_IVA)}.")

    @property
    def direccion(self) -> str:
        """Dirección de la empresa."""
        return self._direccion

    @direccion.setter
    def direccion(self, valor: str) -> None:
        self._direccion = (valor or "").strip()

    @property
    def email(self) -> str:
        """Email de contacto."""
        return self._email

    @email.setter
    def email(self, valor: str) -> None:
        valor = (valor or "").strip()
        if valor and "@" not in valor:
            raise ValueError("El email no es válido.")
        self._email = valor

    @property
    def telefono(self) -> str:
        """Teléfono de contacto."""
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        self._telefono = (valor or "").strip()

    def to_dict(self) -> Dict[str, Any]:
        """Devuelve la editorial como diccionario."""
        return {"id": self.id, "nombre": self.nombre, "cuit": self.cuit,
                "condicion_iva": self.condicion_iva,
                "direccion": self.direccion, "email": self.email,
                "telefono": self.telefono}

    def __str__(self) -> str:
        """Representación legible de la editorial."""
        return self.nombre

    def __repr__(self) -> str:
        """Representación técnica de la editorial."""
        return f"Editorial(id={self.id}, nombre={self.nombre!r})"


class Moneda(EntidadBase):
    """Moneda en la que se puede expresar un precio (ARS, USD, etc.)."""

    def __init__(self, codigo: str, nombre: str, simbolo: str = "",
                 id: Optional[int] = None) -> None:
        """Crea una moneda."""
        super().__init__(id)
        self.codigo = codigo
        self.nombre = nombre
        self.simbolo = simbolo

    @property
    def codigo(self) -> str:
        """Código ISO 4217 de la moneda (tres letras)."""
        return self._codigo

    @codigo.setter
    def codigo(self, valor: str) -> None:
        valor = self._validar_texto(valor, "codigo").upper()
        if len(valor) != 3 or not valor.isalpha():
            raise ValueError("El código de moneda debe tener 3 letras.")
        self._codigo = valor

    @property
    def nombre(self) -> str:
        """Nombre de la moneda."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = self._validar_texto(valor, "nombre")

    @property
    def simbolo(self) -> str:
        """Símbolo de la moneda."""
        return self._simbolo

    @simbolo.setter
    def simbolo(self, valor: str) -> None:
        self._simbolo = (valor or "").strip()

    def to_dict(self) -> Dict[str, Any]:
        """Devuelve la moneda como diccionario."""
        return {"id": self.id, "codigo": self.codigo, "nombre": self.nombre,
                "simbolo": self.simbolo}

    def __str__(self) -> str:
        """Representación legible de la moneda."""
        return self.codigo

    def __repr__(self) -> str:
        """Representación técnica de la moneda."""
        return f"Moneda(id={self.id}, codigo={self.codigo!r})"


class TipoCotizacion(EntidadBase):
    """Tipo de cotización del dólar (Oficial, Blue, MEP, etc.)."""

    def __init__(self, nombre: str, descripcion: str = "",
                 id: Optional[int] = None) -> None:
        """Crea un tipo de cotización."""
        super().__init__(id)
        self.nombre = nombre
        self.descripcion = descripcion

    @property
    def nombre(self) -> str:
        """Nombre del tipo de cotización."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = self._validar_texto(valor, "nombre")

    @property
    def descripcion(self) -> str:
        """Descripción del tipo de cotización."""
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor: str) -> None:
        self._descripcion = (valor or "").strip()

    def to_dict(self) -> Dict[str, Any]:
        """Devuelve el tipo de cotización como diccionario."""
        return {"id": self.id, "nombre": self.nombre,
                "descripcion": self.descripcion}

    def __str__(self) -> str:
        """Representación legible del tipo de cotización."""
        return self.nombre

    def __repr__(self) -> str:
        """Representación técnica del tipo de cotización."""
        return f"TipoCotizacion(id={self.id}, nombre={self.nombre!r})"


class Libro(EntidadBase):
    """Título del catálogo de la librería."""

    def __init__(self, isbn: str, titulo: str, autor: str,
                 editorial: Editorial, genero: Genero,
                 fecha_impresion: datetime.date, numero_impresion: int = 1,
                 id: Optional[int] = None) -> None:
        """Crea un libro asociado a una editorial y a un género."""
        super().__init__(id)
        self.isbn = isbn
        self.titulo = titulo
        self.autor = autor
        self.editorial = editorial
        self.genero = genero
        self.fecha_impresion = fecha_impresion
        self.numero_impresion = numero_impresion

    @property
    def isbn(self) -> str:
        """ISBN-10 o ISBN-13 (sólo dígitos; puede terminar en X)."""
        return self._isbn

    @isbn.setter
    def isbn(self, valor: str) -> None:
        limpio = self._validar_texto(str(valor), "isbn")
        limpio = limpio.replace("-", "").replace(" ", "").upper()
        cuerpo = limpio[:-1] if limpio.endswith("X") else limpio
        if len(limpio) not in (10, 13) or not cuerpo.isdigit():
            raise ValueError("El ISBN debe tener 10 o 13 dígitos.")
        self._isbn = limpio

    @property
    def titulo(self) -> str:
        """Título del libro."""
        return self._titulo

    @titulo.setter
    def titulo(self, valor: str) -> None:
        self._titulo = self._validar_texto(valor, "titulo")

    @property
    def autor(self) -> str:
        """Autor del libro."""
        return self._autor

    @autor.setter
    def autor(self, valor: str) -> None:
        self._autor = self._validar_texto(valor, "autor")

    @property
    def editorial(self) -> Editorial:
        """Editorial que provee el libro."""
        return self._editorial

    @editorial.setter
    def editorial(self, valor: Editorial) -> None:
        if not isinstance(valor, Editorial):
            raise TypeError("La editorial debe ser un objeto Editorial.")
        self._editorial = valor

    @property
    def genero(self) -> Genero:
        """Género literario del libro."""
        return self._genero

    @genero.setter
    def genero(self, valor: Genero) -> None:
        if not isinstance(valor, Genero):
            raise TypeError("El género debe ser un objeto Genero.")
        self._genero = valor

    @property
    def fecha_impresion(self) -> datetime.date:
        """Fecha de impresión del ejemplar."""
        return self._fecha_impresion

    @fecha_impresion.setter
    def fecha_impresion(self, valor: datetime.date) -> None:
        if not isinstance(valor, datetime.date):
            raise TypeError("La fecha de impresión debe ser un objeto date.")
        if valor > datetime.date.today():
            raise ValueError("La fecha de impresión no puede ser futura.")
        self._fecha_impresion = valor

    @property
    def numero_impresion(self) -> int:
        """Número de impresión (1 = primera impresión)."""
        return self._numero_impresion

    @numero_impresion.setter
    def numero_impresion(self, valor: int) -> None:
        valor = int(valor)
        if valor < 1:
            raise ValueError("El número de impresión debe ser 1 o mayor.")
        self._numero_impresion = valor

    def to_dict(self) -> Dict[str, Any]:
        """Devuelve el libro como diccionario (relaciones por ID)."""
        return {"id": self.id, "isbn": self.isbn, "titulo": self.titulo,
                "autor": self.autor, "editorial_id": self.editorial.id,
                "genero_id": self.genero.id,
                "fecha_impresion": self.fecha_impresion.isoformat(),
                "numero_impresion": self.numero_impresion}

    def __str__(self) -> str:
        """Representación legible del libro."""
        return f"{self.titulo} - {self.autor} ({self.editorial})"

    def __repr__(self) -> str:
        """Representación técnica del libro."""
        return (f"Libro(id={self.id}, isbn={self.isbn!r}, "
                f"titulo={self.titulo!r})")


class Precio(EntidadBase):
    """Valor monetario de un libro en una moneda determinada."""

    def __init__(self, libro: Libro, moneda: Moneda, valor: float,
                 fecha: Optional[datetime.date] = None,
                 id: Optional[int] = None) -> None:
        """Crea un precio para un libro en una moneda y fecha."""
        super().__init__(id)
        self.libro = libro
        self.moneda = moneda
        self.valor = valor
        self.fecha = fecha or datetime.date.today()

    @property
    def libro(self) -> Libro:
        """Libro al que corresponde el precio."""
        return self._libro

    @libro.setter
    def libro(self, valor: Libro) -> None:
        if not isinstance(valor, Libro):
            raise TypeError("El libro debe ser un objeto Libro.")
        self._libro = valor

    @property
    def moneda(self) -> Moneda:
        """Moneda en la que se expresa el precio."""
        return self._moneda

    @moneda.setter
    def moneda(self, valor: Moneda) -> None:
        if not isinstance(valor, Moneda):
            raise TypeError("La moneda debe ser un objeto Moneda.")
        self._moneda = valor

    @property
    def valor(self) -> float:
        """Importe del precio."""
        return self._valor

    @valor.setter
    def valor(self, valor: float) -> None:
        valor = float(valor)
        if valor < 0:
            raise ValueError("El precio no puede ser negativo.")
        self._valor = round(valor, 2)

    @property
    def fecha(self) -> datetime.date:
        """Fecha de vigencia del precio."""
        return self._fecha

    @fecha.setter
    def fecha(self, valor: datetime.date) -> None:
        if not isinstance(valor, datetime.date):
            raise TypeError("La fecha debe ser un objeto date.")
        self._fecha = valor

    def to_dict(self) -> Dict[str, Any]:
        """Devuelve el precio como diccionario (relaciones por ID)."""
        return {"id": self.id, "libro_id": self.libro.id,
                "moneda_id": self.moneda.id, "valor": self.valor,
                "fecha": self.fecha.isoformat()}

    def __str__(self) -> str:
        """Representación legible del precio."""
        simbolo = self.moneda.simbolo or self.moneda.codigo
        return f"{simbolo} {self.valor:,.2f}"

    def __repr__(self) -> str:
        """Representación técnica del precio."""
        return (f"Precio(id={self.id}, libro_id={self.libro.id}, "
                f"moneda={self.moneda.codigo!r}, valor={self.valor})")


class Stock:
    """Cantidad disponible de un libro (identificado por el libro)."""

    def __init__(self, libro: Libro, cantidad: int = 0,
                 stock_minimo: int = 0) -> None:
        """Crea el registro de stock de un libro."""
        self.libro = libro
        self.cantidad = cantidad
        self.stock_minimo = stock_minimo

    @property
    def libro(self) -> Libro:
        """Libro al que corresponde el stock."""
        return self._libro

    @libro.setter
    def libro(self, valor: Libro) -> None:
        if not isinstance(valor, Libro):
            raise TypeError("El libro debe ser un objeto Libro.")
        self._libro = valor

    @property
    def libro_id(self) -> Optional[int]:
        """ID del libro, que identifica al registro de stock."""
        return self.libro.id

    @property
    def cantidad(self) -> int:
        """Unidades disponibles."""
        return self._cantidad

    @cantidad.setter
    def cantidad(self, valor: int) -> None:
        valor = int(valor)
        if valor < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        self._cantidad = valor

    @property
    def stock_minimo(self) -> int:
        """Cantidad mínima deseada antes de reponer."""
        return self._stock_minimo

    @stock_minimo.setter
    def stock_minimo(self, valor: int) -> None:
        valor = int(valor)
        if valor < 0:
            raise ValueError("El stock mínimo no puede ser negativo.")
        self._stock_minimo = valor

    @property
    def requiere_reposicion(self) -> bool:
        """Indica si la cantidad está por debajo del stock mínimo."""
        return self.cantidad < self.stock_minimo

    def agregar(self, unidades: int) -> None:
        """Suma unidades al stock."""
        if unidades <= 0:
            raise ValueError("Las unidades a agregar deben ser positivas.")
        self.cantidad += unidades

    def retirar(self, unidades: int) -> None:
        """Resta unidades del stock, validando que alcance."""
        if unidades <= 0:
            raise ValueError("Las unidades a retirar deben ser positivas.")
        if unidades > self.cantidad:
            raise ValueError("No hay stock suficiente.")
        self.cantidad -= unidades

    def to_dict(self) -> Dict[str, Any]:
        """Devuelve el stock como diccionario (relaciones por ID)."""
        return {"libro_id": self.libro_id, "cantidad": self.cantidad,
                "stock_minimo": self.stock_minimo}

    def __str__(self) -> str:
        """Representación legible del stock."""
        return f"{self.libro.titulo}: {self.cantidad} u."

    def __repr__(self) -> str:
        """Representación técnica del stock."""
        return f"Stock(libro_id={self.libro_id}, cantidad={self.cantidad})"


class CotizacionDolar:
    """Registro histórico de la cotización del dólar por tipo y fecha."""

    def __init__(self, tipo: TipoCotizacion, fecha: datetime.date,
                 compra: float, venta: float) -> None:
        """Crea una cotización (identificada por tipo y fecha)."""
        self.tipo = tipo
        self.fecha = fecha
        self._compra = 0.0
        self._venta = float("inf")
        self.compra = compra
        self.venta = venta

    @property
    def tipo(self) -> TipoCotizacion:
        """Tipo de cotización (Oficial, Blue, MEP, etc.)."""
        return self._tipo

    @tipo.setter
    def tipo(self, valor: TipoCotizacion) -> None:
        if not isinstance(valor, TipoCotizacion):
            raise TypeError("El tipo debe ser un objeto TipoCotizacion.")
        self._tipo = valor

    @property
    def tipo_id(self) -> Optional[int]:
        """ID del tipo de cotización."""
        return self.tipo.id

    @property
    def fecha(self) -> datetime.date:
        """Fecha de la cotización."""
        return self._fecha

    @fecha.setter
    def fecha(self, valor: datetime.date) -> None:
        if not isinstance(valor, datetime.date):
            raise TypeError("La fecha debe ser un objeto date.")
        self._fecha = valor

    @property
    def compra(self) -> float:
        """Valor de compra en pesos."""
        return self._compra

    @compra.setter
    def compra(self, valor: float) -> None:
        valor = float(valor)
        if valor <= 0:
            raise ValueError("La cotización de compra debe ser positiva.")
        if valor > self._venta:
            raise ValueError("La compra no puede superar a la venta.")
        self._compra = round(valor, 2)

    @property
    def venta(self) -> float:
        """Valor de venta en pesos."""
        return self._venta

    @venta.setter
    def venta(self, valor: float) -> None:
        valor = float(valor)
        if valor <= 0:
            raise ValueError("La cotización de venta debe ser positiva.")
        if valor < self._compra:
            raise ValueError("La venta no puede ser menor a la compra.")
        self._venta = round(valor, 2)

    @property
    def promedio(self) -> float:
        """Promedio entre compra y venta."""
        return round((self.compra + self.venta) / 2, 2)

    def convertir_a_pesos(self, monto_usd: float) -> float:
        """Convierte un monto en dólares a pesos (valor de venta)."""
        return round(float(monto_usd) * self.venta, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Devuelve la cotización como diccionario (relaciones por ID)."""
        return {"tipo_id": self.tipo_id, "fecha": self.fecha.isoformat(),
                "compra": self.compra, "venta": self.venta}

    def __str__(self) -> str:
        """Representación legible de la cotización."""
        return (f"Dólar {self.tipo} {self.fecha:%d/%m/%Y}: "
                f"compra ${self.compra:,.2f} / venta ${self.venta:,.2f}")

    def __repr__(self) -> str:
        """Representación técnica de la cotización."""
        return (f"CotizacionDolar(tipo_id={self.tipo_id}, "
                f"fecha={self.fecha.isoformat()!r}, venta={self.venta})")
