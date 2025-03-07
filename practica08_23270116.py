import mysql.connector

def conectar_bd():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="k921k76",
        database="dbtaller"
    )

def insertar_linea():
    clave = input("Ingrese clave: ")
    nombre = input("Ingrese nombre: ")
    conexion = conectar_bd()
    cursor = conexion.cursor()
    sql = "INSERT INTO lineainv (clavein, nombre) VALUES (%s, %s)"
    cursor.execute(sql, (clave, nombre))
    conexion.commit()h  
    print("Línea de investigación insertada con éxito.")
    cursor.close()
    conexion.close()

def leer_lineas():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM lineainv")
    for (clavein, nombre) in cursor:
        print(f"Clave: {clavein}, Nombre: {nombre}")
    cursor.close()
    conexion.close()

def actualizar_linea():
    clave = input("Ingrese clave de la línea a actualizar: ")
    nombre = input("Ingrese nuevo nombre: ")
    conexion = conectar_bd()
    cursor = conexion.cursor()
    sql = "UPDATE lineainv SET nombre = %s WHERE clavein = %s"
    cursor.execute(sql, (nombre, clave))
    conexion.commit()
    print("Línea de investigación actualizada con éxito.")
    cursor.close()
    conexion.close()

def eliminar_linea():
    clave = input("Ingrese clave de la línea a eliminar: ")
    conexion = conectar_bd()
    cursor = conexion.cursor()
    sql = "DELETE FROM lineainv WHERE clavein = %s"
    cursor.execute(sql, (clave,))
    conexion.commit()
    print("Línea de investigación eliminada con éxito.")
    cursor.close()
    conexion.close()

def menu():
    while True:
        print("\n1. Insertar línea de investigación")
        print("2. Leer líneas de investigación")
        print("3. Actualizar línea de investigación")
        print("4. Eliminar línea de investigación")
        print("5. Salir")
        opcion = input("Seleccione una opción: ")
        
        if opcion == "1":
            insertar_linea()
        elif opcion == "2":
            leer_lineas()
        elif opcion == "3":
            actualizar_linea()
        elif opcion == "4":
            eliminar_linea()
        elif opcion == "5":
            print("Saliendo...")
            break
        else:
            print("Opción no válida")

if __name__ == "__main__":
    menu()