# coding: utf-8  # Add encoding for potential special characters
import flet as ft
import mysql.connector
from decimal import Decimal  # Import Decimal for handling database decimals correctly

def main(page: ft.Page):
    page.title = "Sistema de Gestión - Zapatería"
    page.bgcolor = ft.colors.GREY_200 # Use Flet's color constants
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "k921k76", # Consider using environment variables or a config file for security
        "database": "zapateria"
    }

    conn = None
    cursor = None

    # --- Database Connection ---
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("Database connected successfully.")
    except mysql.connector.Error as err:
        # Display error on the page if connection fails
        page.add(ft.Text(f"Error de conexión a la base de datos: {err}", color=ft.colors.RED))
        print(f"Database connection error: {err}")
        # Optional: Exit or disable functionality if connection fails
        # return # Or handle appropriately

    # --- Shared Utility Function ---
    def mostrar_mensaje(mensaje, tipo):
        """Displays a SnackBar message."""
        color = ft.colors.GREEN_600 if tipo == "success" else ft.colors.RED_600
        page.snack_bar = ft.SnackBar(
            ft.Text(mensaje, color=ft.colors.WHITE), # Ensure text is visible
            bgcolor=color,
            open=True
        )
        page.update()

    # --- Function to Create Clientes View ---
    def crear_vista_clientes():
        """Creates the UI Controls and logic for the Clientes tab."""
        nombre_input = ft.TextField(label="Nombre*", width=300, color=ft.colors.BLACK)
        apellido_input = ft.TextField(label="Apellido*", width=300, color=ft.colors.BLACK)
        email_input = ft.TextField(label="Email*", width=300, color=ft.colors.BLACK)
        telefono_input = ft.TextField(label="Teléfono", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        direccion_input = ft.TextField(label="Dirección", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        clientes_container = ft.Column(scroll="adaptive", expand=True, spacing=5)
        # Use a specific state variable to hold the ID for editing
        cliente_id_para_editar = ft.Ref[int]()

        def limpiar_campos_cliente():
            nombre_input.value = ""
            apellido_input.value = ""
            email_input.value = ""
            telefono_input.value = ""
            direccion_input.value = ""
            cliente_id_para_editar.current = None # Reset editing state
            guardar_button.visible = True
            actualizar_button.visible = False
            cancelar_edicion_button.visible = False
            page.update()

        def cargar_clientes():
            if not cursor: return # Don't run if DB connection failed
            clientes_container.controls.clear()
            try:
                cursor.execute("SELECT id_cliente, nombre, apellido, email FROM clientes ORDER BY apellido, nombre")
                clientes = cursor.fetchall()
                if not clientes:
                    clientes_container.controls.append(ft.Text("No hay clientes registrados.", color=ft.colors.GREY_700))
                else:
                    for cliente in clientes:
                        cliente_id = cliente[0] # Capture id for lambda
                        clientes_container.controls.append(
                            ft.Container( # Add some padding/margin
                                padding=ft.padding.symmetric(vertical=2),
                                content = ft.Row(
                                    [
                                        ft.Text(f"{cliente[1]} {cliente[2]} ({cliente[3]})", expand=True, color=ft.colors.BLACK),
                                        ft.IconButton(
                                            ft.icons.EDIT,
                                            tooltip="Editar Cliente",
                                            on_click=lambda e, id=cliente_id: cargar_datos_cliente_para_editar(id), # Pass id correctly
                                            icon_color=ft.colors.BLUE_700
                                        ),
                                        ft.IconButton(
                                             ft.icons.DELETE_FOREVER,
                                             tooltip="Eliminar Cliente",
                                            on_click=lambda e, id=cliente_id: eliminar_cliente(id), # Pass id correctly
                                            icon_color=ft.colors.RED_700
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            )
                        )
                page.update()
            except mysql.connector.Error as db_err:
                mostrar_mensaje(f"Error al cargar clientes: {db_err}", "error")
            except Exception as ex:
                 mostrar_mensaje(f"Error inesperado al cargar clientes: {ex}", "error")


        def cargar_datos_cliente_para_editar(cliente_id):
            if not cursor: return
            try:
                cursor.execute("SELECT nombre, apellido, email, telefono, direccion FROM clientes WHERE id_cliente = %s", (cliente_id,))
                cliente = cursor.fetchone()
                if cliente:
                    nombre_input.value = cliente[0]
                    apellido_input.value = cliente[1]
                    email_input.value = cliente[2]
                    telefono_input.value = cliente[3] if cliente[3] else ""
                    direccion_input.value = cliente[4] if cliente[4] else ""
                    cliente_id_para_editar.current = cliente_id # Store ID for update function
                    # Change button visibility
                    guardar_button.visible = False
                    actualizar_button.visible = True
                    cancelar_edicion_button.visible = True
                    page.update()
                else:
                    mostrar_mensaje("Cliente no encontrado.", "error")
            except mysql.connector.Error as db_err:
                mostrar_mensaje(f"Error al cargar datos del cliente: {db_err}", "error")
            except Exception as ex:
                 mostrar_mensaje(f"Error inesperado al cargar cliente para editar: {ex}", "error")

        def guardar_cliente(e):
            if not (nombre_input.value and apellido_input.value and email_input.value):
                mostrar_mensaje("Por favor, completa los campos obligatorios (*).", "error")
                return
            if not cursor: return

            try:
                cursor.execute(
                    "INSERT INTO clientes (nombre, apellido, email, telefono, direccion) VALUES (%s, %s, %s, %s, %s)",
                    (nombre_input.value.strip(),
                     apellido_input.value.strip(),
                     email_input.value.strip(),
                     telefono_input.value.strip() or None, # Handle empty optional fields
                     direccion_input.value.strip() or None)
                )
                conn.commit()
                mostrar_mensaje("Cliente agregado exitosamente!", "success")
                limpiar_campos_cliente()
                cargar_clientes()
            except mysql.connector.Error as db_err:
                conn.rollback() # Rollback on error
                mostrar_mensaje(f"Error al guardar cliente: {db_err}", "error")
                print(f"DB Error saving client: {db_err}")
            except Exception as ex:
                conn.rollback()
                mostrar_mensaje(f"Error inesperado: {ex}", "error")
                print(f"Unexpected Error saving client: {ex}")

        def actualizar_cliente_actual(e):
             # Calls the main update function with the stored ID
            if cliente_id_para_editar.current:
                editar_cliente(cliente_id_para_editar.current)
            else:
                 mostrar_mensaje("No se seleccionó ningún cliente para actualizar.", "error")


        def editar_cliente(cliente_id):
            if not (nombre_input.value and apellido_input.value and email_input.value):
                mostrar_mensaje("Por favor, completa los campos obligatorios (*).", "error")
                return
            if not cursor: return

            try:
                cursor.execute(
                    "UPDATE clientes SET nombre = %s, apellido = %s, email = %s, telefono = %s, direccion = %s WHERE id_cliente = %s",
                    (nombre_input.value.strip(),
                     apellido_input.value.strip(),
                     email_input.value.strip(),
                     telefono_input.value.strip() or None,
                     direccion_input.value.strip() or None,
                     cliente_id)
                )
                conn.commit()
                mostrar_mensaje("Cliente actualizado exitosamente!", "success")
                limpiar_campos_cliente()
                cargar_clientes()
            except mysql.connector.Error as db_err:
                conn.rollback()
                mostrar_mensaje(f"Error al actualizar cliente: {db_err}", "error")
                print(f"DB Error updating client: {db_err}")
            except Exception as ex:
                conn.rollback()
                mostrar_mensaje(f"Error inesperado al actualizar: {ex}", "error")
                print(f"Unexpected Error updating client: {ex}")

        def eliminar_cliente(cliente_id):
            if not cursor: return
            try:
                 # Check for related sales (ventas) - IMPORTANT
                cursor.execute("SELECT COUNT(*) FROM ventas WHERE id_cliente = %s", (cliente_id,))
                ventas_count = cursor.fetchone()[0]

                if ventas_count > 0:
                     mostrar_mensaje("No se puede eliminar el cliente, tiene ventas asociadas.", "error")
                     return # Prevent deletion

                 # If no sales, proceed with deletion
                cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (cliente_id,))
                conn.commit()
                mostrar_mensaje("Cliente eliminado exitosamente!", "success")
                limpiar_campos_cliente() # Clean form if the deleted user was being edited
                cargar_clientes()
            except mysql.connector.Error as db_err:
                conn.rollback()
                mostrar_mensaje(f"Error al eliminar cliente: {db_err}", "error")
                print(f"DB Error deleting client: {db_err}")
            except Exception as ex:
                 conn.rollback()
                 mostrar_mensaje(f"Error inesperado al eliminar: {ex}", "error")
                 print(f"Unexpected Error deleting client: {ex}")


        # Buttons
        guardar_button = ft.ElevatedButton(
            "Guardar Cliente",
            on_click=guardar_cliente,
            icon=ft.icons.SAVE,
            bgcolor=ft.colors.GREEN_700,
            color=ft.colors.WHITE,
            visible=True # Initially visible
        )
        actualizar_button = ft.ElevatedButton(
             "Actualizar Cliente",
             on_click=actualizar_cliente_actual, # Connects to the specific update function
             icon=ft.icons.UPDATE,
             bgcolor=ft.colors.BLUE_700,
             color=ft.colors.WHITE,
             visible=False # Initially hidden
        )
        cancelar_edicion_button = ft.ElevatedButton(
            "Cancelar Edición",
            on_click=lambda e: limpiar_campos_cliente(), # Reuse cleaner function
            icon=ft.icons.CANCEL,
            bgcolor=ft.colors.GREY_600,
            color=ft.colors.WHITE,
            visible=False # Initially hidden
         )

        # Initial data load
        cargar_clientes()

        # Layout for this tab
        return ft.Column(
            [
                ft.Text("Gestión de Clientes", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                ft.Divider(height=10, color=ft.colors.GREY_400),
                ft.Row( # Form layout
                    [
                       ft.Column( [nombre_input, apellido_input, email_input], spacing=10),
                       ft.Column( [telefono_input, direccion_input], spacing=10)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    vertical_alignment=ft.CrossAxisAlignment.START
                ),
                ft.Row( # Button layout
                    [guardar_button, actualizar_button, cancelar_edicion_button],
                    alignment=ft.MainAxisAlignment.CENTER, spacing=10
                 ),
                ft.Divider(height=10, color=ft.colors.GREY_400),
                ft.Text("Clientes Registrados:", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_700),
                clientes_container, # Container where clients are listed
            ],
            spacing=15,
            alignment=ft.MainAxisAlignment.START,
            expand=True # Allow the column to take available vertical space
        )

    # --- Function to Create Empleados View ---
    def crear_vista_empleados():
        """Creates the UI Controls and logic for the Empleados tab."""
        nombre_input = ft.TextField(label="Nombre*", width=300, color=ft.colors.BLACK)
        apellido_input = ft.TextField(label="Apellido*", width=300, color=ft.colors.BLACK)
        cargo_input = ft.TextField(label="Cargo", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        telefono_input = ft.TextField(label="Teléfono", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        email_input = ft.TextField(label="Email", width=300, hint_text="Opcional (único)", color=ft.colors.BLACK)
        salario_input = ft.TextField(label="Salario*", width=300, color=ft.colors.BLACK, input_filter=ft.InputFilter(r'[0-9\.]'))
        empleados_container = ft.Column(scroll="adaptive", expand=True, spacing=5)
        empleado_id_para_editar = ft.Ref[int]()

        def limpiar_campos_empleado():
            nombre_input.value = ""
            apellido_input.value = ""
            cargo_input.value = ""
            telefono_input.value = ""
            email_input.value = ""
            salario_input.value = ""
            empleado_id_para_editar.current = None
            registrar_button.visible = True
            actualizar_button.visible = False
            cancelar_edicion_button.visible = False
            page.update()

        def cargar_empleados():
            if not cursor: return
            empleados_container.controls.clear()
            try:
                cursor.execute("SELECT id_empleado, nombre, apellido, cargo, salario FROM empleados ORDER BY apellido, nombre")
                empleados = cursor.fetchall()
                if not empleados:
                    empleados_container.controls.append(ft.Text("No hay empleados registrados.", color=ft.colors.GREY_700))
                else:
                    for emp in empleados:
                        emp_id = emp[0]
                        salario_formatted = f"${emp[4]:,.2f}" if isinstance(emp[4], (int, float, Decimal)) else "N/A"
                        empleados_container.controls.append(
                             ft.Container(
                                padding=ft.padding.symmetric(vertical=2),
                                content = ft.Row(
                                    [
                                        ft.Text(f"{emp[1]} {emp[2]} - {emp[3]} ({salario_formatted})", expand=True, color=ft.colors.BLACK),
                                         ft.IconButton(
                                            ft.icons.EDIT,
                                            tooltip="Editar Empleado",
                                            on_click=lambda e, id=emp_id: cargar_datos_empleado_para_editar(id),
                                            icon_color=ft.colors.BLUE_700
                                        ),
                                        ft.IconButton(
                                            ft.icons.DELETE_FOREVER,
                                            tooltip="Eliminar Empleado",
                                            on_click=lambda e, id=emp_id: eliminar_empleado(id),
                                            icon_color=ft.colors.RED_700
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                     vertical_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            )
                        )
                page.update()
            except mysql.connector.Error as db_err:
                 mostrar_mensaje(f"Error al cargar empleados: {db_err}", "error")
            except Exception as ex:
                 mostrar_mensaje(f"Error inesperado al cargar empleados: {ex}", "error")


        def cargar_datos_empleado_para_editar(empleado_id):
            if not cursor: return
            try:
                cursor.execute("SELECT nombre, apellido, cargo, telefono, email, salario FROM empleados WHERE id_empleado = %s", (empleado_id,))
                empleado = cursor.fetchone()
                if empleado:
                    nombre_input.value = empleado[0]
                    apellido_input.value = empleado[1]
                    cargo_input.value = empleado[2] if empleado[2] else ""
                    telefono_input.value = empleado[3] if empleado[3] else ""
                    email_input.value = empleado[4] if empleado[4] else ""
                    salario_input.value = str(empleado[5]) if empleado[5] is not None else "" # Convert decimal to string
                    empleado_id_para_editar.current = empleado_id
                    registrar_button.visible = False
                    actualizar_button.visible = True
                    cancelar_edicion_button.visible = True
                    page.update()
                else:
                    mostrar_mensaje("Empleado no encontrado.", "error")
            except mysql.connector.Error as db_err:
                 mostrar_mensaje(f"Error al cargar datos del empleado: {db_err}", "error")
            except Exception as ex:
                 mostrar_mensaje(f"Error inesperado al cargar empleado para editar: {ex}", "error")


        def registrar_empleado(e):
            if not (nombre_input.value and apellido_input.value and salario_input.value):
                mostrar_mensaje("Por favor, completa Nombre, Apellido y Salario (*).", "error")
                return
            if not cursor: return

            try:
                salario = Decimal(salario_input.value) # Convert to Decimal
            except Exception:
                 mostrar_mensaje("Salario inválido. Debe ser un número.", "error")
                 return

            try:
                cursor.execute(
                    "INSERT INTO empleados (nombre, apellido, cargo, telefono, email, salario) VALUES (%s, %s, %s, %s, %s, %s)",
                    (nombre_input.value.strip(),
                     apellido_input.value.strip(),
                     cargo_input.value.strip() or None,
                     telefono_input.value.strip() or None,
                     email_input.value.strip() or None,
                     salario)
                )
                conn.commit()
                mostrar_mensaje("Empleado registrado exitosamente!", "success")
                limpiar_campos_empleado()
                cargar_empleados()
            except mysql.connector.Error as db_err:
                conn.rollback()
                mostrar_mensaje(f"Error al registrar empleado: {db_err}", "error")
                print(f"DB Error registering employee: {db_err}")
            except Exception as ex:
                conn.rollback()
                mostrar_mensaje(f"Error inesperado al registrar: {ex}", "error")
                print(f"Unexpected Error registering employee: {ex}")


        def actualizar_empleado_actual(e):
             if empleado_id_para_editar.current:
                actualizar_empleado(empleado_id_para_editar.current)
             else:
                 mostrar_mensaje("No se seleccionó ningún empleado para actualizar.", "error")

        def actualizar_empleado(empleado_id):
            if not (nombre_input.value and apellido_input.value and salario_input.value):
                mostrar_mensaje("Por favor, completa Nombre, Apellido y Salario (*).", "error")
                return
            if not cursor: return

            try:
                salario = Decimal(salario_input.value) # Convert to Decimal
            except Exception:
                 mostrar_mensaje("Salario inválido. Debe ser un número.", "error")
                 return

            try:
                cursor.execute(
                    "UPDATE empleados SET nombre = %s, apellido = %s, cargo = %s, telefono = %s, email = %s, salario = %s WHERE id_empleado = %s",
                    (nombre_input.value.strip(),
                     apellido_input.value.strip(),
                     cargo_input.value.strip() or None,
                     telefono_input.value.strip() or None,
                     email_input.value.strip() or None,
                     salario,
                     empleado_id)
                )
                conn.commit()
                mostrar_mensaje("Empleado actualizado exitosamente!", "success")
                limpiar_campos_empleado()
                cargar_empleados()
            except mysql.connector.Error as db_err:
                 conn.rollback()
                 mostrar_mensaje(f"Error al actualizar empleado: {db_err}", "error")
                 print(f"DB Error updating employee: {db_err}")
            except Exception as ex:
                 conn.rollback()
                 mostrar_mensaje(f"Error inesperado al actualizar: {ex}", "error")
                 print(f"Unexpected Error updating employee: {ex}")

        def eliminar_empleado(empleado_id):
            if not cursor: return
            try:
                # Check for related sales (ventas) - IMPORTANT
                cursor.execute("SELECT COUNT(*) FROM ventas WHERE id_empleado = %s", (empleado_id,))
                ventas_count = cursor.fetchone()[0]

                if ventas_count > 0:
                     mostrar_mensaje("No se puede eliminar el empleado, tiene ventas asociadas.", "error")
                     return # Prevent deletion

                cursor.execute("DELETE FROM empleados WHERE id_empleado = %s", (empleado_id,))
                conn.commit()
                mostrar_mensaje("Empleado eliminado exitosamente!", "success")
                limpiar_campos_empleado()
                cargar_empleados()
            except mysql.connector.Error as db_err:
                conn.rollback()
                mostrar_mensaje(f"Error al eliminar empleado: {db_err}", "error")
                print(f"DB Error deleting employee: {db_err}")
            except Exception as ex:
                conn.rollback()
                mostrar_mensaje(f"Error inesperado al eliminar: {ex}", "error")
                print(f"Unexpected Error deleting employee: {ex}")


        # Buttons
        registrar_button = ft.ElevatedButton(
             "Registrar Empleado",
             on_click=registrar_empleado,
             icon=ft.icons.PERSON_ADD,
             bgcolor=ft.colors.GREEN_700,
             color=ft.colors.WHITE,
             visible=True
        )
        actualizar_button = ft.ElevatedButton(
            "Actualizar Empleado",
            on_click=actualizar_empleado_actual,
            icon=ft.icons.UPDATE,
            bgcolor=ft.colors.BLUE_700,
            color=ft.colors.WHITE,
            visible=False
        )
        cancelar_edicion_button = ft.ElevatedButton(
            "Cancelar Edición",
            on_click=lambda e: limpiar_campos_empleado(),
            icon=ft.icons.CANCEL,
            bgcolor=ft.colors.GREY_600,
            color=ft.colors.WHITE,
            visible=False
         )

        # Initial data load
        cargar_empleados()

        # Layout
        return ft.Column(
            [
                ft.Text("Gestión de Empleados", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                ft.Divider(height=10, color=ft.colors.GREY_400),
                 ft.Row( # Form layout
                     [
                         ft.Column([nombre_input, apellido_input, cargo_input], spacing=10),
                         ft.Column([telefono_input, email_input, salario_input], spacing=10),
                     ],
                     alignment=ft.MainAxisAlignment.SPACE_AROUND,
                     vertical_alignment=ft.CrossAxisAlignment.START
                 ),
                ft.Row( # Buttons
                    [registrar_button, actualizar_button, cancelar_edicion_button],
                    alignment=ft.MainAxisAlignment.CENTER, spacing=10
                ),
                ft.Divider(height=10, color=ft.colors.GREY_400),
                ft.Text("Empleados Registrados:", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_700),
                empleados_container,
            ],
            spacing=15,
            alignment=ft.MainAxisAlignment.START,
            expand=True
        )


    # --- Function to Create Proveedores View ---
    def crear_vista_proveedores():
        """Creates the UI Controls and logic for the Proveedores tab."""
        nombre_empresa_input = ft.TextField(label="Nombre de la Empresa*", width=300, color=ft.colors.BLACK)
        contacto_input = ft.TextField(label="Contacto", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        telefono_input = ft.TextField(label="Teléfono", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        email_input = ft.TextField(label="Email", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        direccion_input = ft.TextField(label="Dirección", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        proveedores_container = ft.Column(scroll="adaptive", expand=True, spacing=5)
        proveedor_id_para_editar = ft.Ref[int]()


        def limpiar_campos_proveedor():
            nombre_empresa_input.value = ""
            contacto_input.value = ""
            telefono_input.value = ""
            email_input.value = ""
            direccion_input.value = ""
            proveedor_id_para_editar.current = None
            registrar_button.visible = True
            actualizar_button.visible = False
            cancelar_edicion_button.visible = False
            page.update()


        def cargar_proveedores():
            if not cursor: return
            proveedores_container.controls.clear()
            try:
                cursor.execute("SELECT id_proveedor, nombre_empresa, contacto, telefono FROM proveedores ORDER BY nombre_empresa")
                proveedores = cursor.fetchall()
                if not proveedores:
                    proveedores_container.controls.append(ft.Text("No hay proveedores registrados.", color=ft.colors.GREY_700))
                else:
                    for prov in proveedores:
                        prov_id = prov[0]
                        proveedores_container.controls.append(
                            ft.Container(
                                padding=ft.padding.symmetric(vertical=2),
                                content = ft.Row(
                                    [
                                        ft.Text(f"{prov[1]} (Contacto: {prov[2] or 'N/A'}, Tel: {prov[3] or 'N/A'})", expand=True, color=ft.colors.BLACK),
                                        ft.IconButton(
                                            ft.icons.EDIT,
                                            tooltip="Editar Proveedor",
                                            on_click=lambda e, id=prov_id: cargar_datos_proveedor_para_editar(id),
                                            icon_color=ft.colors.BLUE_700
                                        ),
                                        ft.IconButton(
                                            ft.icons.DELETE_FOREVER,
                                            tooltip="Eliminar Proveedor",
                                            on_click=lambda e, id=prov_id: eliminar_proveedor(id),
                                            icon_color=ft.colors.RED_700
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                     vertical_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            )
                        )
                page.update()
            except mysql.connector.Error as db_err:
                 mostrar_mensaje(f"Error al cargar proveedores: {db_err}", "error")
            except Exception as ex:
                 mostrar_mensaje(f"Error inesperado al cargar proveedores: {ex}", "error")


        def cargar_datos_proveedor_para_editar(proveedor_id):
             if not cursor: return
             try:
                 cursor.execute("SELECT nombre_empresa, contacto, telefono, email, direccion FROM proveedores WHERE id_proveedor = %s", (proveedor_id,))
                 proveedor = cursor.fetchone()
                 if proveedor:
                     nombre_empresa_input.value = proveedor[0]
                     contacto_input.value = proveedor[1] if proveedor[1] else ""
                     telefono_input.value = proveedor[2] if proveedor[2] else ""
                     email_input.value = proveedor[3] if proveedor[3] else ""
                     direccion_input.value = proveedor[4] if proveedor[4] else ""
                     proveedor_id_para_editar.current = proveedor_id
                     registrar_button.visible = False
                     actualizar_button.visible = True
                     cancelar_edicion_button.visible = True
                     page.update()
                 else:
                     mostrar_mensaje("Proveedor no encontrado.", "error")
             except mysql.connector.Error as db_err:
                 mostrar_mensaje(f"Error al cargar datos del proveedor: {db_err}", "error")
             except Exception as ex:
                 mostrar_mensaje(f"Error inesperado al cargar proveedor para editar: {ex}", "error")

        def registrar_proveedor(e):
            if not nombre_empresa_input.value:
                 mostrar_mensaje("El Nombre de la Empresa es obligatorio (*).", "error")
                 return
            if not cursor: return

            try:
                 cursor.execute(
                     "INSERT INTO proveedores (nombre_empresa, contacto, telefono, email, direccion) VALUES (%s, %s, %s, %s, %s)",
                     (nombre_empresa_input.value.strip(),
                      contacto_input.value.strip() or None,
                      telefono_input.value.strip() or None,
                      email_input.value.strip() or None,
                      direccion_input.value.strip() or None)
                 )
                 conn.commit()
                 mostrar_mensaje("Proveedor registrado exitosamente!", "success")
                 limpiar_campos_proveedor()
                 cargar_proveedores()
            except mysql.connector.Error as db_err:
                 conn.rollback()
                 mostrar_mensaje(f"Error al registrar proveedor: {db_err}", "error")
                 print(f"DB Error registering supplier: {db_err}")
            except Exception as ex:
                 conn.rollback()
                 mostrar_mensaje(f"Error inesperado al registrar: {ex}", "error")
                 print(f"Unexpected Error registering supplier: {ex}")

        def actualizar_proveedor_actual(e):
              if proveedor_id_para_editar.current:
                 actualizar_proveedor(proveedor_id_para_editar.current)
              else:
                 mostrar_mensaje("No se seleccionó ningún proveedor para actualizar.", "error")


        def actualizar_proveedor(proveedor_id):
             if not nombre_empresa_input.value:
                 mostrar_mensaje("El Nombre de la Empresa es obligatorio (*).", "error")
                 return
             if not cursor: return

             try:
                 cursor.execute(
                     "UPDATE proveedores SET nombre_empresa = %s, contacto = %s, telefono = %s, email = %s, direccion = %s WHERE id_proveedor = %s",
                     (nombre_empresa_input.value.strip(),
                      contacto_input.value.strip() or None,
                      telefono_input.value.strip() or None,
                      email_input.value.strip() or None,
                      direccion_input.value.strip() or None,
                      proveedor_id)
                 )
                 conn.commit()
                 mostrar_mensaje("Proveedor actualizado exitosamente!", "success")
                 limpiar_campos_proveedor()
                 cargar_proveedores()
             except mysql.connector.Error as db_err:
                 conn.rollback()
                 mostrar_mensaje(f"Error al actualizar proveedor: {db_err}", "error")
                 print(f"DB Error updating supplier: {db_err}")
             except Exception as ex:
                 conn.rollback()
                 mostrar_mensaje(f"Error inesperado al actualizar: {ex}", "error")
                 print(f"Unexpected Error updating supplier: {ex}")


        def eliminar_proveedor(proveedor_id):
            if not cursor: return
            try:
                # Check for related products - IMPORTANT
                cursor.execute("SELECT COUNT(*) FROM productos WHERE id_proveedor = %s", (proveedor_id,))
                productos_count = cursor.fetchone()[0]

                if productos_count > 0:
                    # Option 1: Prevent deletion
                    # mostrar_mensaje("No se puede eliminar, tiene productos asociados. Cambie los productos a otro proveedor o elimínelos primero.", "error")
                    # return

                    # Option 2: Warn and set products' id_proveedor to NULL (as defined in schema ON DELETE SET NULL)
                    print(f"Proveedor {proveedor_id} tiene {productos_count} productos asociados. Se establecerá su id_proveedor a NULL.")
                    # The ON DELETE SET NULL in the FOREIGN KEY definition handles this automatically when deleting the proveedor

                cursor.execute("DELETE FROM proveedores WHERE id_proveedor = %s", (proveedor_id,))
                conn.commit()
                mostrar_mensaje("Proveedor eliminado exitosamente!", "success")
                limpiar_campos_proveedor()
                cargar_proveedores()
            except mysql.connector.Error as db_err:
                 conn.rollback()
                 mostrar_mensaje(f"Error al eliminar proveedor: {db_err}", "error")
                 print(f"DB Error deleting supplier: {db_err}")
            except Exception as ex:
                 conn.rollback()
                 mostrar_mensaje(f"Error inesperado al eliminar: {ex}", "error")
                 print(f"Unexpected Error deleting supplier: {ex}")

        # Buttons
        registrar_button = ft.ElevatedButton(
            "Registrar Proveedor",
            on_click=registrar_proveedor,
            icon=ft.icons.BUSINESS,
             bgcolor=ft.colors.GREEN_700,
             color=ft.colors.WHITE,
             visible=True
        )
        actualizar_button = ft.ElevatedButton(
             "Actualizar Proveedor",
             on_click=actualizar_proveedor_actual,
             icon=ft.icons.UPDATE,
             bgcolor=ft.colors.BLUE_700,
             color=ft.colors.WHITE,
             visible=False
        )
        cancelar_edicion_button = ft.ElevatedButton(
            "Cancelar Edición",
            on_click=lambda e: limpiar_campos_proveedor(),
            icon=ft.icons.CANCEL,
            bgcolor=ft.colors.GREY_600,
            color=ft.colors.WHITE,
            visible=False
         )

        # Initial load
        cargar_proveedores()

        # Layout
        return ft.Column(
             [
                 ft.Text("Gestión de Proveedores", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                 ft.Divider(height=10, color=ft.colors.GREY_400),
                  ft.Row( # Form layout
                      [
                          ft.Column([nombre_empresa_input, contacto_input, telefono_input], spacing=10),
                          ft.Column([email_input, direccion_input], spacing=10),
                      ],
                     alignment=ft.MainAxisAlignment.SPACE_AROUND,
                      vertical_alignment=ft.CrossAxisAlignment.START
                  ),
                 ft.Row( # Buttons
                     [registrar_button, actualizar_button, cancelar_edicion_button],
                     alignment=ft.MainAxisAlignment.CENTER, spacing=10
                 ),
                 ft.Divider(height=10, color=ft.colors.GREY_400),
                 ft.Text("Proveedores Registrados:", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_700),
                 proveedores_container,
             ],
             spacing=15,
             alignment=ft.MainAxisAlignment.START,
             expand=True
         )


    # --- Function to Create Productos View ---
    def crear_vista_productos():
        """Creates the UI Controls and logic for the Productos tab."""
        nombre_input = ft.TextField(label="Nombre*", width=250, color=ft.colors.BLACK)
        descripcion_input = ft.TextField(label="Descripción", width=250, hint_text="Opcional", color=ft.colors.BLACK)
        marca_input = ft.TextField(label="Marca", width=250, hint_text="Opcional", color=ft.colors.BLACK)
        categoria_input = ft.TextField(label="Categoría", width=250, hint_text="Opcional", color=ft.colors.BLACK)
        talla_input = ft.TextField(label="Talla*", width=250, color=ft.colors.BLACK, input_filter=ft.InputFilter(r'[0-9\.]'))
        color_input = ft.TextField(label="Color", width=250, hint_text="Opcional", color=ft.colors.BLACK)
        stock_input = ft.TextField(label="Stock*", width=250, color=ft.colors.BLACK, input_filter=ft.InputFilter(r'[0-9]'))
        precio_input = ft.TextField(label="Precio*", width=250, color=ft.colors.BLACK, input_filter=ft.InputFilter(r'[0-9\.]'))
        id_proveedor_input = ft.TextField(label="ID Proveedor", width=250, hint_text="Opcional (número)", color=ft.colors.BLACK, input_filter=ft.InputFilter(r'[0-9]'))
        qr_input = ft.TextField(label="QR*", width=250, color=ft.colors.BLACK, max_length=13) # Limit length based on schema CHAR(13)

        productos_container = ft.Column(scroll="adaptive", expand=True, spacing=5)
        producto_id_para_editar = ft.Ref[int]()


        def limpiar_campos_producto():
            nombre_input.value = ""
            descripcion_input.value = ""
            marca_input.value = ""
            categoria_input.value = ""
            talla_input.value = ""
            color_input.value = ""
            stock_input.value = ""
            precio_input.value = ""
            id_proveedor_input.value = ""
            qr_input.value = ""
            producto_id_para_editar.current = None
            registrar_button.visible = True
            actualizar_button.visible = False
            cancelar_edicion_button.visible = False
            page.update()


        def cargar_productos():
            if not cursor: return
            productos_container.controls.clear()
            try:
                # Join with proveedores to show supplier name (optional but helpful)
                # cursor.execute("SELECT p.id_producto, p.nombre, p.categoria, p.stock, p.precio, pr.nombre_empresa FROM productos p LEFT JOIN proveedores pr ON p.id_proveedor = pr.id_proveedor ORDER BY p.nombre")
                # Simpler version without join first:
                cursor.execute("SELECT id_producto, nombre, categoria, stock, precio, qr FROM productos ORDER BY nombre")
                productos = cursor.fetchall()
                if not productos:
                     productos_container.controls.append(ft.Text("No hay productos registrados.", color=ft.colors.GREY_700))
                else:
                    for prod in productos:
                        prod_id = prod[0]
                        precio_formatted = f"${prod[4]:,.2f}" if isinstance(prod[4], (int, float, Decimal)) else "N/A"
                        # proveedor_nombre = prod[5] if len(prod) > 5 and prod[5] else "Sin Proveedor" # If using JOIN
                        productos_container.controls.append(
                             ft.Container(
                                padding=ft.padding.symmetric(vertical=2),
                                content= ft.Row(
                                    [
                                        ft.Text(f"{prod[1]} ({prod[2] or 'N/A'}) - Stock: {prod[3]} - QR: {prod[5]} - {precio_formatted}", expand=True, color=ft.colors.BLACK),
                                         ft.IconButton(
                                            ft.icons.EDIT,
                                            tooltip="Editar Producto",
                                            on_click=lambda e, id=prod_id: cargar_datos_producto_para_editar(id),
                                            icon_color=ft.colors.BLUE_700
                                        ),
                                        ft.IconButton(
                                            ft.icons.DELETE_FOREVER,
                                            tooltip="Eliminar Producto",
                                            on_click=lambda e, id=prod_id: eliminar_producto(id),
                                             icon_color=ft.colors.RED_700
                                        ),
                                    ],
                                     alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                     vertical_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            )
                        )
                page.update()
            except mysql.connector.Error as db_err:
                 mostrar_mensaje(f"Error al cargar productos: {db_err}", "error")
            except Exception as ex:
                 mostrar_mensaje(f"Error inesperado al cargar productos: {ex}", "error")

        def cargar_datos_producto_para_editar(producto_id):
            if not cursor: return
            try:
                cursor.execute("SELECT nombre, descripcion, marca, categoria, talla, color, stock, precio, id_proveedor, qr FROM productos WHERE id_producto = %s", (producto_id,))
                producto = cursor.fetchone()
                if producto:
                    nombre_input.value = producto[0]
                    descripcion_input.value = producto[1] if producto[1] else ""
                    marca_input.value = producto[2] if producto[2] else ""
                    categoria_input.value = producto[3] if producto[3] else ""
                    talla_input.value = str(producto[4]) if producto[4] is not None else "" # Decimal to string
                    color_input.value = producto[5] if producto[5] else ""
                    stock_input.value = str(producto[6]) if producto[6] is not None else "" # Int to string
                    precio_input.value = str(producto[7]) if producto[7] is not None else "" # Decimal to string
                    id_proveedor_input.value = str(producto[8]) if producto[8] is not None else "" # Int to string or empty
                    qr_input.value = producto[9] if producto[9] else ""

                    producto_id_para_editar.current = producto_id
                    registrar_button.visible = False
                    actualizar_button.visible = True
                    cancelar_edicion_button.visible = True
                    page.update()
                else:
                    mostrar_mensaje("Producto no encontrado.", "error")
            except mysql.connector.Error as db_err:
                 mostrar_mensaje(f"Error al cargar datos del producto: {db_err}", "error")
            except Exception as ex:
                 mostrar_mensaje(f"Error inesperado al cargar producto para editar: {ex}", "error")

        def registrar_producto(e):
            # --- Validation ---
            nombre = nombre_input.value.strip()
            talla_str = talla_input.value.strip()
            stock_str = stock_input.value.strip()
            precio_str = precio_input.value.strip()
            qr = qr_input.value.strip()

            if not (nombre and talla_str and stock_str and precio_str and qr):
                mostrar_mensaje("Completa los campos obligatorios: Nombre, Talla, Stock, Precio, QR (*).", "error")
                return

            try:
                talla = Decimal(talla_str)
                stock = int(stock_str)
                precio = Decimal(precio_str)
            except ValueError:
                mostrar_mensaje("Talla, Stock o Precio tienen formato numérico inválido.", "error")
                return

            if len(qr) > 13:
                mostrar_mensaje("El código QR no puede tener más de 13 caracteres.", "error")
                return

            id_proveedor = None
            id_proveedor_str = id_proveedor_input.value.strip()
            if id_proveedor_str:
                try:
                    id_proveedor = int(id_proveedor_str)
                    # Optional: Check if proveedor ID exists
                    # cursor.execute("SELECT COUNT(*) FROM proveedores WHERE id_proveedor = %s", (id_proveedor,))
                    # if cursor.fetchone()[0] == 0:
                    #     mostrar_mensaje(f"El ID de Proveedor {id_proveedor} no existe.", "error")
                    #     return
                except ValueError:
                    mostrar_mensaje("ID de Proveedor debe ser un número entero.", "error")
                    return
                except mysql.connector.Error as db_err:
                     mostrar_mensaje(f"Error al verificar proveedor: {db_err}", "error")
                     return


            # --- Insertion ---
            if not cursor: return
            try:
                 print(f"Intentando insertar producto: {(nombre, descripcion_input.value.strip() or None, marca_input.value.strip() or None, categoria_input.value.strip() or None, talla, color_input.value.strip() or None, stock, precio, id_proveedor, qr)}")
                 cursor.execute(
                     "INSERT INTO productos (nombre, descripcion, marca, categoria, talla, color, stock, precio, id_proveedor, qr) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                     (nombre,
                      descripcion_input.value.strip() or None,
                      marca_input.value.strip() or None,
                      categoria_input.value.strip() or None,
                      talla,
                      color_input.value.strip() or None,
                      stock,
                      precio,
                      id_proveedor,
                      qr)
                 )
                 conn.commit()
                 mostrar_mensaje("Producto registrado exitosamente!", "success")
                 limpiar_campos_producto()
                 cargar_productos()
            except mysql.connector.Error as db_err:
                 conn.rollback()
                 mostrar_mensaje(f"Error al registrar producto: {db_err}", "error")
                 print(f"DB Error registering product: {db_err}")
            except Exception as ex:
                 conn.rollback()
                 mostrar_mensaje(f"Error inesperado al registrar: {ex}", "error")
                 print(f"Unexpected Error registering product: {ex}")


        def actualizar_producto_actual(e):
             if producto_id_para_editar.current:
                actualizar_producto(producto_id_para_editar.current)
             else:
                 mostrar_mensaje("No se seleccionó ningún producto para actualizar.", "error")


        def actualizar_producto(producto_id):
             # --- Validation (similar to registration) ---
             nombre = nombre_input.value.strip()
             talla_str = talla_input.value.strip()
             stock_str = stock_input.value.strip()
             precio_str = precio_input.value.strip()
             qr = qr_input.value.strip()

             if not (nombre and talla_str and stock_str and precio_str and qr):
                 mostrar_mensaje("Completa los campos obligatorios: Nombre, Talla, Stock, Precio, QR (*).", "error")
                 return

             try:
                 talla = Decimal(talla_str)
                 stock = int(stock_str)
                 precio = Decimal(precio_str)
             except ValueError:
                 mostrar_mensaje("Talla, Stock o Precio tienen formato numérico inválido.", "error")
                 return

             if len(qr) > 13:
                 mostrar_mensaje("El código QR no puede tener más de 13 caracteres.", "error")
                 return

             id_proveedor = None
             id_proveedor_str = id_proveedor_input.value.strip()
             if id_proveedor_str:
                 try:
                     id_proveedor = int(id_proveedor_str)
                     # Optional: Check proveedor existence (important if they could be deleted)
                     # cursor.execute("SELECT COUNT(*) FROM proveedores WHERE id_proveedor = %s", (id_proveedor,))
                     # if cursor.fetchone()[0] == 0:
                     #     mostrar_mensaje(f"El ID de Proveedor {id_proveedor} no existe.", "error")
                     #     return
                 except ValueError:
                     mostrar_mensaje("ID de Proveedor debe ser un número entero.", "error")
                     return
                 except mysql.connector.Error as db_err:
                     mostrar_mensaje(f"Error al verificar proveedor: {db_err}", "error")
                     return

             # --- Update ---
             if not cursor: return
             try:
                 cursor.execute(
                     "UPDATE productos SET nombre=%s, descripcion=%s, marca=%s, categoria=%s, talla=%s, color=%s, stock=%s, precio=%s, id_proveedor=%s, qr=%s WHERE id_producto=%s",
                     (nombre,
                      descripcion_input.value.strip() or None,
                      marca_input.value.strip() or None,
                      categoria_input.value.strip() or None,
                      talla,
                      color_input.value.strip() or None,
                      stock,
                      precio,
                      id_proveedor,
                      qr,
                      producto_id) # Use the passed producto_id
                 )
                 conn.commit()
                 mostrar_mensaje("Producto actualizado exitosamente!", "success")
                 limpiar_campos_producto()
                 cargar_productos()
             except mysql.connector.Error as db_err:
                 conn.rollback()
                 mostrar_mensaje(f"Error al actualizar producto: {db_err}", "error")
                 print(f"DB Error updating product: {db_err}")
             except Exception as ex:
                 conn.rollback()
                 mostrar_mensaje(f"Error inesperado al actualizar: {ex}", "error")
                 print(f"Unexpected Error updating product: {ex}")


        def eliminar_producto(producto_id):
            if not cursor: return
            try:
                # Check for related details in ventas or pedidos - IMPORTANT
                cursor.execute("SELECT COUNT(*) FROM detalles_venta WHERE id_producto = %s", (producto_id,))
                ventas_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM detalles_pedido WHERE id_producto = %s", (producto_id,))
                pedidos_count = cursor.fetchone()[0]

                if ventas_count > 0 or pedidos_count > 0:
                    mostrar_mensaje(f"No se puede eliminar, el producto está en {ventas_count} ventas y {pedidos_count} pedidos.", "error")
                    return # Prevent deletion

                cursor.execute("DELETE FROM productos WHERE id_producto = %s", (producto_id,))
                conn.commit()
                mostrar_mensaje("Producto eliminado exitosamente!", "success")
                limpiar_campos_producto() # Clean form if the deleted product was being edited
                cargar_productos()
            except mysql.connector.Error as db_err:
                 conn.rollback()
                 mostrar_mensaje(f"Error al eliminar producto: {db_err}", "error")
                 print(f"DB Error deleting product: {db_err}")
            except Exception as ex:
                 conn.rollback()
                 mostrar_mensaje(f"Error inesperado al eliminar: {ex}", "error")
                 print(f"Unexpected Error deleting product: {ex}")


        # Buttons
        registrar_button = ft.ElevatedButton(
            "Registrar Producto",
            on_click=registrar_producto,
             icon=ft.icons.ADD_SHOPPING_CART,
             bgcolor=ft.colors.GREEN_700,
             color=ft.colors.WHITE,
             visible=True
        )
        actualizar_button = ft.ElevatedButton(
             "Actualizar Producto",
             on_click=actualizar_producto_actual,
             icon=ft.icons.UPDATE,
             bgcolor=ft.colors.BLUE_700,
             color=ft.colors.WHITE,
             visible=False
        )
        cancelar_edicion_button = ft.ElevatedButton(
            "Cancelar Edición",
            on_click=lambda e: limpiar_campos_producto(),
            icon=ft.icons.CANCEL,
            bgcolor=ft.colors.GREY_600,
            color=ft.colors.WHITE,
            visible=False
         )


        # Initial Load
        cargar_productos()

        # Layout for this tab
        return ft.Column(
            [
                 ft.Text("Gestión de Productos", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                 ft.Divider(height=10, color=ft.colors.GREY_400),
                 # Use two columns for better form layout
                 ft.Row(
                     [
                         ft.Column(
                             [
                                 nombre_input,
                                 descripcion_input,
                                 marca_input,
                                 categoria_input,
                                 talla_input,
                              ],
                             spacing=10,
                         ),
                         ft.Column(
                             [
                                 color_input,
                                 stock_input,
                                 precio_input,
                                 id_proveedor_input,
                                 qr_input,
                              ],
                             spacing=10,
                          ),
                     ],
                     alignment=ft.MainAxisAlignment.SPACE_AROUND,
                     vertical_alignment=ft.CrossAxisAlignment.START
                 ),
                 ft.Row( # Buttons
                    [registrar_button, actualizar_button, cancelar_edicion_button],
                    alignment=ft.MainAxisAlignment.CENTER, spacing=10
                ),
                 ft.Divider(height=10, color=ft.colors.GREY_400),
                 ft.Text("Productos Registrados:", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_700),
                 productos_container, # List container
             ],
             spacing=15,
             alignment=ft.MainAxisAlignment.START,
             expand=True,
             # scroll="adaptive" # Scrolling applied to inner container 'productos_container'
         )

    # --- Create Tabs ---
    # Check if connection was successful before creating views that need it
    if conn and cursor:
        tabs_control = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Clientes",
                    icon=ft.icons.PERSON,
                    content=ft.Container( # Add padding around each tab's content
                        content=crear_vista_clientes(),
                        padding=ft.padding.all(15),
                    )
                ),
                ft.Tab(
                    text="Empleados",
                    icon=ft.icons.PEOPLE,
                     content=ft.Container(
                        content=crear_vista_empleados(),
                         padding=ft.padding.all(15),
                    )
                ),
                ft.Tab(
                    text="Proveedores",
                    icon=ft.icons.BUSINESS,
                    content=ft.Container(
                        content=crear_vista_proveedores(),
                        padding=ft.padding.all(15),
                     )
                 ),
                 ft.Tab(
                     text="Productos",
                     icon=ft.icons.SHOPPING_BAG,
                     content=ft.Container(
                         content=crear_vista_productos(),
                         padding=ft.padding.all(15),
                     )
                 ),
             ],
             expand=True, # Make tabs fill width
         )

        # Add the tabs to the page
        page.add(tabs_control)
    else:
        # Display a message if the database isn't connected
        page.add(ft.Text("No se pudo conectar a la base de datos. La aplicación no puede funcionar.", color=ft.colors.RED, size=20))

    # --- Close connection when app closes ---
    def cerrar_conexion(_):
         if conn and conn.is_connected():
             cursor.close()
             conn.close()
             print("Database connection closed.")

    page.on_disconnect = cerrar_conexion # Use on_disconnect for graceful closing


# --- Run the Flet App ---
if __name__ == "__main__":
     ft.app(target=main)