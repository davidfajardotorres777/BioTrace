"""
Interfaz gráfica de escritorio de InmoCore, construida con customtkinter.
Permite elegir la agencia (tenant) con la que se va a operar y expone
las características avanzadas del sistema: alertas automáticas,
publicación de propiedades, búsqueda semántica (ChromaDB) y búsqueda
geoespacial (`$nearSphere`).
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from dao import AdminDAO, InmoCoreDAO, VectorDAO
from db_models import Propiedad

# Premium styling
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class InmoCoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("InmoCore V3 Enterprise - Plataforma Inmobiliaria")
        self.geometry("1000x700")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Estado de sesión
        self.admin_dao = AdminDAO()
        self.agencias = list(self.admin_dao.col_agencias.find())
        self.agencia_actual = None
        self.dao = None
        self.vector_dao = VectorDAO()
        
        if not self.agencias:
            messagebox.showerror("Error", "No hay agencias en la base de datos. Ejecuta setup_db.py y seed.py primero.")
            self.destroy()
            return

        self.mostrar_login()

    def mostrar_login(self):
        for widget in self.winfo_children():
            widget.destroy()
            
        self.login_frame = ctk.CTkFrame(self, corner_radius=15, width=400, height=400)
        self.login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        ctk.CTkLabel(self.login_frame, text="INMOCORE", font=ctk.CTkFont(size=36, weight="bold"), text_color="#2ecc71").pack(pady=(40, 5))
        ctk.CTkLabel(self.login_frame, text="Sistema de Gestión Inmobiliaria Multi-tenant", font=ctk.CTkFont(size=14), text_color="gray").pack(pady=(0, 30))
        
        ctk.CTkLabel(self.login_frame, text="Seleccione su Agencia Inmobiliaria (Tenant):", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        self.combo_agencia = ctk.CTkComboBox(
            self.login_frame, 
            values=[a["nombre"] for a in self.agencias],
            width=300,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.combo_agencia.pack(pady=10)
        
        btn_login = ctk.CTkButton(
            self.login_frame, 
            text="Acceder al Sistema", 
            width=300,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.iniciar_sesion
        )
        btn_login.pack(pady=30)

    def iniciar_sesion(self):
        nombre_seleccionado = self.combo_agencia.get()
        agencia = next((a for a in self.agencias if a["nombre"] == nombre_seleccionado), None)
        if agencia:
            self.agencia_actual = agencia
            self.dao = InmoCoreDAO(agencia_id=str(agencia["_id"]))
            self.mostrar_dashboard()

    def mostrar_dashboard(self):
        for widget in self.winfo_children():
            widget.destroy()
            
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        ctk.CTkLabel(self.sidebar_frame, text="INMOCORE", font=ctk.CTkFont(size=24, weight="bold"), text_color="#2ecc71").grid(row=0, column=0, padx=20, pady=(20, 5))
        ctk.CTkLabel(self.sidebar_frame, text=f"Tenant:\n{self.agencia_actual['nombre']}", font=ctk.CTkFont(size=14), text_color="#f39c12").grid(row=1, column=0, padx=20, pady=(0, 20))
        
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.grid_columnconfigure(1, weight=1)
        
        self.tabview = ctk.CTkTabview(self.main_frame, width=800, height=600)
        self.tabview.pack(fill="both", expand=True)
        
        self.tabview.add("Publicar Propiedad")
        self.tabview.add("Alertas de Precios")
        self.tabview.add("Buscador Semántico (IA)")
        self.tabview.add("Mapa Inmobiliario (Geo)")
        
        self.construir_tab_publicar(self.tabview.tab("Publicar Propiedad"))
        self.construir_tab_alertas(self.tabview.tab("Alertas de Precios"))
        self.construir_tab_semantico(self.tabview.tab("Buscador Semántico (IA)"))
        self.construir_tab_geo(self.tabview.tab("Mapa Inmobiliario (Geo)"))
        
        ctk.CTkButton(self.sidebar_frame, text="Cerrar Sesión", fg_color="#e74c3c", hover_color="#c0392b", command=self.mostrar_login).grid(row=6, column=0, padx=20, pady=20, sticky="ew")

    def construir_tab_publicar(self, tab):
        ctk.CTkLabel(tab, text="Publicar Nueva Propiedad", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)

        form = ctk.CTkScrollableFrame(tab, width=700, height=430)
        form.pack(fill="both", expand=True, padx=10, pady=10)

        self.entry_pub_titulo = ctk.CTkEntry(form, placeholder_text="Título (Ej: Casa en Av. Libertador)", width=500, height=35)
        self.entry_pub_titulo.pack(pady=5)

        self.entry_pub_desc = ctk.CTkTextbox(form, width=500, height=80)
        self.entry_pub_desc.pack(pady=5)

        fila_tipo = ctk.CTkFrame(form, fg_color="transparent")
        fila_tipo.pack(pady=5)
        self.combo_pub_tipo = ctk.CTkComboBox(fila_tipo, values=["Casa", "Departamento", "PH", "Terreno"], width=230)
        self.combo_pub_tipo.pack(side="left", padx=5)
        self.combo_pub_operacion = ctk.CTkComboBox(fila_tipo, values=["Venta", "Alquiler"], width=230)
        self.combo_pub_operacion.pack(side="left", padx=5)

        fila_num = ctk.CTkFrame(form, fg_color="transparent")
        fila_num.pack(pady=5)
        self.entry_pub_precio = ctk.CTkEntry(fila_num, placeholder_text="Precio USD", width=150)
        self.entry_pub_precio.pack(side="left", padx=5)
        self.entry_pub_sup = ctk.CTkEntry(fila_num, placeholder_text="Superficie m2", width=150)
        self.entry_pub_sup.pack(side="left", padx=5)
        self.entry_pub_hab = ctk.CTkEntry(fila_num, placeholder_text="Habitaciones", width=150)
        self.entry_pub_hab.pack(side="left", padx=5)

        fila_geo = ctk.CTkFrame(form, fg_color="transparent")
        fila_geo.pack(pady=5)
        self.entry_pub_lat = ctk.CTkEntry(fila_geo, placeholder_text="Latitud", width=230)
        self.entry_pub_lat.pack(side="left", padx=5)
        self.entry_pub_lon = ctk.CTkEntry(fila_geo, placeholder_text="Longitud", width=230)
        self.entry_pub_lon.pack(side="left", padx=5)

        ctk.CTkButton(form, text="Publicar Propiedad", height=40, font=ctk.CTkFont(weight="bold"), command=self.publicar_propiedad).pack(pady=15)

    def publicar_propiedad(self):
        try:
            precio = float(self.entry_pub_precio.get())
            superficie = float(self.entry_pub_sup.get())
            habitaciones = int(self.entry_pub_hab.get())
            lat = float(self.entry_pub_lat.get())
            lon = float(self.entry_pub_lon.get())
        except ValueError:
            messagebox.showerror("Error", "Precio, superficie, habitaciones, latitud y longitud deben ser numéricos.")
            return

        titulo = self.entry_pub_titulo.get().strip()
        descripcion = self.entry_pub_desc.get("1.0", "end").strip()
        if not titulo or not descripcion:
            messagebox.showerror("Error", "Completá el título y la descripción.")
            return

        propiedad = Propiedad(
            agencia_id=str(self.agencia_actual["_id"]),
            titulo=titulo,
            descripcion=descripcion,
            tipo=self.combo_pub_tipo.get(),
            operacion=self.combo_pub_operacion.get(),
            precio_usd=precio,
            superficie_m2=superficie,
            habitaciones=habitaciones,
            ubicacion={"type": "Point", "coordinates": [lon, lat]}
        )
        propiedad_id = self.dao.insertar_propiedad(propiedad)
        self.vector_dao.indexar_descripcion(propiedad_id, descripcion)

        messagebox.showinfo("Éxito", "Propiedad publicada correctamente.")
        self.mostrar_dashboard()

    def construir_tab_alertas(self, tab):
        ctk.CTkLabel(tab, text="Panel de Alertas (Precios Sospechosos / Descuentos)", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        scroll = ctk.CTkScrollableFrame(tab, width=700, height=400)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        alertas = self.dao.listar_alertas()
        if not alertas:
            ctk.CTkLabel(scroll, text="No hay alertas activas en esta agencia.", text_color="gray", font=ctk.CTkFont(size=14)).pack(pady=20)
        else:
            for a in alertas:
                frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#2c3e50")
                frame.pack(fill="x", pady=5, padx=5)
                ctk.CTkLabel(frame, text=f"⚠ {a.tipo_alerta}", font=ctk.CTkFont(weight="bold", size=16), text_color="#f39c12").pack(anchor="w", padx=10, pady=(10, 0))
                ctk.CTkLabel(frame, text=a.mensaje, font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(5, 0))
                ctk.CTkButton(
                    frame, text="Marcar como resuelta", fg_color="#27ae60", hover_color="#1e8449",
                    height=28, command=lambda alerta_id=a.id: self.resolver_alerta(alerta_id)
                ).pack(anchor="w", padx=10, pady=(5, 10))

    def resolver_alerta(self, alerta_id):
        self.dao.resolver_alerta(alerta_id)
        self.mostrar_dashboard()

    def construir_tab_semantico(self, tab):
        ctk.CTkLabel(tab, text="Buscador de Propiedades (ChromaDB Vector Search)", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        frame_top = ctk.CTkFrame(tab, fg_color="transparent")
        frame_top.pack(fill="x", padx=10, pady=10)
        
        self.entry_busqueda = ctk.CTkEntry(frame_top, placeholder_text="Ej: Departamento luminoso con terraza y piscina...", width=500, height=40)
        self.entry_busqueda.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(frame_top, text="Buscar con IA", command=self.ejecutar_busqueda_semantica, height=40, font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        self.scroll_semantico = ctk.CTkScrollableFrame(tab, width=700, height=400)
        self.scroll_semantico.pack(fill="both", expand=True, padx=10, pady=10)
        
    def ejecutar_busqueda_semantica(self):
        for widget in self.scroll_semantico.winfo_children():
            widget.destroy()
            
        query = self.entry_busqueda.get().strip()
        if not query:
            return
            
        resultados = self.vector_dao.buscar_similitud(query)
        if not resultados or not resultados['ids'][0]:
            ctk.CTkLabel(self.scroll_semantico, text="No se encontraron propiedades similares.", text_color="gray").pack(pady=20)
            return
            
        for i, propiedad_id in enumerate(resultados['ids'][0]):
            propiedad = self.dao.obtener_propiedad(propiedad_id)
            if not propiedad: continue
            
            distancia = resultados['distances'][0][i]
            similitud = max(0, int((1 - distancia)*100))
            descripcion = resultados['documents'][0][i]
            
            frame = ctk.CTkFrame(self.scroll_semantico, corner_radius=10)
            frame.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(frame, text=f"{propiedad.titulo} - ${propiedad.precio_usd}", font=ctk.CTkFont(weight="bold", size=16)).pack(anchor="w", padx=10, pady=(10, 0))
            ctk.CTkLabel(frame, text=f"Match Semántico: {similitud}%", font=ctk.CTkFont(size=12), text_color="#2ecc71").pack(anchor="w", padx=10, pady=0)
            ctk.CTkLabel(frame, text=f"Descripción:\n{descripcion}", justify="left", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(5, 10))

    def construir_tab_geo(self, tab):
        ctk.CTkLabel(tab, text="Búsqueda Geoespacial de Propiedades ($nearSphere)", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        frame_top = ctk.CTkFrame(tab, fg_color="transparent")
        frame_top.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(frame_top, text="Radio (KM):", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        self.entry_radio = ctk.CTkEntry(frame_top, placeholder_text="Ej: 5", width=100, height=40)
        self.entry_radio.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(frame_top, text="Encontrar Propiedades Cercanas", command=self.ejecutar_busqueda_geo, height=40, font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        self.scroll_geo = ctk.CTkScrollableFrame(tab, width=700, height=400)
        self.scroll_geo.pack(fill="both", expand=True, padx=10, pady=10)
        
    def ejecutar_busqueda_geo(self):
        for widget in self.scroll_geo.winfo_children():
            widget.destroy()
            
        try:
            radio = float(self.entry_radio.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido para el radio.")
            return
            
        ubicacion = self.agencia_actual.get("ubicacion")
        if not ubicacion or "coordinates" not in ubicacion:
            ctk.CTkLabel(self.scroll_geo, text="La agencia actual no tiene coordenadas registradas.", text_color="red").pack(pady=20)
            return
            
        lon, lat = ubicacion["coordinates"]
        
        propiedades = self.dao.buscar_propiedades_cerca_de(lat, lon, radio)
        
        if not propiedades:
            ctk.CTkLabel(self.scroll_geo, text="No hay propiedades en ese radio.", text_color="gray").pack(pady=20)
            return
            
        for p in propiedades:
            frame = ctk.CTkFrame(self.scroll_geo, corner_radius=10)
            frame.pack(fill="x", pady=5, padx=5)
            
            p_lon, p_lat = p.ubicacion["coordinates"]
            ctk.CTkLabel(frame, text=f"{p.titulo} - ${p.precio_usd}", font=ctk.CTkFont(weight="bold", size=16)).pack(anchor="w", padx=10, pady=(10, 0))
            ctk.CTkLabel(frame, text=f"Tipo: {p.tipo} | Sup: {p.superficie_m2} m2 | Coordenadas: [{p_lon:.4f}, {p_lat:.4f}]", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(5, 10))


if __name__ == "__main__":
    app = InmoCoreApp()
    app.mainloop()
