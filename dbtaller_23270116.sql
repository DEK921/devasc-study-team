-- Eliminar la base de datos si existe y crearla nuevamente
DROP DATABASE IF EXISTS dbtaller;
CREATE DATABASE dbtaller;
USE dbtaller;

-- Crear tablas principales
CREATE TABLE lineainv (
    clavein CHAR(10) PRIMARY KEY,  
    nombre VARCHAR(250)           
);

CREATE TABLE profesor (
    idprofesor INT AUTO_INCREMENT PRIMARY KEY,  
    nombreProf VARCHAR(200)           
);

CREATE TABLE tipoproyecto (
    tipo CHAR(10) PRIMARY KEY, 
    nombre VARCHAR(150)        
);

CREATE TABLE proyecto (
    clave CHAR(10) PRIMARY KEY,  
    nombre VARCHAR(250),        
    clavein CHAR(10),            
    tipo CHAR(10),              
    CONSTRAINT corresponde FOREIGN KEY (clavein) REFERENCES lineainv(clavein),
    CONSTRAINT asignado FOREIGN KEY (tipo) REFERENCES tipoproyecto(tipo)
);

CREATE TABLE alumno (
    nocontrol CHAR(10) PRIMARY KEY,  
    nombre VARCHAR(150),             
    clave CHAR(10),                 
    CONSTRAINT elige FOREIGN KEY (clave) REFERENCES proyecto(clave)
);

CREATE TABLE profesorproy (
    idprofesor INT,                  
    clave CHAR(10),                 
    calificacion FLOAT,              
    rol VARCHAR(45),              
    CONSTRAINT asesora FOREIGN KEY (idprofesor) REFERENCES profesor(idprofesor),
    CONSTRAINT asigna FOREIGN KEY (clave) REFERENCES proyecto(clave)
);

-- Nueva tabla: Perfil
CREATE TABLE perfil (
    idperfil INT AUTO_INCREMENT PRIMARY KEY,  
    nombre VARCHAR(100) NOT NULL
);

-- Nueva tabla: Objetos
CREATE TABLE objetos (
    idobjeto INT AUTO_INCREMENT PRIMARY KEY,  
    nombre VARCHAR(100) NOT NULL
);

-- Nueva tabla: Objeto_Privilegios (relaciona perfil y objetos)
CREATE TABLE objeto_privilegios (
    idperfil INT,
    idobjeto INT,
    privilegio VARCHAR(100),
    PRIMARY KEY (idperfil, idobjeto),
    FOREIGN KEY (idperfil) REFERENCES perfil(idperfil) ON DELETE CASCADE,
    FOREIGN KEY (idobjeto) REFERENCES objetos(idobjeto) ON DELETE CASCADE
);

-- Crear usuarios y permisos
CREATE USER 'alumno'@'localhost' IDENTIFIED BY 'alumno123';
CREATE USER 'profesor'@'localhost' IDENTIFIED BY 'profesor123';
CREATE USER 'admin'@'localhost' IDENTIFIED BY 'admin123';

GRANT SELECT, INSERT ON dbtaller.alumno TO 'alumno'@'localhost';
GRANT SELECT ON dbtaller.proyecto TO 'alumno'@'localhost';

GRANT SELECT, INSERT ON dbtaller.profesor TO 'profesor'@'localhost';
GRANT SELECT, INSERT, UPDATE ON dbtaller.profesorproy TO 'profesor'@'localhost';

GRANT ALL PRIVILEGES ON dbtaller.* TO 'admin'@'localhost';

FLUSH PRIVILEGES;
