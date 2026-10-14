-- Esquema de la base de datos Book Manager
-- Dialecto: sqlite

CREATE TABLE generos (
	id INTEGER NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	descripcion VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

CREATE TABLE editoriales (
	id INTEGER NOT NULL, 
	nombre VARCHAR(150) NOT NULL, 
	cuit VARCHAR(11) NOT NULL, 
	condicion_iva VARCHAR(30) NOT NULL, 
	direccion VARCHAR(200) NOT NULL, 
	email VARCHAR(150) NOT NULL, 
	telefono VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (cuit)
);

CREATE TABLE monedas (
	id INTEGER NOT NULL, 
	codigo VARCHAR(3) NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	simbolo VARCHAR(10) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (codigo)
);

CREATE TABLE tipos_cotizacion (
	id INTEGER NOT NULL, 
	nombre VARCHAR(50) NOT NULL, 
	descripcion VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

CREATE TABLE libros (
	id INTEGER NOT NULL, 
	isbn VARCHAR(13) NOT NULL, 
	titulo VARCHAR(200) NOT NULL, 
	autor VARCHAR(150) NOT NULL, 
	editorial_id INTEGER NOT NULL, 
	genero_id INTEGER NOT NULL, 
	fecha_impresion DATE NOT NULL, 
	numero_impresion INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_libros_numero_impresion CHECK (numero_impresion >= 1), 
	UNIQUE (isbn), 
	FOREIGN KEY(editorial_id) REFERENCES editoriales (id) ON DELETE RESTRICT, 
	FOREIGN KEY(genero_id) REFERENCES generos (id) ON DELETE RESTRICT
);

CREATE TABLE precios (
	id INTEGER NOT NULL, 
	libro_id INTEGER NOT NULL, 
	moneda_id INTEGER NOT NULL, 
	valor NUMERIC(12, 2) NOT NULL, 
	fecha DATE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_precios_libro_moneda_fecha UNIQUE (libro_id, moneda_id, fecha), 
	CONSTRAINT ck_precios_valor CHECK (valor >= 0), 
	FOREIGN KEY(libro_id) REFERENCES libros (id) ON DELETE CASCADE, 
	FOREIGN KEY(moneda_id) REFERENCES monedas (id) ON DELETE RESTRICT
);

CREATE TABLE stock (
	libro_id INTEGER NOT NULL, 
	cantidad INTEGER NOT NULL, 
	stock_minimo INTEGER NOT NULL, 
	PRIMARY KEY (libro_id), 
	CONSTRAINT ck_stock_cantidad CHECK (cantidad >= 0), 
	CONSTRAINT ck_stock_minimo CHECK (stock_minimo >= 0), 
	FOREIGN KEY(libro_id) REFERENCES libros (id) ON DELETE CASCADE
);

CREATE TABLE cotizaciones_dolar (
	tipo_id INTEGER NOT NULL, 
	fecha DATE NOT NULL, 
	compra NUMERIC(12, 2) NOT NULL, 
	venta NUMERIC(12, 2) NOT NULL, 
	PRIMARY KEY (tipo_id, fecha), 
	CONSTRAINT ck_cotizaciones_valores CHECK (compra > 0 AND venta >= compra), 
	FOREIGN KEY(tipo_id) REFERENCES tipos_cotizacion (id) ON DELETE RESTRICT
);
