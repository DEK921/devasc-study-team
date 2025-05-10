# coding: utf-8
import flet as ft
import mysql.connector
from decimal import Decimal, ROUND_HALF_UP # Import Decimal for handling database decimals correctly
from datetime import datetime # For Ventas module

def main(page: ft.Page):
    page.title = "Sistema de Gestión - Zapatería Integral"
    page.bgcolor = ft.colors.GREY_200
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    # page.window_width = 1000 # Optional: set a default width
    # page.window_height = 750 # Optional: set a default height

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
        cursor = conn.cursor() # Standard cursor (not dictionary=True)
        print("Database connected successfully.")
    except mysql.connector.Error as err:
        page.add(ft.Text(f"Error de conexión a la base de datos: {err}", color=ft.colors.RED, size=18, text_align=ft.TextAlign.CENTER))
        print(f"Database connection error: {err}")
        # Application cannot function without DB, so we might stop here or disable controls.
        # For now, tabs will show an error if conn/cursor are None.

    # --- Shared Utility Function ---
    def mostrar_mensaje(mensaje, tipo, duration=3000):
        """Displays a SnackBar message."""
        color = ft.colors.GREEN_ACCENT_700 if tipo == "success" else ft.colors.RED_ACCENT_700
        page.snack_bar = ft.SnackBar(
            ft.Text(mensaje, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=color,
            open=True,
            duration=duration
        )
        page.update()

    # --- Database functions for Ventas (adapted from Script 2) ---
    def _registrar_venta_db(db_conn, db_cursor, id_cliente, id_empleado, productos_qr_data):
        """
        Registra una nueva venta.
        productos_qr_data: Lista de diccionarios, cada uno con {"qr": str, "cantidad": int, "precio_unitario": Decimal}
        Uses passed db_conn and db_cursor. Assumes cursor is NOT dictionary based.
        """
        current_total_venta = Decimal("0.00")
        detalles_para_insertar = []
        productos_para_actualizar_stock = []

        try:
            # Iniciar transacción
            db_conn.start_transaction()

            for p_data in productos_qr_data:
                qr = p_data["qr"]
                cantidad_vendida = p_data["cantidad"]
                precio_unitario_venta = Decimal(p_data["precio_unitario"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                # 1. Obtener id_producto, stock actual y nombre usando QR
                db_cursor.execute("SELECT id_producto, stock, nombre, precio FROM productos WHERE qr = %s", (qr,))
                producto_db_result = db_cursor.fetchone()

                if not producto_db_result:
                    db_conn.rollback()
                    raise ValueError(f"Producto con QR {qr} no encontrado.")

                id_producto = producto_db_result[0]
                stock_actual = producto_db_result[1]
                nombre_producto = producto_db_result[2]
                # precio_lista_producto = producto_db_result[3] # Available if needed

                if stock_actual < cantidad_vendida:
                    db_conn.rollback()
                    raise ValueError(f"Stock insuficiente para '{nombre_producto}' (QR: {qr}). Disponible: {stock_actual}, Solicitado: {cantidad_vendida}.")

                # 2. Calcular subtotal para este producto
                subtotal = (Decimal(cantidad_vendida) * precio_unitario_venta).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                current_total_venta += subtotal

                detalles_para_insertar.append({
                    "id_producto": id_producto,
                    "cantidad": cantidad_vendida,
                    "precio_unitario": precio_unitario_venta,
                    "subtotal": subtotal
                })

                productos_para_actualizar_stock.append({
                    "id_producto": id_producto,
                    "nueva_existencia": stock_actual - cantidad_vendida
                })

            # 3. Insertar en la tabla 'ventas'
            db_cursor.execute("""
                INSERT INTO ventas (id_cliente, id_empleado, fecha_venta, total_venta)
                VALUES (%s, %s, %s, %s)
            """, (id_cliente, id_empleado, datetime.now(), current_total_venta))
            id_venta = db_cursor.lastrowid

            # 4. Insertar en la tabla 'detalles_venta'
            for detalle in detalles_para_insertar:
                db_cursor.execute("""
                    INSERT INTO detalles_venta (id_venta, id_producto, cantidad, precio_unitario, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                """, (id_venta, detalle["id_producto"], detalle["cantidad"], detalle["precio_unitario"], detalle["subtotal"]))

            # 5. Actualizar stock en la tabla 'productos'
            for stock_update in productos_para_actualizar_stock:
                db_cursor.execute(
                    "UPDATE productos SET stock = %s WHERE id_producto = %s",
                    (stock_update["nueva_existencia"], stock_update["id_producto"])
                )

            db_conn.commit() # Confirmar transacción
            return id_venta

        except (mysql.connector.Error, ValueError) as err:
            db_conn.rollback() # Revertir cambios en caso de error
            raise err # Re-raise the error to be handled by the calling function
        # finally clause removed, cursor/conn managed externally

    def _obtener_ventas_db(db_conn, db_cursor):
        """
        Obtener lista de ventas con detalles.
        Uses passed db_conn and db_cursor. Assumes cursor is NOT dictionary based.
        """
        # Indices for main query:
        # 0: v.id_venta, 1: c.nombre, 2: c.apellido, 3: e.nombre, 4: e.apellido,
        # 5: v.fecha_venta, 6: v.total_venta
        db_cursor.execute("""
            SELECT
                v.id_venta,
                c.nombre AS cliente_nombre,
                c.apellido AS cliente_apellido,
                e.nombre AS empleado_nombre,
                e.apellido AS empleado_apellido,
                v.fecha_venta,
                v.total_venta
            FROM ventas v
            LEFT JOIN clientes c ON v.id_cliente = c.id_cliente
            LEFT JOIN empleados e ON v.id_empleado = e.id_empleado
            ORDER BY v.id_venta DESC
        """)
        ventas_raw = db_cursor.fetchall()
        ventas_list = []

        for v_raw in ventas_raw:
            venta_data = {
                "id_venta": v_raw[0],
                "cliente_nombre": v_raw[1],
                "cliente_apellido": v_raw[2],
                "empleado_nombre": v_raw[3],
                "empleado_apellido": v_raw[4],
                "fecha_venta": v_raw[5],
                "total_venta": v_raw[6],
                "detalles": []
            }
            # Indices for details query:
            # 0: p.nombre, 1: dv.cantidad, 2: dv.precio_unitario, 3: dv.subtotal
            db_cursor.execute("""
                SELECT p.nombre, dv.cantidad, dv.precio_unitario, dv.subtotal
                FROM detalles_venta dv
                JOIN productos p ON dv.id_producto = p.id_producto
                WHERE dv.id_venta = %s
            """, (venta_data["id_venta"],))
            detalles_raw = db_cursor.fetchall()
            for d_raw in detalles_raw:
                venta_data["detalles"].append({
                    "nombre_producto": d_raw[0],
                    "cantidad": d_raw[1],
                    "precio_unitario": d_raw[2],
                    "subtotal": d_raw[3]
                })
            ventas_list.append(venta_data)
        return ventas_list


    # --- Function to Create Clientes View ---
    def crear_vista_clientes():
        """Creates the UI Controls and logic for the Clientes tab."""
        nombre_input = ft.TextField(label="Nombre*", width=300, color=ft.colors.BLACK)
        apellido_input = ft.TextField(label="Apellido*", width=300, color=ft.colors.BLACK)
        email_input = ft.TextField(label="Email*", width=300, color=ft.colors.BLACK)
        telefono_input = ft.TextField(label="Teléfono", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        direccion_input = ft.TextField(label="Dirección", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        clientes_container = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=5)
        cliente_id_para_editar = ft.Ref[int]()

        def limpiar_campos_cliente():
            nombre_input.value = ""
            apellido_input.value = ""
            email_input.value = ""
            telefono_input.value = ""
            direccion_input.value = ""
            cliente_id_para_editar.current = None
            guardar_button.text = "Guardar Cliente" # Reset button text
            guardar_button.icon = ft.icons.SAVE
            guardar_button.on_click = guardar_cliente_action # Reset on_click
            guardar_button.bgcolor = ft.colors.GREEN_ACCENT_700
            # actualizar_button.visible = False # Replaced by dynamic guardar_button
            # cancelar_edicion_button.visible = False
            if hasattr(cancelar_edicion_button, 'visible'): # Check if it exists (it might be removed)
                cancelar_edicion_button.visible = False
            page.update()

        def cargar_clientes():
            if not cursor or not conn:
                clientes_container.controls.clear()
                clientes_container.controls.append(ft.Text("Error de base de datos no disponible para cargar clientes.", color=ft.colors.RED))
                page.update()
                return
            clientes_container.controls.clear()
            try:
                cursor.execute("SELECT id_cliente, nombre, apellido, email FROM clientes ORDER BY apellido, nombre")
                clientes = cursor.fetchall()
                if not clientes:
                    clientes_container.controls.append(ft.Text("No hay clientes registrados.", color=ft.colors.GREY_700, style=ft.TextStyle(italic=True)))
                else:
                    for cliente in clientes:
                        cliente_id_val = cliente[0]
                        clientes_container.controls.append(
                            ft.Container(
                                padding=ft.padding.symmetric(vertical=3, horizontal=5),
                                border_radius=5,
                                # bgcolor=ft.colors.WHITE,
                                # shadow=ft.BoxShadow(spread_radius=1,blur_radius=3,color=ft.colors.with_opacity(0.1, ft.colors.BLACK)),
                                content=ft.Row(
                                    [
                                        ft.Text(f"{cliente[1]} {cliente[2]} ({cliente[3]})", expand=True, color=ft.colors.BLACK87, weight=ft.FontWeight.NORMAL),
                                        ft.IconButton(
                                            ft.icons.EDIT_NOTE, # Changed icon
                                            tooltip="Editar Cliente",
                                            on_click=lambda e, id_edit=cliente_id_val: cargar_datos_cliente_para_editar(id_edit),
                                            icon_color=ft.colors.BLUE_ACCENT_700, icon_size=20
                                        ),
                                        ft.IconButton(
                                            ft.icons.DELETE_FOREVER,
                                            tooltip="Eliminar Cliente",
                                            on_click=lambda e, id_del=cliente_id_val: eliminar_cliente_action(id_del),
                                            icon_color=ft.colors.RED_ACCENT_700, icon_size=20
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

        def cargar_datos_cliente_para_editar(cliente_id_val_edit):
            if not cursor: return
            try:
                cursor.execute("SELECT nombre, apellido, email, telefono, direccion FROM clientes WHERE id_cliente = %s", (cliente_id_val_edit,))
                cliente = cursor.fetchone()
                if cliente:
                    nombre_input.value = cliente[0]
                    apellido_input.value = cliente[1]
                    email_input.value = cliente[2]
                    telefono_input.value = cliente[3] if cliente[3] else ""
                    direccion_input.value = cliente[4] if cliente[4] else ""
                    cliente_id_para_editar.current = cliente_id_val_edit
                    guardar_button.text = "Actualizar Cliente"
                    guardar_button.icon = ft.icons.UPDATE
                    guardar_button.on_click = lambda e: actualizar_cliente_action(cliente_id_val_edit) # Pass id directly
                    guardar_button.bgcolor = ft.colors.ORANGE_ACCENT_700 # Distinct color for update
                    # actualizar_button.visible = True
                    cancelar_edicion_button.visible = True # This can be one button
                    page.update()
                else:
                    mostrar_mensaje("Cliente no encontrado.", "error")
            except mysql.connector.Error as db_err:
                mostrar_mensaje(f"Error al cargar datos del cliente: {db_err}", "error")
            except Exception as ex:
                mostrar_mensaje(f"Error inesperado al cargar cliente: {ex}", "error")

        def guardar_cliente_action(e):
            if not (nombre_input.value and apellido_input.value and email_input.value):
                mostrar_mensaje("Por favor, completa los campos obligatorios (*).", "error")
                return
            if not cursor or not conn: return

            try:
                cursor.execute(
                    "INSERT INTO clientes (nombre, apellido, email, telefono, direccion) VALUES (%s, %s, %s, %s, %s)",
                    (nombre_input.value.strip(),
                     apellido_input.value.strip(),
                     email_input.value.strip(),
                     telefono_input.value.strip() or None,
                     direccion_input.value.strip() or None)
                )
                conn.commit()
                mostrar_mensaje("Cliente agregado exitosamente!", "success")
                limpiar_campos_cliente()
                cargar_clientes()
            except mysql.connector.Error as db_err:
                conn.rollback()
                mostrar_mensaje(f"Error al guardar cliente: {db_err}", "error")
            except Exception as ex:
                conn.rollback()
                mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def actualizar_cliente_action(cliente_id_to_update): # Renamed and accepts ID
            if not (nombre_input.value and apellido_input.value and email_input.value):
                mostrar_mensaje("Por favor, completa los campos obligatorios (*).", "error")
                return
            if not cursor or not conn: return

            try:
                cursor.execute(
                    "UPDATE clientes SET nombre = %s, apellido = %s, email = %s, telefono = %s, direccion = %s WHERE id_cliente = %s",
                    (nombre_input.value.strip(),
                     apellido_input.value.strip(),
                     email_input.value.strip(),
                     telefono_input.value.strip() or None,
                     direccion_input.value.strip() or None,
                     cliente_id_to_update) # Use the passed ID
                )
                conn.commit()
                mostrar_mensaje("Cliente actualizado exitosamente!", "success")
                limpiar_campos_cliente()
                cargar_clientes()
            except mysql.connector.Error as db_err:
                conn.rollback()
                mostrar_mensaje(f"Error al actualizar cliente: {db_err}", "error")
            except Exception as ex:
                conn.rollback()
                mostrar_mensaje(f"Error inesperado al actualizar: {ex}", "error")

        def eliminar_cliente_action(cliente_id_to_delete):
            if not cursor or not conn: return
            try:
                cursor.execute("SELECT COUNT(*) FROM ventas WHERE id_cliente = %s", (cliente_id_to_delete,))
                ventas_count = cursor.fetchone()[0]
                if ventas_count > 0:
                    mostrar_mensaje(f"No se puede eliminar el cliente, tiene {ventas_count} ventas asociadas.", "error")
                    return

                cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (cliente_id_to_delete,))
                conn.commit()
                mostrar_mensaje("Cliente eliminado exitosamente!", "success")
                if cliente_id_para_editar.current == cliente_id_to_delete: # If deleting the one being edited
                    limpiar_campos_cliente()
                cargar_clientes()
            except mysql.connector.Error as db_err:
                conn.rollback()
                mostrar_mensaje(f"Error al eliminar cliente: {db_err}", "error")
            except Exception as ex:
                conn.rollback()
                mostrar_mensaje(f"Error inesperado al eliminar: {ex}", "error")

        guardar_button = ft.ElevatedButton( # This button will serve for both save and update
            text="Guardar Cliente",
            on_click=guardar_cliente_action,
            icon=ft.icons.SAVE,
            bgcolor=ft.colors.GREEN_ACCENT_700, # Brighter green
            color=ft.colors.WHITE,
            height=40,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        cancelar_edicion_button = ft.OutlinedButton( # Changed style for cancel
            "Cancelar Edición",
            on_click=lambda e: limpiar_campos_cliente(),
            icon=ft.icons.CANCEL_OUTLINED,
            visible=False, # Initially hidden
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=40
         )

        cargar_clientes()

        return ft.Column(
            [
                ft.Text("Gestión de Clientes", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                ft.Divider(height=10, color=ft.colors.GREY_400),
                ft.Row(
                    [
                       ft.Column([nombre_input, apellido_input, email_input], spacing=10, expand=1),
                       ft.Column([telefono_input, direccion_input], spacing=10, expand=1)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN, # Use space_between for wider spacing
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=20 # Space between the columns
                ),
                ft.Row(
                    [guardar_button, cancelar_edicion_button],
                    alignment=ft.MainAxisAlignment.END, spacing=10, # Align buttons to the right
                 ),
                ft.Divider(height=20, color=ft.colors.GREY_400), # Increased height
                ft.Text("Clientes Registrados:", size=18, weight=ft.FontWeight.W_600, color=ft.colors.BLUE_GREY_700),
                ft.Container(content=clientes_container, expand=True, padding=ft.padding.only(top=5))
            ],
            spacing=15, alignment=ft.MainAxisAlignment.START, expand=True
        )

    # --- Function to Create Empleados View ---
    def crear_vista_empleados():
        nombre_input = ft.TextField(label="Nombre*", width=300, color=ft.colors.BLACK)
        apellido_input = ft.TextField(label="Apellido*", width=300, color=ft.colors.BLACK)
        cargo_input = ft.TextField(label="Cargo", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        telefono_input = ft.TextField(label="Teléfono", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        email_input = ft.TextField(label="Email", width=300, hint_text="Opcional (único)", color=ft.colors.BLACK)
        salario_input = ft.TextField(label="Salario*", width=300, color=ft.colors.BLACK, input_filter=ft.InputFilter(r'[0-9\.]'), prefix_text="$")
        empleados_container = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=5)
        empleado_id_para_editar = ft.Ref[int]()


        def limpiar_campos_empleado():
            nombre_input.value = ""
            apellido_input.value = ""
            cargo_input.value = ""
            telefono_input.value = ""
            email_input.value = ""
            salario_input.value = ""
            empleado_id_para_editar.current = None
            action_button.text = "Registrar Empleado"
            action_button.icon = ft.icons.PERSON_ADD
            action_button.on_click = registrar_empleado_action
            action_button.bgcolor = ft.colors.GREEN_ACCENT_700
            cancelar_button.visible = False
            page.update()

        def cargar_empleados():
            if not cursor or not conn:
                empleados_container.controls.clear()
                empleados_container.controls.append(ft.Text("Error de base de datos no disponible para cargar empleados.", color=ft.colors.RED))
                page.update()
                return
            empleados_container.controls.clear()
            try:
                cursor.execute("SELECT id_empleado, nombre, apellido, cargo, salario FROM empleados ORDER BY apellido, nombre")
                empleados = cursor.fetchall()
                if not empleados:
                    empleados_container.controls.append(ft.Text("No hay empleados registrados.", color=ft.colors.GREY_700, style=ft.TextStyle(italic=True)))
                else:
                    for emp in empleados:
                        emp_id = emp[0]
                        salario_val = emp[4]
                        salario_formatted = f"${salario_val:,.2f}" if isinstance(salario_val, (int, float, Decimal)) else "N/A"
                        empleados_container.controls.append(
                             ft.Container(
                                padding=ft.padding.symmetric(vertical=3, horizontal=5),
                                content=ft.Row(
                                    [
                                        ft.Text(f"{emp[1]} {emp[2]} - {emp[3] or 'N/A'} ({salario_formatted})", expand=True, color=ft.colors.BLACK87),
                                        ft.IconButton(
                                            ft.icons.EDIT_NOTE,
                                            tooltip="Editar Empleado",
                                            on_click=lambda e, id_edit=emp_id: cargar_datos_empleado_para_editar(id_edit),
                                            icon_color=ft.colors.BLUE_ACCENT_700, icon_size=20
                                        ),
                                        ft.IconButton(
                                            ft.icons.DELETE_FOREVER,
                                            tooltip="Eliminar Empleado",
                                            on_click=lambda e, id_del=emp_id: eliminar_empleado_action(id_del),
                                            icon_color=ft.colors.RED_ACCENT_700, icon_size=20
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            )
                        )
                page.update()
            except mysql.connector.Error as db_err:
                 mostrar_mensaje(f"Error al cargar empleados: {db_err}", "error")
            except Exception as ex:
                 mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def cargar_datos_empleado_para_editar(emp_id_val_edit):
            if not cursor: return
            try:
                cursor.execute("SELECT nombre, apellido, cargo, telefono, email, salario FROM empleados WHERE id_empleado = %s", (emp_id_val_edit,))
                empleado = cursor.fetchone()
                if empleado:
                    nombre_input.value = empleado[0]
                    apellido_input.value = empleado[1]
                    cargo_input.value = empleado[2] if empleado[2] else ""
                    telefono_input.value = empleado[3] if empleado[3] else ""
                    email_input.value = empleado[4] if empleado[4] else ""
                    salario_input.value = str(empleado[5]) if empleado[5] is not None else ""
                    empleado_id_para_editar.current = emp_id_val_edit
                    action_button.text = "Actualizar Empleado"
                    action_button.icon = ft.icons.UPDATE
                    action_button.on_click = lambda e: actualizar_empleado_action(emp_id_val_edit)
                    action_button.bgcolor = ft.colors.ORANGE_ACCENT_700
                    cancelar_button.visible = True
                    page.update()
                else:
                    mostrar_mensaje("Empleado no encontrado.", "error")
            except mysql.connector.Error as db_err:
                 mostrar_mensaje(f"Error al cargar datos del empleado: {db_err}", "error")
            except Exception as ex:
                 mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def registrar_empleado_action(e):
            if not (nombre_input.value and apellido_input.value and salario_input.value):
                mostrar_mensaje("Por favor, completa Nombre, Apellido y Salario (*).", "error")
                return
            if not cursor or not conn: return

            try:
                salario = Decimal(salario_input.value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if salario < 0:
                    mostrar_mensaje("El salario no puede ser negativo.", "error")
                    return
            except Exception:
                 mostrar_mensaje("Salario inválido. Debe ser un número.", "error")
                 return

            try:
                cursor.execute(
                    "INSERT INTO empleados (nombre, apellido, cargo, telefono, email, salario) VALUES (%s, %s, %s, %s, %s, %s)",
                    (nombre_input.value.strip(), apellido_input.value.strip(),
                     cargo_input.value.strip() or None, telefono_input.value.strip() or None,
                     email_input.value.strip() or None, salario)
                )
                conn.commit()
                mostrar_mensaje("Empleado registrado exitosamente!", "success")
                limpiar_campos_empleado()
                cargar_empleados()
            except mysql.connector.Error as db_err:
                conn.rollback(); mostrar_mensaje(f"Error al registrar empleado: {db_err}", "error")
            except Exception as ex:
                conn.rollback(); mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def actualizar_empleado_action(emp_id_to_update):
            if not (nombre_input.value and apellido_input.value and salario_input.value):
                mostrar_mensaje("Por favor, completa Nombre, Apellido y Salario (*).", "error")
                return
            if not cursor or not conn: return
            try:
                salario = Decimal(salario_input.value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if salario < 0:
                    mostrar_mensaje("El salario no puede ser negativo.", "error")
                    return
            except Exception:
                 mostrar_mensaje("Salario inválido. Debe ser un número.", "error")
                 return

            try:
                cursor.execute(
                    "UPDATE empleados SET nombre = %s, apellido = %s, cargo = %s, telefono = %s, email = %s, salario = %s WHERE id_empleado = %s",
                    (nombre_input.value.strip(), apellido_input.value.strip(),
                     cargo_input.value.strip() or None, telefono_input.value.strip() or None,
                     email_input.value.strip() or None, salario, emp_id_to_update)
                )
                conn.commit()
                mostrar_mensaje("Empleado actualizado exitosamente!", "success")
                limpiar_campos_empleado()
                cargar_empleados()
            except mysql.connector.Error as db_err:
                 conn.rollback(); mostrar_mensaje(f"Error al actualizar empleado: {db_err}", "error")
            except Exception as ex:
                 conn.rollback(); mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def eliminar_empleado_action(emp_id_to_delete):
            if not cursor or not conn: return
            try:
                cursor.execute("SELECT COUNT(*) FROM ventas WHERE id_empleado = %s", (emp_id_to_delete,))
                ventas_count = cursor.fetchone()[0]
                if ventas_count > 0:
                     mostrar_mensaje(f"No se puede eliminar, tiene {ventas_count} ventas asociadas.", "error")
                     return

                cursor.execute("DELETE FROM empleados WHERE id_empleado = %s", (emp_id_to_delete,))
                conn.commit()
                mostrar_mensaje("Empleado eliminado exitosamente!", "success")
                if empleado_id_para_editar.current == emp_id_to_delete:
                    limpiar_campos_empleado()
                cargar_empleados()
            except mysql.connector.Error as db_err:
                conn.rollback(); mostrar_mensaje(f"Error al eliminar empleado: {db_err}", "error")
            except Exception as ex:
                conn.rollback(); mostrar_mensaje(f"Error inesperado: {ex}", "error")

        action_button = ft.ElevatedButton(
             text="Registrar Empleado", on_click=registrar_empleado_action, icon=ft.icons.PERSON_ADD,
             bgcolor=ft.colors.GREEN_ACCENT_700, color=ft.colors.WHITE, height=40,
             style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        cancelar_button = ft.OutlinedButton(
            "Cancelar Edición", on_click=lambda e: limpiar_campos_empleado(), icon=ft.icons.CANCEL_OUTLINED, visible=False,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), height=40
         )
        cargar_empleados()
        return ft.Column(
            [
                ft.Text("Gestión de Empleados", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                ft.Divider(height=10, color=ft.colors.GREY_400),
                 ft.Row(
                     [
                         ft.Column([nombre_input, apellido_input, cargo_input], spacing=10, expand=1),
                         ft.Column([telefono_input, email_input, salario_input], spacing=10, expand=1),
                     ],
                     alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START, spacing=20
                 ),
                ft.Row([action_button, cancelar_button], alignment=ft.MainAxisAlignment.END, spacing=10),
                ft.Divider(height=20, color=ft.colors.GREY_400),
                ft.Text("Empleados Registrados:", size=18, weight=ft.FontWeight.W_600, color=ft.colors.BLUE_GREY_700),
                ft.Container(content=empleados_container, expand=True, padding=ft.padding.only(top=5))
            ],
            spacing=15, alignment=ft.MainAxisAlignment.START, expand=True
        )

    # --- Function to Create Proveedores View ---
    def crear_vista_proveedores():
        nombre_empresa_input = ft.TextField(label="Nombre de la Empresa*", width=300, color=ft.colors.BLACK)
        contacto_input = ft.TextField(label="Contacto", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        telefono_input = ft.TextField(label="Teléfono", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        email_input = ft.TextField(label="Email", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        direccion_input = ft.TextField(label="Dirección", width=300, hint_text="Opcional", color=ft.colors.BLACK)
        proveedores_container = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=5)
        proveedor_id_para_editar = ft.Ref[int]()

        def limpiar_campos_proveedor():
            nombre_empresa_input.value = ""
            contacto_input.value = ""
            telefono_input.value = ""
            email_input.value = ""
            direccion_input.value = ""
            proveedor_id_para_editar.current = None
            action_button.text = "Registrar Proveedor"
            action_button.icon = ft.icons.BUSINESS_CENTER # Changed icon
            action_button.on_click = registrar_proveedor_action
            action_button.bgcolor = ft.colors.GREEN_ACCENT_700
            cancelar_button.visible = False
            page.update()

        def cargar_proveedores():
            if not cursor or not conn:
                proveedores_container.controls.clear()
                proveedores_container.controls.append(ft.Text("Error de base de datos no disponible para cargar proveedores.", color=ft.colors.RED))
                page.update()
                return
            proveedores_container.controls.clear()
            try:
                cursor.execute("SELECT id_proveedor, nombre_empresa, contacto, telefono FROM proveedores ORDER BY nombre_empresa")
                proveedores = cursor.fetchall()
                if not proveedores:
                    proveedores_container.controls.append(ft.Text("No hay proveedores registrados.", color=ft.colors.GREY_700, style=ft.TextStyle(italic=True)))
                else:
                    for prov in proveedores:
                        prov_id = prov[0]
                        proveedores_container.controls.append(
                            ft.Container(
                                padding=ft.padding.symmetric(vertical=3, horizontal=5),
                                content = ft.Row(
                                    [
                                        ft.Text(f"{prov[1]} (Contacto: {prov[2] or 'N/A'}, Tel: {prov[3] or 'N/A'})", expand=True, color=ft.colors.BLACK87),
                                        ft.IconButton(ft.icons.EDIT_NOTE, tooltip="Editar Proveedor",
                                            on_click=lambda e, id_edit=prov_id: cargar_datos_proveedor_para_editar(id_edit),
                                            icon_color=ft.colors.BLUE_ACCENT_700, icon_size=20),
                                        ft.IconButton(ft.icons.DELETE_FOREVER, tooltip="Eliminar Proveedor",
                                            on_click=lambda e, id_del=prov_id: eliminar_proveedor_action(id_del),
                                            icon_color=ft.colors.RED_ACCENT_700, icon_size=20),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            )
                        )
                page.update()
            except mysql.connector.Error as db_err: mostrar_mensaje(f"Error al cargar proveedores: {db_err}", "error")
            except Exception as ex: mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def cargar_datos_proveedor_para_editar(prov_id_val_edit):
             if not cursor: return
             try:
                 cursor.execute("SELECT nombre_empresa, contacto, telefono, email, direccion FROM proveedores WHERE id_proveedor = %s", (prov_id_val_edit,))
                 proveedor = cursor.fetchone()
                 if proveedor:
                     nombre_empresa_input.value = proveedor[0]
                     contacto_input.value = proveedor[1] if proveedor[1] else ""
                     telefono_input.value = proveedor[2] if proveedor[2] else ""
                     email_input.value = proveedor[3] if proveedor[3] else ""
                     direccion_input.value = proveedor[4] if proveedor[4] else ""
                     proveedor_id_para_editar.current = prov_id_val_edit
                     action_button.text = "Actualizar Proveedor"
                     action_button.icon = ft.icons.UPDATE
                     action_button.on_click = lambda e: actualizar_proveedor_action(prov_id_val_edit)
                     action_button.bgcolor = ft.colors.ORANGE_ACCENT_700
                     cancelar_button.visible = True
                     page.update()
                 else: mostrar_mensaje("Proveedor no encontrado.", "error")
             except mysql.connector.Error as db_err: mostrar_mensaje(f"Error al cargar proveedor: {db_err}", "error")
             except Exception as ex: mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def registrar_proveedor_action(e):
            if not nombre_empresa_input.value:
                 mostrar_mensaje("El Nombre de la Empresa es obligatorio (*).", "error"); return
            if not cursor or not conn: return
            try:
                 cursor.execute(
                     "INSERT INTO proveedores (nombre_empresa, contacto, telefono, email, direccion) VALUES (%s, %s, %s, %s, %s)",
                     (nombre_empresa_input.value.strip(), contacto_input.value.strip() or None,
                      telefono_input.value.strip() or None, email_input.value.strip() or None,
                      direccion_input.value.strip() or None)
                 )
                 conn.commit(); mostrar_mensaje("Proveedor registrado exitosamente!", "success")
                 limpiar_campos_proveedor(); cargar_proveedores()
            except mysql.connector.Error as db_err: conn.rollback(); mostrar_mensaje(f"Error al registrar: {db_err}", "error")
            except Exception as ex: conn.rollback(); mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def actualizar_proveedor_action(prov_id_to_update):
             if not nombre_empresa_input.value:
                 mostrar_mensaje("El Nombre de la Empresa es obligatorio (*).", "error"); return
             if not cursor or not conn: return
             try:
                 cursor.execute(
                     "UPDATE proveedores SET nombre_empresa = %s, contacto = %s, telefono = %s, email = %s, direccion = %s WHERE id_proveedor = %s",
                     (nombre_empresa_input.value.strip(), contacto_input.value.strip() or None,
                      telefono_input.value.strip() or None, email_input.value.strip() or None,
                      direccion_input.value.strip() or None, prov_id_to_update)
                 )
                 conn.commit(); mostrar_mensaje("Proveedor actualizado exitosamente!", "success")
                 limpiar_campos_proveedor(); cargar_proveedores()
             except mysql.connector.Error as db_err: conn.rollback(); mostrar_mensaje(f"Error al actualizar: {db_err}", "error")
             except Exception as ex: conn.rollback(); mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def eliminar_proveedor_action(prov_id_to_delete):
            if not cursor or not conn: return
            try:
                cursor.execute("SELECT COUNT(*) FROM productos WHERE id_proveedor = %s", (prov_id_to_delete,))
                productos_count = cursor.fetchone()[0]
                if productos_count > 0:
                    # Option: Default is ON DELETE SET NULL for id_proveedor in productos based on schema
                    # This means deletion here will set id_proveedor to NULL for associated products
                    mostrar_mensaje(f"Proveedor tiene {productos_count} productos. Se eliminará y su ID en productos se anulará (si la BD lo permite).", "success", 5000)
                cursor.execute("DELETE FROM proveedores WHERE id_proveedor = %s", (prov_id_to_delete,))
                conn.commit(); mostrar_mensaje("Proveedor eliminado exitosamente!", "success")
                if proveedor_id_para_editar.current == prov_id_to_delete: limpiar_campos_proveedor()
                cargar_proveedores()
            except mysql.connector.Error as db_err: conn.rollback(); mostrar_mensaje(f"Error al eliminar proveedor: {db_err}", "error")
            except Exception as ex: conn.rollback(); mostrar_mensaje(f"Error inesperado: {ex}", "error")

        action_button = ft.ElevatedButton(
            text="Registrar Proveedor", on_click=registrar_proveedor_action, icon=ft.icons.BUSINESS_CENTER,
            bgcolor=ft.colors.GREEN_ACCENT_700, color=ft.colors.WHITE, height=40,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        cancelar_button = ft.OutlinedButton(
            "Cancelar Edición", on_click=lambda e: limpiar_campos_proveedor(), icon=ft.icons.CANCEL_OUTLINED, visible=False,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), height=40
         )
        cargar_proveedores()
        return ft.Column(
             [
                 ft.Text("Gestión de Proveedores", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                 ft.Divider(height=10, color=ft.colors.GREY_400),
                  ft.Row(
                      [
                          ft.Column([nombre_empresa_input, contacto_input, telefono_input], spacing=10, expand=1),
                          ft.Column([email_input, direccion_input], spacing=10, expand=1),
                      ],
                     alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START, spacing=20
                  ),
                 ft.Row([action_button, cancelar_button], alignment=ft.MainAxisAlignment.END, spacing=10),
                 ft.Divider(height=20, color=ft.colors.GREY_400),
                 ft.Text("Proveedores Registrados:", size=18, weight=ft.FontWeight.W_600, color=ft.colors.BLUE_GREY_700),
                 ft.Container(content=proveedores_container, expand=True, padding=ft.padding.only(top=5)),
             ],
             spacing=15, alignment=ft.MainAxisAlignment.START, expand=True
         )

    # --- Function to Create Productos View ---
    def crear_vista_productos():
        # Define TextFields
        nombre_input = ft.TextField(label="Nombre*", width=250, color=ft.colors.BLACK87)
        descripcion_input = ft.TextField(label="Descripción", width=250, hint_text="Opcional", color=ft.colors.BLACK87)
        marca_input = ft.TextField(label="Marca", width=250, hint_text="Opcional", color=ft.colors.BLACK87)
        categoria_input = ft.TextField(label="Categoría", width=250, hint_text="Opcional", color=ft.colors.BLACK87)
        talla_input = ft.TextField(label="Talla*", width=250, color=ft.colors.BLACK87, input_filter=ft.InputFilter(r'[0-9\.]'))
        color_input = ft.TextField(label="Color", width=250, hint_text="Opcional", color=ft.colors.BLACK87)
        stock_input = ft.TextField(label="Stock*", width=250, color=ft.colors.BLACK87, input_filter=ft.InputFilter(r'[0-9]'))
        precio_input = ft.TextField(label="Precio*", width=250, color=ft.colors.BLACK87, input_filter=ft.InputFilter(r'[0-9\.]'), prefix_text="$")
        id_proveedor_input = ft.TextField(label="ID Proveedor", width=250, hint_text="Opcional (número)", color=ft.colors.BLACK87, input_filter=ft.InputFilter(r'[0-9]'))
        qr_input = ft.TextField(label="QR*", width=250, color=ft.colors.BLACK87, max_length=13)

        productos_container = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=5)
        producto_id_para_editar = ft.Ref[int]()

        def limpiar_campos_producto():
            for field in [nombre_input, descripcion_input, marca_input, categoria_input, talla_input, color_input, stock_input, precio_input, id_proveedor_input, qr_input]:
                field.value = ""
            producto_id_para_editar.current = None
            action_button.text = "Registrar Producto"
            action_button.icon = ft.icons.ADD_SHOPPING_CART
            action_button.on_click = registrar_producto_action
            action_button.bgcolor = ft.colors.GREEN_ACCENT_700
            cancelar_button.visible = False
            page.update()

        def cargar_productos():
            if not cursor or not conn:
                productos_container.controls.clear()
                productos_container.controls.append(ft.Text("Error de base de datos no disponible para cargar productos.", color=ft.colors.RED))
                page.update()
                return
            productos_container.controls.clear()
            try:
                cursor.execute("SELECT p.id_producto, p.nombre, p.categoria, p.stock, p.precio, p.qr, pr.nombre_empresa FROM productos p LEFT JOIN proveedores pr ON p.id_proveedor = pr.id_proveedor ORDER BY p.nombre")
                productos = cursor.fetchall()
                if not productos:
                     productos_container.controls.append(ft.Text("No hay productos registrados.", color=ft.colors.GREY_700, style=ft.TextStyle(italic=True)))
                else:
                    for prod in productos:
                        prod_id = prod[0] # id_producto
                        precio_val = prod[4] # precio
                        precio_formatted = f"${precio_val:,.2f}" if isinstance(precio_val, (int, float, Decimal)) else "N/A"
                        proveedor_nombre = prod[6] if prod[6] else "Sin Proveedor"
                        productos_container.controls.append(
                             ft.Container(
                                padding=ft.padding.symmetric(vertical=3, horizontal=5),
                                content= ft.Row(
                                    [
                                        ft.Text(f"{prod[1]} ({prod[2] or 'N/A'}) - Stock: {prod[3]} - QR: {prod[5]}\nProveedor: {proveedor_nombre} - {precio_formatted}", expand=True, color=ft.colors.BLACK87),
                                         ft.IconButton(ft.icons.EDIT_NOTE, tooltip="Editar Producto",
                                            on_click=lambda e, id_edit=prod_id: cargar_datos_producto_para_editar(id_edit),
                                            icon_color=ft.colors.BLUE_ACCENT_700, icon_size=20),
                                        ft.IconButton(ft.icons.DELETE_FOREVER, tooltip="Eliminar Producto",
                                            on_click=lambda e, id_del=prod_id: eliminar_producto_action(id_del),
                                            icon_color=ft.colors.RED_ACCENT_700, icon_size=20),
                                    ],
                                     alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            )
                        )
                page.update()
            except mysql.connector.Error as db_err: mostrar_mensaje(f"Error al cargar productos: {db_err}", "error")
            except Exception as ex: mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def cargar_datos_producto_para_editar(prod_id_val_edit):
            if not cursor: return
            try:
                cursor.execute("SELECT nombre, descripcion, marca, categoria, talla, color, stock, precio, id_proveedor, qr FROM productos WHERE id_producto = %s", (prod_id_val_edit,))
                producto = cursor.fetchone()
                if producto:
                    nombre_input.value, descripcion_input.value, marca_input.value, categoria_input.value = producto[0], producto[1] or "", producto[2] or "", producto[3] or ""
                    talla_input.value, color_input.value = str(producto[4]) if producto[4] is not None else "", producto[5] or ""
                    stock_input.value, precio_input.value = str(producto[6]) if producto[6] is not None else "", str(producto[7]) if producto[7] is not None else ""
                    id_proveedor_input.value, qr_input.value = str(producto[8]) if producto[8] is not None else "", producto[9] or ""
                    producto_id_para_editar.current = prod_id_val_edit
                    action_button.text = "Actualizar Producto"
                    action_button.icon = ft.icons.UPDATE
                    action_button.on_click = lambda e: actualizar_producto_action(prod_id_val_edit)
                    action_button.bgcolor = ft.colors.ORANGE_ACCENT_700
                    cancelar_button.visible = True
                    page.update()
                else: mostrar_mensaje("Producto no encontrado.", "error")
            except mysql.connector.Error as db_err: mostrar_mensaje(f"Error al cargar producto: {db_err}", "error")
            except Exception as ex: mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def _validar_y_preparar_datos_producto():
            nombre = nombre_input.value.strip()
            talla_str = talla_input.value.strip()
            stock_str = stock_input.value.strip()
            precio_str = precio_input.value.strip()
            qr_val = qr_input.value.strip()

            if not (nombre and talla_str and stock_str and precio_str and qr_val):
                mostrar_mensaje("Completa Nombre, Talla, Stock, Precio, QR (*).", "error"); return None
            try:
                talla = Decimal(talla_str).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP) # Example: one decimal place for talla
                stock = int(stock_str)
                precio = Decimal(precio_str).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if stock < 0 or precio < 0 or talla < 0 :
                    mostrar_mensaje("Talla, Stock y Precio no pueden ser negativos.", "error"); return None
            except ValueError: mostrar_mensaje("Talla, Stock o Precio tienen formato numérico inválido.", "error"); return None

            if len(qr_val) > 13: mostrar_mensaje("QR no debe exceder 13 caracteres.", "error"); return None

            id_proveedor = None
            id_proveedor_str = id_proveedor_input.value.strip()
            if id_proveedor_str:
                try:
                    id_proveedor = int(id_proveedor_str)
                    if cursor: # Check proveedor existence only if cursor is available
                        cursor.execute("SELECT COUNT(*) FROM proveedores WHERE id_proveedor = %s", (id_proveedor,))
                        if cursor.fetchone()[0] == 0:
                            mostrar_mensaje(f"ID de Proveedor {id_proveedor} no existe.", "error"); return None
                except ValueError: mostrar_mensaje("ID de Proveedor debe ser un número.", "error"); return None
                except mysql.connector.Error as db_err: mostrar_mensaje(f"Error verificando proveedor: {db_err}", "error"); return None

            return (nombre, descripcion_input.value.strip() or None, marca_input.value.strip() or None,
                    categoria_input.value.strip() or None, talla, color_input.value.strip() or None,
                    stock, precio, id_proveedor, qr_val)

        def registrar_producto_action(e):
            if not cursor or not conn: return
            datos_producto = _validar_y_preparar_datos_producto()
            if not datos_producto: return

            try:
                 cursor.execute(
                     "INSERT INTO productos (nombre, descripcion, marca, categoria, talla, color, stock, precio, id_proveedor, qr) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                     datos_producto
                 )
                 conn.commit(); mostrar_mensaje("Producto registrado exitosamente!", "success")
                 limpiar_campos_producto(); cargar_productos()
            except mysql.connector.Error as db_err: conn.rollback(); mostrar_mensaje(f"Error al registrar: {db_err}", "error")
            except Exception as ex: conn.rollback(); mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def actualizar_producto_action(prod_id_to_update):
             if not cursor or not conn: return
             datos_producto = _validar_y_preparar_datos_producto()
             if not datos_producto: return

             try:
                 cursor.execute(
                     "UPDATE productos SET nombre=%s, descripcion=%s, marca=%s, categoria=%s, talla=%s, color=%s, stock=%s, precio=%s, id_proveedor=%s, qr=%s WHERE id_producto=%s",
                     (*datos_producto, prod_id_to_update)
                 )
                 conn.commit(); mostrar_mensaje("Producto actualizado exitosamente!", "success")
                 limpiar_campos_producto(); cargar_productos()
             except mysql.connector.Error as db_err: conn.rollback(); mostrar_mensaje(f"Error al actualizar: {db_err}", "error")
             except Exception as ex: conn.rollback(); mostrar_mensaje(f"Error inesperado: {ex}", "error")

        def eliminar_producto_action(prod_id_to_delete):
            if not cursor or not conn: return
            try:
                cursor.execute("SELECT COUNT(*) FROM detalles_venta WHERE id_producto = %s", (prod_id_to_delete,))
                ventas_count = cursor.fetchone()[0]
                # cursor.execute("SELECT COUNT(*) FROM detalles_pedido WHERE id_producto = %s", (prod_id_to_delete,)) # Uncomment if pedidos table exists
                # pedidos_count = cursor.fetchone()[0]
                pedidos_count = 0 # Assuming no pedidos table for now

                if ventas_count > 0 or pedidos_count > 0:
                    mostrar_mensaje(f"No se puede eliminar, está en {ventas_count} ventas y {pedidos_count} pedidos.", "error")
                    return
                cursor.execute("DELETE FROM productos WHERE id_producto = %s", (prod_id_to_delete,))
                conn.commit(); mostrar_mensaje("Producto eliminado exitosamente!", "success")
                if producto_id_para_editar.current == prod_id_to_delete: limpiar_campos_producto()
                cargar_productos()
            except mysql.connector.Error as db_err: conn.rollback(); mostrar_mensaje(f"Error al eliminar: {db_err}", "error")
            except Exception as ex: conn.rollback(); mostrar_mensaje(f"Error inesperado: {ex}", "error")

        action_button = ft.ElevatedButton(
            text="Registrar Producto", on_click=registrar_producto_action, icon=ft.icons.ADD_SHOPPING_CART,
            bgcolor=ft.colors.GREEN_ACCENT_700, color=ft.colors.WHITE, height=40,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        cancelar_button = ft.OutlinedButton(
            "Cancelar Edición", on_click=lambda e: limpiar_campos_producto(), icon=ft.icons.CANCEL_OUTLINED, visible=False,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), height=40
         )
        cargar_productos()
        return ft.Column(
            [
                 ft.Text("Gestión de Productos", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                 ft.Divider(height=10, color=ft.colors.GREY_400),
                 ft.Row(
                     [
                         ft.Column([nombre_input, descripcion_input, marca_input, categoria_input, talla_input], spacing=10, expand=1),
                         ft.Column([color_input, stock_input, precio_input, id_proveedor_input, qr_input], spacing=10, expand=1),
                     ],
                     alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START, spacing=20
                 ),
                 ft.Row([action_button, cancelar_button], alignment=ft.MainAxisAlignment.END, spacing=10),
                 ft.Divider(height=20, color=ft.colors.GREY_400),
                 ft.Text("Productos Registrados:", size=18, weight=ft.FontWeight.W_600, color=ft.colors.BLUE_GREY_700),
                 ft.Container(content=productos_container, expand=True, padding=ft.padding.only(top=5)),
             ],
             spacing=15, alignment=ft.MainAxisAlignment.START, expand=True
         )

    # --- Function to Create Ventas View ---
    def crear_vista_ventas():
        venta_output_container = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=10)
        status_text_venta = ft.Text(value="", color=ft.colors.RED_ACCENT_700, weight=ft.FontWeight.BOLD, visible=False)

        # Input fields for new sale
        cliente_id_input_venta = ft.TextField(label="ID Cliente (opcional)", width=200, input_filter=ft.InputFilter(r'[0-9]'))
        empleado_id_input_venta = ft.TextField(label="ID Empleado (opcional)", width=200, input_filter=ft.InputFilter(r'[0-9]'))
        # For simplicity, current sale logic handles one product per transaction via UI.
        # To handle multiple products, UI needs a list/table for items to be added to the sale.
        qr_input_venta = ft.TextField(label="QR Producto*", width=220, autofocus=True, max_length=13)
        cantidad_input_venta = ft.TextField(label="Cantidad*", keyboard_type=ft.KeyboardType.NUMBER, width=150, input_filter=ft.InputFilter(r'[0-9]'))
        precio_input_venta = ft.TextField(label="Precio Unitario*", keyboard_type=ft.KeyboardType.NUMBER, width=180, input_filter=ft.InputFilter(r'[0-9\.]'), prefix_text="$")

        def _limpiar_campos_venta():
            qr_input_venta.value = ""
            cantidad_input_venta.value = ""
            precio_input_venta.value = ""
            # Optionally clear cliente/empleado or leave for next sale
            # cliente_id_input_venta.value = ""
            # empleado_id_input_venta.value = ""
            status_text_venta.value = ""
            status_text_venta.visible = False
            qr_input_venta.focus()
            page.update()

        def _cargar_historial_ventas_ui(e=None):
            if not cursor or not conn:
                venta_output_container.controls.clear()
                venta_output_container.controls.append(ft.Text("Error de base de datos no disponible para cargar ventas.", color=ft.colors.RED))
                page.update()
                return

            venta_output_container.controls.clear()
            try:
                lista_ventas = _obtener_ventas_db(conn, cursor) # Use the adapted DB function
                if not lista_ventas:
                    venta_output_container.controls.append(ft.Text("No hay ventas registradas.", color=ft.colors.GREY_700, style=ft.TextStyle(italic=True)))
                for v_data in lista_ventas:
                    detalles_str_list = []
                    for d_data in v_data["detalles"]:
                        precio_unit_fmt = f"${d_data['precio_unitario']:.2f}" if isinstance(d_data['precio_unitario'], (Decimal, float)) else "N/A"
                        subtotal_fmt = f"${d_data['subtotal']:.2f}" if isinstance(d_data['subtotal'], (Decimal, float)) else "N/A"
                        detalles_str_list.append(
                            f"  • {d_data['nombre_producto']} x{d_data['cantidad']} @ {precio_unit_fmt} = {subtotal_fmt}"
                        )
                    detalles_str = "\n".join(detalles_str_list) if detalles_str_list else "  (Sin detalles disponibles)"

                    cliente_nombre_completo = f"{v_data['cliente_nombre'] or ''} {v_data['cliente_apellido'] or ''}".strip()
                    cliente_display = cliente_nombre_completo if cliente_nombre_completo else "N/A"

                    empleado_nombre_completo = f"{v_data['empleado_nombre'] or ''} {v_data['empleado_apellido'] or ''}".strip()
                    empleado_display = empleado_nombre_completo if empleado_nombre_completo else "N/A"
                    
                    fecha_venta_dt = v_data['fecha_venta']
                    fecha_venta_formateada = fecha_venta_dt.strftime("%d/%m/%Y %I:%M %p") if isinstance(fecha_venta_dt, datetime) else "Fecha N/A"
                    total_venta_fmt = f"${v_data['total_venta']:.2f}" if isinstance(v_data['total_venta'], (Decimal, float)) else "N/A"

                    venta_output_container.controls.append(
                        ft.Card(
                            elevation=3, # Slightly more elevation
                            margin=ft.margin.symmetric(vertical=5),
                            content=ft.Container(
                                padding=15, # More padding
                                border_radius=8,
                                bgcolor=ft.colors.WHITE,
                                content=ft.Column([
                                    ft.Text(f"Venta #{v_data['id_venta']}", weight=ft.FontWeight.BOLD, size=17, color=ft.colors.TEAL_700),
                                    ft.Text(f"Cliente: {cliente_display}", size=13, color=ft.colors.BLACK),
                                    ft.Text(f"Empleado: {empleado_display}", size=13, color=ft.colors.BLACK),
                                    ft.Text(f"Fecha: {fecha_venta_formateada}", size=13, color=ft.colors.BLACK),
                                    ft.Text(f"Total: {total_venta_fmt}", weight=ft.FontWeight.BOLD, size=15, color=ft.colors.GREEN_700),
                                    ft.Divider(height=5, thickness=0.5),
                                    ft.Text("Detalles:", weight=ft.FontWeight.W_600, size=14, color=ft.colors.TEAL_700), # Corrected here
                                    ft.Text(detalles_str, size=13, color=ft.colors.BLACK)
                                ], spacing=4) # Reduced spacing inside card column
                            )
                        )
                    )
            except mysql.connector.Error as db_err:
                mostrar_mensaje(f"Error al cargar historial de ventas: {db_err}", "error")
            except Exception as ex:
                mostrar_mensaje(f"Error inesperado al cargar historial: {ex}", "error")
            page.update()

        def _realizar_venta_click_handler(e):
            if not cursor or not conn:
                mostrar_mensaje("Error de base de datos no disponible para registrar venta.", "error"); return

            status_text_venta.value = ""; status_text_venta.visible = False
            page.update() # Update to hide previous message immediately
            
            try:
                id_cliente_str = cliente_id_input_venta.value.strip()
                id_empleado_str = empleado_id_input_venta.value.strip()
                qr_val = qr_input_venta.value.strip()
                cantidad_str = cantidad_input_venta.value.strip()
                precio_str = precio_input_venta.value.strip()

                if not qr_val: raise ValueError("El QR del producto es obligatorio.")
                if not cantidad_str or not cantidad_str.isdigit() or int(cantidad_str) <= 0:
                    raise ValueError("La cantidad debe ser un número entero positivo.")
                if not precio_str: raise ValueError("El precio unitario es obligatorio.")

                precio_decimal = Decimal(precio_str).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if precio_decimal < 0: raise ValueError("El precio unitario no puede ser negativo.")

                id_cliente = int(id_cliente_str) if id_cliente_str else None
                id_empleado = int(id_empleado_str) if id_empleado_str else None

                # Verify existence of client and employee if IDs are provided
                if id_cliente is not None:
                    cursor.execute("SELECT COUNT(*) FROM clientes WHERE id_cliente = %s", (id_cliente,))
                    if cursor.fetchone()[0] == 0: raise ValueError(f"Cliente con ID {id_cliente} no encontrado.")
                if id_empleado is not None:
                    cursor.execute("SELECT COUNT(*) FROM empleados WHERE id_empleado = %s", (id_empleado,))
                    if cursor.fetchone()[0] == 0: raise ValueError(f"Empleado con ID {id_empleado} no encontrado.")

                productos_data = [{"qr": qr_val, "cantidad": int(cantidad_str), "precio_unitario": precio_decimal}]

                id_venta = _registrar_venta_db(conn, cursor, id_cliente, id_empleado, productos_data)
                mostrar_mensaje(f"Venta #{id_venta} registrada exitosamente.", "success")
                _limpiar_campos_venta()
                _cargar_historial_ventas_ui()

            except ValueError as ve:
                status_text_venta.value = f"Error de validación: {ve}"
                status_text_venta.color = ft.colors.AMBER_ACCENT_700
                status_text_venta.visible = True
            except mysql.connector.Error as db_err:
                # Specific check for foreign key constraint on id_producto (related to QR not found via _registrar_venta_db logic)
                # or other database related errors from the transaction.
                if "Producto con QR" in str(db_err) or "Stock insuficiente" in str(db_err): # Error message from _registrar_venta_db
                    status_text_venta.value = f"Error: {db_err}"
                elif db_err.errno == 1452 and "FOREIGN KEY (`id_cliente`) REFERENCES `clientes`" in str(db_err):
                     status_text_venta.value = f"Error: Cliente con ID '{id_cliente_str}' no existe."
                elif db_err.errno == 1452 and "FOREIGN KEY (`id_empleado`) REFERENCES `empleados`" in str(db_err):
                     status_text_venta.value = f"Error: Empleado con ID '{id_empleado_str}' no existe."
                else: # Generic DB error
                    status_text_venta.value = f"Error de base de datos: {db_err}"
                status_text_venta.color = ft.colors.RED_ACCENT_700
                status_text_venta.visible = True
            except Exception as ex: # Catch other exceptions like Decimal conversion errors not caught by ValueError
                status_text_venta.value = f"Error inesperado: {ex}"
                status_text_venta.color = ft.colors.RED_ACCENT_700
                status_text_venta.visible = True
            page.update()

        # Initial load of sales history
        _cargar_historial_ventas_ui()

        return ft.Column(
            [
                ft.Text("Registrar Nueva Venta", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                ft.Row(
                    [cliente_id_input_venta, empleado_id_input_venta],
                    spacing=15, alignment=ft.MainAxisAlignment.START
                ),
                ft.Row(
                    [qr_input_venta, cantidad_input_venta, precio_input_venta],
                    spacing=15, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.END
                ),
                status_text_venta,
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Registrar Venta", on_click=_realizar_venta_click_handler, icon=ft.icons.POINT_OF_SALE, # Changed Icon
                            bgcolor=ft.colors.TEAL_ACCENT_700, color=ft.colors.WHITE, height=40, # Teal color for sale
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        ft.OutlinedButton(
                            "Limpiar", on_click=lambda e: _limpiar_campos_venta(), icon=ft.icons.CLEAR_ALL, height=40,
                             style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START, spacing=10
                ),
                ft.Divider(height=20, thickness=1, color=ft.colors.GREY_400),
                ft.Text("Historial de Ventas", size=20, weight=ft.FontWeight.W_600, color=ft.colors.BLUE_GREY_700), # Slightly smaller title, Corrected Here
                ft.Container(content=venta_output_container, expand=True, padding=ft.padding.only(top=5))
            ],
            spacing=15, alignment=ft.MainAxisAlignment.START, expand=True
        )

    # --- Create Tabs ---
    tabs_list = []
    if conn and cursor: # Only create tabs if DB connection is successful
        tabs_list = [
            ft.Tab(text="Clientes", icon=ft.icons.ACCOUNT_CIRCLE, content=ft.Container(content=crear_vista_clientes(), padding=ft.padding.all(20))),
            ft.Tab(text="Empleados", icon=ft.icons.PEOPLE_ALT, content=ft.Container(content=crear_vista_empleados(), padding=ft.padding.all(20))),
            ft.Tab(text="Proveedores", icon=ft.icons.STOREFRONT, content=ft.Container(content=crear_vista_proveedores(), padding=ft.padding.all(20))),
            ft.Tab(text="Productos", icon=ft.icons.CATEGORY, content=ft.Container(content=crear_vista_productos(), padding=ft.padding.all(20))),
            ft.Tab(text="Ventas", icon=ft.icons.SHOPPING_CART_CHECKOUT, content=ft.Container(content=crear_vista_ventas(), padding=ft.padding.all(20))),
        ]
    else: # Fallback if DB connection failed
        error_content = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.ERROR_OUTLINE, color=ft.colors.RED_700, size=50),
                    ft.Text("Fallo la conexión a la Base de Datos.", size=22, color=ft.colors.RED_700, weight=ft.FontWeight.BOLD),
                    ft.Text("La aplicación no puede funcionar correctamente. Por favor, verifique la configuración de la base de datos y reinicie la aplicación.",
                            size=16, color=ft.colors.BLACK54, text_align=ft.TextAlign.CENTER)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
            ),
            alignment=ft.alignment.center,
            expand=True
        )
        tabs_list = [ft.Tab(text="Error", icon=ft.icons.ERROR, content=error_content)]


    tabs_control = ft.Tabs(
        selected_index=0,
        animation_duration=250,
        tabs=tabs_list,
        expand=True,
        label_color=ft.colors.TEAL_ACCENT_700, # Color for selected tab label
        unselected_label_color=ft.colors.BLACK54,
        indicator_color=ft.colors.TEAL_ACCENT_700, # Color for the indicator line
    )
    page.add(tabs_control)


    # --- Close connection when app closes ---
    def cerrar_conexion(e): # Parameter 'e' is typically passed by Flet for event handlers
         if cursor:
             cursor.close()
             print("Database cursor closed.")
         if conn and conn.is_connected():
             conn.close()
             print("Database connection closed.")

    page.on_disconnect = cerrar_conexion # Use on_disconnect for graceful closing
    page.update() # Initial page update

# --- Run the Flet App ---
if __name__ == "__main__":
     ft.app(target=main)