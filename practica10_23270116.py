import mysql.connector

def conectar_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",  
        password="k921k76",
        database="dbtaller"
    )

def crear_profesor(nombre):
    conn = conectar_db()
    cursor = conn.cursor()
    sql = "INSERT INTO profesor (nombreProf) VALUES (%s)"
    cursor.execute(sql, (nombre,))
    conn.commit()
    conn.close()
    print("Profesor creado exitosamente.")

def leer_profesores():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profesor")
    resultados = cursor.fetchall()
    conn.close()
    for profesor in resultados:
        print(profesor)

def actualizar_profesor(idprofesor, nuevo_nombre):
    conn = conectar_db()
    cursor = conn.cursor()
    sql = "UPDATE profesor SET nombreProf = %s WHERE idprofesor = %s"
    cursor.execute(sql, (nuevo_nombre, idprofesor))
    conn.commit()
    conn.close()
    print("Profesor actualizado correctamente.")

def eliminar_profesor(idprofesor):
    conn = conectar_db()
    cursor = conn.cursor()
    sql = "DELETE FROM profesor WHERE idprofesor = %s"
    cursor.execute(sql, (idprofesor,))
    conn.commit()
    conn.close()
    print("Profesor eliminado correctamente.")

# Ejemplo de uso
if __name__ == "__main__":
    while True:
        print("\nGestión de Profesores")
        print("1. Crear Profesor")
        print("2. Leer Profesores")
        print("3. Actualizar Profesor")
        print("4. Eliminar Profesor")
        print("5. Salir")
        opcion = input("Seleccione una opción: ")
        
        if opcion == "1":
            nombre = input("Ingrese el nombre del profesor: ")
            crear_profesor(nombre)
        elif opcion == "2":
            leer_profesores()
        elif opcion == "3":
            idprofesor = input("Ingrese el ID del profesor a actualizar: ")
            nuevo_nombre = input("Ingrese el nuevo nombre: ")
            actualizar_profesor(idprofesor, nuevo_nombre)
        elif opcion == "4":
            idprofesor = input("Ingrese el ID del profesor a eliminar: ")
            eliminar_profesor(idprofesor)
        elif opcion == "5":
            break
        else:
            print("Opción no válida. Intente nuevamente.")
