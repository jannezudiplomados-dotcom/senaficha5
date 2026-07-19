-- ============================================
-- Sistema de Gestion de Fichas SENA
-- ============================================
CREATE DATABASE IF NOT EXISTS sena_fichas4
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sena_fichas4;

-- Tabla: programas
CREATE TABLE IF NOT EXISTS programas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    duracion_meses INT DEFAULT 0,
    fecha_inicio DATE,
    fecha_fin DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Tabla: colegios
CREATE TABLE IF NOT EXISTS colegios (
    idcolegio INT AUTO_INCREMENT PRIMARY KEY,
    nombre_colegio VARCHAR(200) NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Tabla: fichas
CREATE TABLE IF NOT EXISTS fichas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero VARCHAR(50) NOT NULL UNIQUE,
    programa_id INT,
    colegio_id INT DEFAULT NULL,
    jornada ENUM('Manana','Tarde','Noche','Mixta') DEFAULT 'Manana',
    fecha_inicio DATE,
    fecha_fin DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ficha_programa FOREIGN KEY (programa_id)
        REFERENCES programas(id) ON DELETE CASCADE,
    CONSTRAINT fk_ficha_colegio FOREIGN KEY (colegio_id)
        REFERENCES colegios(idcolegio) ON DELETE SET NULL,
    INDEX idx_ficha_programa (programa_id),
    INDEX idx_ficha_colegio (colegio_id)
) ENGINE=InnoDB;

-- Tabla: acudientes
CREATE TABLE IF NOT EXISTS acudientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  identificacion VARCHAR(30) NULL,
  nombres_completos VARCHAR(200) NOT NULL,
  correo VARCHAR(150) NULL,
  telefono VARCHAR(30) NULL,
  parentesco VARCHAR(50) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_acudiente_identificacion (identificacion)
) ENGINE=InnoDB;

-- Tabla: usuarios (aprendices)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    identificacion VARCHAR(30) NOT NULL,
    tipo_documento ENUM('CC','TI','CE','PEP','PPT') DEFAULT 'CC',
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    correo VARCHAR(150),
    correo_institucional VARCHAR(150) NULL,
    telefono VARCHAR(30),
    direccion VARCHAR(255),
    acudiente_id INT NULL,
    ficha_id INT,
    firma VARCHAR(255),
    foto LONGTEXT NULL,
    portafolio_url VARCHAR(500) NULL,
    estado ENUM('Activo','Retirado','Graduado') DEFAULT 'Activo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario_ficha FOREIGN KEY (ficha_id)
        REFERENCES fichas(id) ON DELETE SET NULL,
    CONSTRAINT fk_usuario_acudiente FOREIGN KEY (acudiente_id)
        REFERENCES acudientes(id) ON DELETE SET NULL,
    UNIQUE KEY uq_identificacion (identificacion),
    UNIQUE KEY uq_portafolio_url (portafolio_url),
    INDEX idx_usuario_ficha (ficha_id),
    INDEX idx_usuario_nombre (nombres, apellidos),
    INDEX idx_usuario_acudiente (acudiente_id)
) ENGINE=InnoDB;

-- Tabla: admin (multi-administrador)
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    rol ENUM('superadmin','admin','instructor') DEFAULT 'instructor',
    programa_id INT DEFAULT NULL,
    activo TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_admin_programa FOREIGN KEY (programa_id) REFERENCES programas(id) ON DELETE SET NULL,
    INDEX idx_admin_programa (programa_id)
) ENGINE=InnoDB;

-- Tabla: plantillas
CREATE TABLE IF NOT EXISTS plantillas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    archivo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    programa_id INT,
    tipo_generacion ENUM('individual','grupal','ambos') DEFAULT 'ambos',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_plantilla_programa FOREIGN KEY (programa_id)
        REFERENCES programas(id) ON DELETE CASCADE,
    INDEX idx_plantilla_programa (programa_id)
) ENGINE=InnoDB;

-- Tabla: log_actividades (auditoria)
CREATE TABLE IF NOT EXISTS log_actividades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT,
    admin_username VARCHAR(50),
    accion VARCHAR(20) NOT NULL,
    entidad VARCHAR(50) NOT NULL,
    entidad_id INT,
    detalle TEXT,
    ip VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_log_fecha (created_at),
    INDEX idx_log_admin (admin_id)
) ENGINE=InnoDB;

-- ============================================
-- Datos de ejemplo
-- Contraseña: admin123 (hash generado con werkzeug.security.generate_password_hash)
-- Para regenerar: python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('admin123'))"
-- ============================================
INSERT INTO admin (username, password_hash, nombre, rol) VALUES
('admin', 'scrypt:32768:8:1$BZQi9hv67r9m4Ud8$df8da3a23ed32636d5c74be18429b75971dd96185d546a73ec223c33a2502f695b69d1be0821f237dbf144b2b3d03f7f79d9936d9a08b21f5443e7b77ef0dfa7',
 'Administrador General', 'superadmin')
ON DUPLICATE KEY UPDATE username = username;

INSERT INTO programas (codigo, nombre, descripcion, duracion_meses) VALUES
('ADSI-228106', 'Analisis y Desarrollo de Software', 'Desarrollo de software', 24),
('CONTA-123', 'Contabilidad y Finanzas', 'Tecnico en contabilidad', 18)
ON DUPLICATE KEY UPDATE codigo = codigo;

INSERT INTO fichas (numero, programa_id, jornada, fecha_inicio, fecha_fin) VALUES
('2558101', 1, 'Manana', '2025-01-20', '2027-01-20'),
('2558102', 2, 'Tarde', '2025-02-01', '2026-08-01')
ON DUPLICATE KEY UPDATE numero = numero;

INSERT INTO usuarios (identificacion, tipo_documento, nombres, apellidos, correo, telefono, direccion, ficha_id, estado) VALUES
('1001001001', 'CC', 'Laura', 'Gomez Ruiz', 'laura@example.com', '3001112233', 'Calle 1 # 2-3', 1, 'Activo'),
('1002002002', 'TI', 'Carlos', 'Perez Diaz', 'carlos@example.com', '3014445566', 'Carrera 5 # 6-7', 1, 'Activo'),
('1003003003', 'CC', 'Maria', 'Lopez Sanchez', 'maria@example.com', '3027778899', 'Av. 10 # 11-12', 2, 'Activo')
ON DUPLICATE KEY UPDATE identificacion = identificacion;
