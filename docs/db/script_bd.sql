-- =====================================================================
-- Diseño de la Base de Datos del Proyecto Integrador
-- Sistema de gestión documental de cuentas de cobro
-- Motor: MySQL 8, InnoDB, utf8mb4
-- =====================================================================

DROP DATABASE IF EXISTS gestion_documental;
CREATE DATABASE gestion_documental
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE gestion_documental;

-- =====================================================================
-- Catálogos y tablas de acceso
-- =====================================================================

CREATE TABLE roles (
    id_rol       SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre       VARCHAR(50)  NOT NULL,
    descripcion  VARCHAR(200) NOT NULL,
    activo       TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (id_rol),
    UNIQUE KEY uq_roles_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE permisos (
    id_permiso  SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    codigo      VARCHAR(50)  NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    modulo      VARCHAR(50)  NOT NULL,
    PRIMARY KEY (id_permiso),
    UNIQUE KEY uq_permisos_codigo (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE roles_permisos (
    id_rol     SMALLINT UNSIGNED NOT NULL,
    id_permiso SMALLINT UNSIGNED NOT NULL,
    PRIMARY KEY (id_rol, id_permiso),
    KEY idx_roles_permisos_id_permiso (id_permiso),
    CONSTRAINT fk_roles_permisos_rol
        FOREIGN KEY (id_rol) REFERENCES roles (id_rol)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    CONSTRAINT fk_roles_permisos_permiso
        FOREIGN KEY (id_permiso) REFERENCES permisos (id_permiso)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE usuarios (
    id_usuario            INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre                VARCHAR(100) NOT NULL,
    apellido              VARCHAR(100) NOT NULL,
    correo                VARCHAR(120) NOT NULL,
    id_rol                SMALLINT UNSIGNED NOT NULL,
    cargo                 VARCHAR(100) NOT NULL,
    contrasena_hash       VARCHAR(255) NOT NULL,
    activo                TINYINT(1) NOT NULL DEFAULT 1,
    ultimo_acceso         DATETIME NULL,
    intentos_fallidos     TINYINT UNSIGNED NOT NULL DEFAULT 0,
    bloqueado_hasta       DATETIME NULL,
    debe_cambiar_contrasena TINYINT(1) NOT NULL DEFAULT 1,
    fecha_registro        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario),
    UNIQUE KEY uq_usuarios_correo (correo),
    KEY idx_usuarios_id_rol (id_rol),
    CONSTRAINT fk_usuarios_rol
        FOREIGN KEY (id_rol) REFERENCES roles (id_rol)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE contratistas (
    id_contratista  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    tipo_persona    ENUM('NATURAL','JURIDICA') NOT NULL,
    nombre_completo VARCHAR(200) NOT NULL,
    nit_cedula      VARCHAR(30) NOT NULL,
    telefono        VARCHAR(30) NULL,
    correo          VARCHAR(120) NULL,
    direccion       VARCHAR(200) NULL,
    activo          TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (id_contratista),
    UNIQUE KEY uq_contratistas_nit_cedula (nit_cedula)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE estados_contrato (
    id_estado_contrato TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre             VARCHAR(50)  NOT NULL,
    descripcion        VARCHAR(200) NOT NULL,
    PRIMARY KEY (id_estado_contrato),
    UNIQUE KEY uq_estados_contrato_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE contratos (
    id_contrato       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_contratista    INT UNSIGNED NOT NULL,
    numero_contrato   VARCHAR(50) NOT NULL,
    objeto_contrato   TEXT NOT NULL,
    valor_total       DECIMAL(14,2) NOT NULL,
    fecha_inicio      DATE NOT NULL,
    fecha_fin         DATE NOT NULL,
    id_estado_contrato TINYINT UNSIGNED NOT NULL,
    id_supervisor     INT UNSIGNED NOT NULL,
    PRIMARY KEY (id_contrato),
    UNIQUE KEY uq_contratos_numero (numero_contrato),
    KEY idx_contratos_id_contratista (id_contratista),
    KEY idx_contratos_id_estado_contrato (id_estado_contrato),
    KEY idx_contratos_id_supervisor (id_supervisor),
    CONSTRAINT fk_contratos_contratista
        FOREIGN KEY (id_contratista) REFERENCES contratistas (id_contratista)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_contratos_estado
        FOREIGN KEY (id_estado_contrato) REFERENCES estados_contrato (id_estado_contrato)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_contratos_supervisor
        FOREIGN KEY (id_supervisor) REFERENCES usuarios (id_usuario)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_contratos_valor_total CHECK (valor_total > 0),
    CONSTRAINT chk_contratos_fechas CHECK (fecha_fin >= fecha_inicio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE estados_cuenta (
    id_estado_cuenta TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre           VARCHAR(50)  NOT NULL,
    descripcion      VARCHAR(200) NOT NULL,
    PRIMARY KEY (id_estado_cuenta),
    UNIQUE KEY uq_estados_cuenta_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE cuentas_cobro (
    id_cuenta          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_contrato        INT UNSIGNED NOT NULL,
    numero_radicado    VARCHAR(30) NOT NULL,
    numero_cuenta      VARCHAR(30) NOT NULL,
    valor_cobro        DECIMAL(14,2) NOT NULL,
    concepto_pago      TEXT NOT NULL,
    fecha_presentacion DATE NOT NULL,
    id_estado_cuenta   TINYINT UNSIGNED NOT NULL,
    observaciones      TEXT NULL,
    id_usuario         INT UNSIGNED NOT NULL,
    fecha_registro     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_cuenta),
    UNIQUE KEY uq_cuentas_cobro_radicado (numero_radicado),
    UNIQUE KEY uq_cuentas_cobro_contrato_cuenta (id_contrato, numero_cuenta),
    KEY idx_cuentas_cobro_id_estado_cuenta (id_estado_cuenta),
    KEY idx_cuentas_cobro_id_usuario (id_usuario),
    CONSTRAINT fk_cuentas_cobro_contrato
        FOREIGN KEY (id_contrato) REFERENCES contratos (id_contrato)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_cuentas_cobro_estado
        FOREIGN KEY (id_estado_cuenta) REFERENCES estados_cuenta (id_estado_cuenta)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_cuentas_cobro_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_cuentas_cobro_valor CHECK (valor_cobro > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE historial_estado_cuenta (
    id_historial      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_cuenta         INT UNSIGNED NOT NULL,
    id_estado_anterior TINYINT UNSIGNED NULL,
    id_estado_nuevo   TINYINT UNSIGNED NOT NULL,
    id_usuario        INT UNSIGNED NOT NULL,
    fecha_cambio      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observacion       VARCHAR(300) NULL,
    PRIMARY KEY (id_historial),
    KEY idx_historial_id_cuenta (id_cuenta),
    KEY idx_historial_id_estado_anterior (id_estado_anterior),
    KEY idx_historial_id_estado_nuevo (id_estado_nuevo),
    KEY idx_historial_id_usuario (id_usuario),
    CONSTRAINT fk_historial_cuenta
        FOREIGN KEY (id_cuenta) REFERENCES cuentas_cobro (id_cuenta)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_historial_estado_anterior
        FOREIGN KEY (id_estado_anterior) REFERENCES estados_cuenta (id_estado_cuenta)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_historial_estado_nuevo
        FOREIGN KEY (id_estado_nuevo) REFERENCES estados_cuenta (id_estado_cuenta)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_historial_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tipos_documento (
    id_tipo_documento TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre            VARCHAR(50)  NOT NULL,
    descripcion       VARCHAR(200) NOT NULL,
    PRIMARY KEY (id_tipo_documento),
    UNIQUE KEY uq_tipos_documento_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE documentos_adjuntos (
    id_documento      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_cuenta         INT UNSIGNED NOT NULL,
    id_tipo_documento TINYINT UNSIGNED NOT NULL,
    id_usuario        INT UNSIGNED NOT NULL,
    nombre_original   VARCHAR(255) NOT NULL,
    ruta_archivo      VARCHAR(300) NOT NULL,
    tipo_mime         VARCHAR(100) NULL,
    hash_sha256       CHAR(64) NULL,
    tamano_bytes      BIGINT UNSIGNED NULL,
    origen            ENUM('LOCAL','URL') NOT NULL,
    fecha_carga       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_documento),
    KEY idx_documentos_id_cuenta (id_cuenta),
    KEY idx_documentos_id_tipo_documento (id_tipo_documento),
    KEY idx_documentos_id_usuario (id_usuario),
    CONSTRAINT fk_documentos_cuenta
        FOREIGN KEY (id_cuenta) REFERENCES cuentas_cobro (id_cuenta)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    CONSTRAINT fk_documentos_tipo
        FOREIGN KEY (id_tipo_documento) REFERENCES tipos_documento (id_tipo_documento)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_documentos_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_documentos_metadatos CHECK (
        origen = 'URL' OR
        (tipo_mime IS NOT NULL AND hash_sha256 IS NOT NULL AND tamano_bytes IS NOT NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- Datos de prueba
-- =====================================================================

-- roles
INSERT INTO roles (id_rol, nombre, descripcion, activo) VALUES
(1, 'Administrador', 'Administración general del sistema y de usuarios', 1),
(2, 'Radicador', 'Registra cuentas de cobro y adjunta documentos', 1),
(3, 'Revisor', 'Revisa cuentas y cambia su estado', 1),
(4, 'Supervisor', 'Supervisa contratos y cambia el estado de las cuentas', 1),
(5, 'Consulta', 'Solo lectura de cuentas y documentos', 1);

-- permisos
INSERT INTO permisos (id_permiso, codigo, descripcion, modulo) VALUES
(1, 'usuarios.gestionar', 'Crear, editar y desactivar usuarios', 'usuarios'),
(2, 'contratistas.gestionar', 'Crear, editar y desactivar contratistas', 'contratistas'),
(3, 'contratistas.consultar', 'Consultar contratistas', 'contratistas'),
(4, 'contratos.gestionar', 'Crear, editar y cambiar el estado de contratos', 'contratos'),
(5, 'contratos.consultar', 'Consultar contratos', 'contratos'),
(6, 'cuentas.radicar', 'Crear cuentas de cobro', 'cuentas'),
(7, 'cuentas.consultar', 'Consultar cuentas de cobro', 'cuentas'),
(8, 'cuentas.editar', 'Editar cuentas de cobro', 'cuentas'),
(9, 'cuentas.cambiar_estado', 'Cambiar el estado de una cuenta', 'cuentas'),
(10, 'cuentas.pagar', 'Marcar una cuenta como pagada', 'cuentas'),
(11, 'documentos.adjuntar', 'Subir documentos adjuntos', 'documentos'),
(12, 'documentos.consultar', 'Consultar documentos adjuntos', 'documentos'),
(13, 'documentos.eliminar', 'Eliminar documentos adjuntos', 'documentos');

-- roles_permisos (36 filas, según la matriz)
INSERT INTO roles_permisos (id_rol, id_permiso) VALUES
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
(1, 9), (1, 10), (1, 11), (1, 12), (1, 13),
(2, 3), (2, 5), (2, 6), (2, 7), (2, 8), (2, 11), (2, 12), (2, 13),
(3, 3), (3, 5), (3, 7), (3, 9), (3, 12),
(4, 3), (4, 4), (4, 5), (4, 7), (4, 9), (4, 12),
(5, 3), (5, 5), (5, 7), (5, 12);

-- usuarios (hash bcrypt de ejemplo, no contraseñas reales)
INSERT INTO usuarios
  (id_usuario, nombre, apellido, correo, id_rol, cargo, contrasena_hash, activo,
   ultimo_acceso, intentos_fallidos, bloqueado_hasta, debe_cambiar_contrasena, fecha_registro) VALUES
(1, 'Ana', 'Rodríguez', 'ana.rodriguez@entidad.gov.co', 1,
 'Coordinadora de Gestión Documental',
 '$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0', 1,
 '2025-06-20 08:30:00', 0, NULL, 0, '2025-01-06 08:00:00'),
(2, 'Jorge', 'Martínez', 'jorge.martinez@entidad.gov.co', 4,
 'Jefe de Presupuesto',
 '$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0', 1,
 '2025-06-18 16:45:00', 0, NULL, 0, '2025-01-06 08:30:00'),
(3, 'Luz', 'Paredes', 'luz.paredes@entidad.gov.co', 2,
 'Auxiliar Administrativo',
 '$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0', 1,
 '2025-06-25 09:05:00', 0, NULL, 1, '2025-01-07 09:00:00'),
(4, 'Ricardo', 'Gómez', 'ricardo.gomez@entidad.gov.co', 4,
 'Jefe de Servicios Generales',
 '$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0', 1,
 '2025-06-19 14:20:00', 0, NULL, 0, '2025-01-07 09:30:00'),
(5, 'María', 'Cifuentes', 'maria.cifuentes@entidad.gov.co', 3,
 'Profesional de Contratación',
 '$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0', 1,
 '2025-06-24 15:00:00', 5, '2025-06-30 10:00:00', 0, '2025-01-08 08:00:00'),
(6, 'Pedro', 'Sarmiento', 'pedro.sarmiento@entidad.gov.co', 5,
 'Técnico Administrativo',
 '$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0', 0,
 NULL, 0, NULL, 1, '2025-02-03 10:00:00');

-- contratistas
INSERT INTO contratistas
  (id_contratista, tipo_persona, nombre_completo, nit_cedula, telefono, correo, direccion, activo) VALUES
(1, 'NATURAL', 'Luis Fernando Rojas', '1024567891', '3112003456',
 'luis.rojas@correo.com', 'Calle 12 # 34-56, Bogotá', 1),
(2, 'JURIDICA', 'Constructora Andina S.A.S.', '901234567', '6014567890',
 'contacto@constructoraandina.com', 'Av. El Dorado # 68A-45, Bogotá', 1),
(3, 'NATURAL', 'Carmen Elena Duarte', '52213789', '3125678901',
 'carmen.duarte@correo.com', 'Carrera 45 # 78-90, Medellín', 1),
(4, 'JURIDICA', 'Servicios Integrales del Caribe Ltda.', '890123456', '6055551234',
 'gerencia@servicioscaribe.com', 'Calle 30 # 15-20, Barranquilla', 1),
(5, 'NATURAL', 'Andrés Felipe Torres', '76543210', '3156789012',
 'andres.torres@correo.com', 'Transversal 5 # 22-11, Cali', 1),
(6, 'JURIDICA', 'Almacén y Suministros del Oriente S.A.', '910234567', '6076543210',
 'ventas@suministrosoriente.com', 'Cra 23 # 40-55, Bucaramanga', 0);

-- estados_contrato
INSERT INTO estados_contrato (id_estado_contrato, nombre, descripcion) VALUES
(1, 'ACTIVO', 'Contrato en ejecución'),
(2, 'SUSPENDIDO', 'Ejecución detenida temporalmente'),
(3, 'LIQUIDADO', 'Obligaciones cumplidas y finiquitadas'),
(4, 'TERMINADO', 'Finalizado por cumplimiento del plazo'),
(5, 'CANCELADO', 'Dejado sin efecto antes de terminarse');

-- contratos (supervisores: usuarios 2 y 4, ambos con rol Supervisor)
INSERT INTO contratos
  (id_contrato, id_contratista, numero_contrato, objeto_contrato, valor_total,
   fecha_inicio, fecha_fin, id_estado_contrato, id_supervisor) VALUES
(1, 2, 'CONT-2025-001', 'Construcción de la sede administrativa del archivo documental.',
 450000000.00, '2025-01-15', '2025-12-31', 1, 2),
(2, 1, 'CONT-2025-002', 'Prestación de servicios de asesoría jurídica en contratación pública.',
 96000000.00, '2025-02-01', '2025-08-31', 1, 4),
(3, 3, 'CONT-2025-003', 'Suministro de papelería y útiles de oficina.',
 32500000.00, '2025-01-10', '2025-06-30', 3, 2),
(4, 4, 'CONT-2025-004', 'Servicio de limpieza y mantenimiento de instalaciones.',
 180000000.00, '2025-03-01', '2026-02-28', 1, 4),
(5, 5, 'CONT-2025-005', 'Servicios de soporte técnico en infraestructura de TI.',
 72000000.00, '2025-04-01', '2025-10-31', 2, 2),
(6, 1, 'CONT-2025-006', 'Capacitación en gestión documental para el personal.',
 18000000.00, '2025-05-01', '2025-07-31', 4, 4);

-- estados_cuenta
INSERT INTO estados_cuenta (id_estado_cuenta, nombre, descripcion) VALUES
(1, 'RECIBIDA', 'Radicada, pendiente de revisión'),
(2, 'EN_REVISION', 'En verificación por el área encargada'),
(3, 'APROBADA', 'Aprobada para pago'),
(4, 'RECHAZADA', 'Devuelta con observaciones'),
(5, 'PAGADA', 'Pago efectuado'),
(6, 'ANULADA', 'Dejada sin efecto');

-- cuentas_cobro (mismo numero_cuenta en contratos distintos, permitido por el UNIQUE compuesto)
INSERT INTO cuentas_cobro
  (id_cuenta, id_contrato, numero_radicado, numero_cuenta, valor_cobro, concepto_pago,
   fecha_presentacion, id_estado_cuenta, observaciones, id_usuario, fecha_registro, fecha_actualizacion) VALUES
(1, 1, 'RAD-2025-0001', 'CUENTA-001', 37500000.00,
 'Acta parcial 1 - Construcción sede administrativa.', '2025-03-20', 3,
 'Revisado por presupuesto, sin novedades.', 3, '2025-03-20 09:00:00', '2025-03-23 09:00:00'),
(2, 2, 'RAD-2025-0002', 'CUENTA-001', 8000000.00,
 'Honorarios mes de marzo - asesoría jurídica.', '2025-03-31', 2, NULL, 3, '2025-03-31 09:00:00', '2025-04-02 09:00:00'),
(3, 3, 'RAD-2025-0003', 'CUENTA-001', 5420000.00,
 'Entrega final suministro de papelería.', '2025-06-25', 1, NULL, 3, '2025-06-25 09:00:00', '2025-06-25 09:00:00'),
(4, 4, 'RAD-2025-0004', 'CUENTA-001', 15000000.00,
 'Servicio de limpieza del mes de mayo.', '2025-05-31', 4,
 'Falta certificado de paz y salvo del contratista.', 3, '2025-05-31 09:00:00', '2025-06-05 09:00:00'),
(5, 5, 'RAD-2025-0005', 'CUENTA-001', 6000000.00,
 'Soporte técnico abril - mayo.', '2025-06-05', 5, NULL, 3, '2025-06-05 09:00:00', '2025-06-16 09:00:00'),
(6, 6, 'RAD-2025-0006', 'CUENTA-001', 3000000.00,
 'Primer taller de capacitación en gestión documental.', '2025-06-15', 6,
 'Solicitud anulada por el contratista.', 3, '2025-06-15 09:00:00', '2025-06-17 09:00:00');

-- historial_estado_cuenta (cada cuenta termina en su estado actual)
INSERT INTO historial_estado_cuenta
  (id_historial, id_cuenta, id_estado_anterior, id_estado_nuevo, id_usuario, observacion, fecha_cambio) VALUES
(1, 1, NULL, 1, 3, 'Cuenta radicada', '2025-03-20 09:00:00'),
(2, 1, 1, 3, 5, 'Aprobada por contratación', '2025-03-23 09:00:00'),
(3, 2, NULL, 1, 3, 'Cuenta radicada', '2025-03-31 09:00:00'),
(4, 2, 1, 2, 5, 'En revisión de soportes', '2025-04-02 09:00:00'),
(5, 3, NULL, 1, 3, 'Cuenta radicada', '2025-06-25 09:00:00'),
(6, 4, NULL, 1, 3, 'Cuenta radicada', '2025-05-31 09:00:00'),
(7, 4, 1, 4, 5, 'Rechazada: falta paz y salvo', '2025-06-05 09:00:00'),
(8, 5, NULL, 1, 3, 'Cuenta radicada', '2025-06-05 09:00:00'),
(9, 5, 1, 3, 5, 'Aprobada por contratación', '2025-06-09 09:00:00'),
(10, 5, 3, 5, 1, 'Pago efectuado', '2025-06-16 09:00:00'),
(11, 6, NULL, 1, 3, 'Cuenta radicada', '2025-06-15 09:00:00'),
(12, 6, 1, 6, 1, 'Anulada por solicitud del contratista', '2025-06-17 09:00:00');

-- tipos_documento
INSERT INTO tipos_documento (id_tipo_documento, nombre, descripcion) VALUES
(1, 'CUENTA_COBRO', 'Cuenta de cobro propiamente dicha'),
(2, 'CERTIFICADO', 'Certificaciones exigidas al contratista'),
(3, 'RUT', 'Registro Único Tributario'),
(4, 'CEDULA', 'Documento de identidad'),
(5, 'POLIZA', 'Pólizas de cumplimiento'),
(6, 'OTRO', 'Documentos no clasificados');

-- documentos_adjuntos (LOCAL con MIME, hash y tamaño; URL con esos campos en NULL)
INSERT INTO documentos_adjuntos
  (id_documento, id_cuenta, id_tipo_documento, id_usuario, nombre_original, ruta_archivo,
   tipo_mime, hash_sha256, tamano_bytes, origen, fecha_carga) VALUES
(1, 1, 1, 3, 'acta_parcial_1.pdf', '/uploads/acta_parcial_1.pdf', 'application/pdf',
 'aedcbf18f4a5a30426d83622b75e7b1ce5a010b550451fcfcf2dc28fb6789527', 839680, 'LOCAL', '2025-03-20 09:00:00'),
(2, 1, 2, 3, 'certificado_constructora.pdf', '/uploads/certificado_constructora.pdf', 'application/pdf',
 'b988f59608d692fa62192dcfae2279811f055372fa8fb00f4d5264a72f1ba7d5', 440320, 'LOCAL', '2025-03-20 09:00:00'),
(3, 1, 5, 3, 'poliza_cumplimiento.pdf', '/uploads/poliza_cumplimiento.pdf', 'application/pdf',
 '42c076369bcd350d9127a5f811263cb6eb8151fec5712853069fd436b54504d4', 655360, 'LOCAL', '2025-03-20 09:00:00'),
(4, 2, 1, 3, 'cuenta_cobro_marzo.pdf', '/uploads/cuenta_cobro_marzo.pdf', 'application/pdf',
 '46be0955beadf4185e035d9b1fb0b47246a575ba9b917234627af7074879ee82', 399360, 'LOCAL', '2025-03-31 09:00:00'),
(5, 3, 4, 3, 'cedula_luis.jpg', 'https://example.com/cedula_luis.jpg',
 NULL, NULL, NULL, 'URL', '2025-06-25 09:00:00'),
(6, 4, 3, 3, 'rut_servicios_caribe.pdf', 'https://example.com/rut_servicios_caribe.pdf',
 NULL, NULL, NULL, 'URL', '2025-05-31 09:00:00'),
(7, 5, 1, 3, 'soporte_tecnico_mayo.pdf', '/uploads/soporte_tecnico_mayo.pdf', 'application/pdf',
 '6af0cf0895095a5ae12e585681e1b6bb1e9f8b599d84d762b1e07a117863fabf', 286720, 'LOCAL', '2025-06-05 09:00:00'),
(8, 6, 6, 3, 'observaciones_anulacion.pdf', '/uploads/observaciones_anulacion.pdf', 'application/pdf',
 'dec262043cd5123bed5ddd5cf131c4dd8232077ff13715c522e14971cd97097e', 122880, 'LOCAL', '2025-06-15 09:00:00');
