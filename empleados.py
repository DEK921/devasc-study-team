import flet as ft
import mysql.connector

def main(page: ft.Page):
    # Conexión a la base de datos MySQL
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="k921k76",
        database="zapateria"
    )
    cursor = conn.cursor()

    # Función para registrar un empleado
    def registrar_empleado(e):
        nombre = nombre_input.value
        apellido = apellido_input.value
        cargo = cargo_input.value
        telefono = telefono_input.value
        email = email_input.value
        salario = salario_input.value

        if nombre and apellido and salario:
            try:
                cursor.execute(
                    "INSERT INTO empleados (nombre, apellido, cargo, telefono, email, salario) VALUES (%s, %s, %s, %s, %s, %s)",
                    (nombre, apellido, cargo, telefono, email, salario)
                )
                conn.commit()
                mostrar_mensaje("Empleado registrado exitosamente!", "success")
                limpiar_campos()
                cargar_empleados()
            except Exception as ex:
                mostrar_mensaje(f"Error: {ex}", "error")
        else:
            mostrar_mensaje("Por favor, completa los campos obligatorios.", "error")

    # Función para actualizar un empleado
    def actualizar_empleado(empleado_id):
        nombre = nombre_input.value
        apellido = apellido_input.value
        cargo = cargo_input.value
        telefono = telefono_input.value
        email = email_input.value
        salario = salario_input.value

        if nombre and apellido and salario:
            try:
                cursor.execute(
                    "UPDATE empleados SET nombre = %s, apellido = %s, cargo = %s, telefono = %s, email = %s, salario = %s WHERE id_empleado = %s",
                    (nombre, apellido, cargo, telefono, email, salario, empleado_id)
                )
                conn.commit()
                mostrar_mensaje("Empleado actualizado exitosamente!", "success")
                limpiar_campos()
                cargar_empleados()
            except Exception as ex:
                mostrar_mensaje(f"Error: {ex}", "error")
        else:
            mostrar_mensaje("Por favor, completa los campos obligatorios.", "error")

    # Función para eliminar un empleado
    def eliminar_empleado(empleado_id):
        try:
            cursor.execute("DELETE FROM empleados WHERE id_empleado = %s", (empleado_id,))
            conn.commit()
            mostrar_mensaje("Empleado eliminado exitosamente!", "success")
            cargar_empleados()
        except Exception as ex:
            mostrar_mensaje(f"Error: {ex}", "error")

    # Función para cargar empleados
    def cargar_empleados():
        empleados_container.controls.clear()
        cursor.execute("SELECT id_empleado, nombre, apellido, cargo, salario FROM empleados")
        empleados = cursor.fetchall()
        for empleado in empleados:
            empleados_container.controls.append(
                ft.Row(
                    [
                        ft.Text(f"{empleado[1]} {empleado[2]} - {empleado[3]} - ${empleado[4]:,.2f}", expand=True, color="black"),
                        ft.ElevatedButton("Editar", on_click=lambda e, id=empleado[0]: cargar_datos_para_editar(id), bgcolor="blue", color="black"),
                        ft.ElevatedButton("Eliminar", on_click=lambda e, id=empleado[0]: eliminar_empleado(id), bgcolor="red", color="black"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )
        page.update()

    # Función para cargar datos en los campos para editar
    def cargar_datos_para_editar(empleado_id):
        cursor.execute("SELECT nombre, apellido, cargo, telefono, email, salario FROM empleados WHERE id_empleado = %s", (empleado_id,))
        empleado = cursor.fetchone()
        if empleado:
            nombre_input.value = empleado[0]
            apellido_input.value = empleado[1]
            cargo_input.value = empleado[2]
            telefono_input.value = empleado[3]
            email_input.value = empleado[4]
            salario_input.value = empleado[5]
            registrar_button.text = "Actualizar Empleado"
            registrar_button.on_click = lambda e: actualizar_empleado(empleado_id)
            page.update()

    # Función para limpiar los campos del formulario
    def limpiar_campos():
        nombre_input.value = ""
        apellido_input.value = ""
        cargo_input.value = ""
        telefono_input.value = ""
        email_input.value = ""
        salario_input.value = ""
        registrar_button.text = "Registrar Empleado"
        registrar_button.on_click = registrar_empleado
        page.update()

    # Función para mostrar mensajes
    def mostrar_mensaje(mensaje, tipo):
        color = "green" if tipo == "success" else "red"
        page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="black"), bgcolor=color, open=True)
        page.update()

    # Configuración de la página
    page.title = "Gestión de Empleados"
    page.bgcolor = "#F5F5F5"

    # Controles de entrada
    nombre_input = ft.TextField(label="Nombre", width=300, color="black")
    apellido_input = ft.TextField(label="Apellido", width=300, color="black")
    cargo_input = ft.TextField(label="Cargo", width=300, hint_text="Opcional", color="black")
    telefono_input = ft.TextField(label="Teléfono", width=300, hint_text="Opcional", color="black")
    email_input = ft.TextField(label="Email", width=300, hint_text="Opcional", color="black")
    salario_input = ft.TextField(label="Salario", width=300, color="black")

    # Botones
    registrar_button = ft.ElevatedButton("Registrar Empleado", on_click=registrar_empleado, bgcolor="green", color="black")

    # Contenedor para empleados
    empleados_container = ft.Column(scroll="adaptive")

    # Layout principal
    page.add(
        ft.Column(
            [
                ft.Text("Gestión de Empleados", size=30, weight="bold", color="black"),
                ft.Divider(),
                ft.Column(
                    [
                        nombre_input,
                        apellido_input,
                        cargo_input,
                        telefono_input,
                        email_input,
                        salario_input,
                        ft.Row([registrar_button], alignment=ft.MainAxisAlignment.CENTER),
                    ],
                    spacing=10,
                ),
                ft.Divider(),
                ft.Text("Empleados Registrados:", size=20, weight="bold", color="black"),
                empleados_container,
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )
    )

    # Cargar empleados al iniciar
    cargar_empleados()

    # Cerrar conexión al salir
    page.on_close = lambda e: conn.close()

ft.app(target=main)