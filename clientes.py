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

    # Función para guardar un cliente
    def guardar_cliente(e):
        nombre = nombre_input.value
        apellido = apellido_input.value
        email = email_input.value
        telefono = telefono_input.value
        direccion = direccion_input.value

        if nombre and apellido and email:
            try:
                cursor.execute(
                    "INSERT INTO clientes (nombre, apellido, email, telefono, direccion) VALUES (%s, %s, %s, %s, %s)",
                    (nombre, apellido, email, telefono, direccion)
                )
                conn.commit()
                mostrar_mensaje("Cliente agregado exitosamente!", "success")
                limpiar_campos()
                cargar_clientes()
            except Exception as ex:
                mostrar_mensaje(f"Error: {ex}", "error")
        else:
            mostrar_mensaje("Por favor, completa los campos obligatorios.", "error")

    # Función para editar un cliente
    def editar_cliente(cliente_id):
        nombre = nombre_input.value
        apellido = apellido_input.value
        email = email_input.value
        telefono = telefono_input.value
        direccion = direccion_input.value

        if nombre and apellido and email:
            try:
                cursor.execute(
                    "UPDATE clientes SET nombre = %s, apellido = %s, email = %s, telefono = %s, direccion = %s WHERE id_cliente = %s",
                    (nombre, apellido, email, telefono, direccion, cliente_id)
                )
                conn.commit()
                mostrar_mensaje("Cliente actualizado exitosamente!", "success")
                limpiar_campos()
                cargar_clientes()
            except Exception as ex:
                mostrar_mensaje(f"Error: {ex}", "error")
        else:
            mostrar_mensaje("Por favor, completa los campos obligatorios.", "error")

    # Función para eliminar un cliente
    def eliminar_cliente(cliente_id):
        try:
            cursor.execute("SELECT COUNT(*) FROM ventas WHERE id_cliente = %s", (cliente_id,))
            ventas = cursor.fetchone()[0]
            if ventas > 0:
                mostrar_mensaje("No se puede eliminar el cliente porque tiene ventas asociadas.", "error")
            else:
                cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (cliente_id,))
                conn.commit()
                mostrar_mensaje("Cliente eliminado exitosamente!", "success")
                cargar_clientes()
        except Exception as ex:
            mostrar_mensaje(f"Error: {ex}", "error")

    # Función para cargar clientes
    def cargar_clientes():
        clientes_container.controls.clear()
        cursor.execute("SELECT id_cliente, nombre, apellido, email FROM clientes")
        clientes = cursor.fetchall()
        for cliente in clientes:
            clientes_container.controls.append(
                ft.Row(
                    [
                        ft.Text(f"{cliente[1]} {cliente[2]} - {cliente[3]}", expand=True, color="black"),
                        ft.ElevatedButton("Editar", on_click=lambda e, id=cliente[0]: cargar_datos_para_editar(id), bgcolor="blue", color="black"),
                        ft.ElevatedButton("Eliminar", on_click=lambda e, id=cliente[0]: eliminar_cliente(id), bgcolor="red", color="black"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )
        page.update()

    # Función para cargar datos en los campos para editar
    def cargar_datos_para_editar(cliente_id):
        cursor.execute("SELECT nombre, apellido, email, telefono, direccion FROM clientes WHERE id_cliente = %s", (cliente_id,))
        cliente = cursor.fetchone()
        if cliente:
            nombre_input.value = cliente[0]
            apellido_input.value = cliente[1]
            email_input.value = cliente[2]
            telefono_input.value = cliente[3]
            direccion_input.value = cliente[4]
            editar_button.on_click = lambda e: editar_cliente(cliente_id)
            page.update()

    # Función para limpiar los campos del formulario
    def limpiar_campos():
        nombre_input.value = ""
        apellido_input.value = ""
        email_input.value = ""
        telefono_input.value = ""
        direccion_input.value = ""
        editar_button.on_click = None
        page.update()

    # Función para mostrar mensajes
    def mostrar_mensaje(mensaje, tipo):
        color = "green" if tipo == "success" else "red"
        page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="black"), bgcolor=color, open=True)
        page.update()

    # Configuración de la página
    page.title = "Gestión de Clientes"
    page.bgcolor = "#F5F5F5"

    # Controles de entrada
    nombre_input = ft.TextField(label="Nombre", width=300, color="black")
    apellido_input = ft.TextField(label="Apellido", width=300, color="black")
    email_input = ft.TextField(label="Email", width=300, color="black")
    telefono_input = ft.TextField(label="Teléfono", width=300, hint_text="Opcional", color="black")
    direccion_input = ft.TextField(label="Dirección", width=300, hint_text="Opcional", color="black")

    # Botones
    guardar_button = ft.ElevatedButton("Guardar Cliente", on_click=guardar_cliente, bgcolor="green", color="black")
    editar_button = ft.ElevatedButton("Editar Cliente", bgcolor="blue", color="black")

    # Contenedor para clientes
    clientes_container = ft.Column(scroll="adaptive")

    # Layout principal
    page.add(
        ft.Column(
            [
                ft.Text("Gestión de Clientes", size=30, weight="bold", color="black"),
                ft.Divider(),
                ft.Column(
                    [
                        nombre_input,
                        apellido_input,
                        email_input,
                        telefono_input,
                        direccion_input,
                        ft.Row([guardar_button, editar_button], alignment=ft.MainAxisAlignment.CENTER),
                    ],
                    spacing=10,
                ),
                ft.Divider(),
                ft.Text("Clientes Registrados:", size=20, weight="bold", color="black"),
                clientes_container,
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )
    )

    # Cargar clientes al iniciar
    cargar_clientes()

    # Cerrar conexión al salir
    page.on_close = lambda e: conn.close()

ft.app(target=main)