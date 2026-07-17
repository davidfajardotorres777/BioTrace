from faker import Faker
import random
from datetime import datetime, timedelta
from db_models.paciente import Paciente
from db_models.muestra import Muestra
from db_models.analisis import Analisis
from db_models.clinica import Clinica
from dao import AdminDAO, BioTraceDAO, StorageDAO

fake = Faker('es_AR')

def generar_datos_prueba():
    print("Conectando y limpiando base de datos y Storage...")
    admin_dao = AdminDAO()
    storage = StorageDAO()
    
    admin_dao.col_clinicas.delete_many({})
    admin_dao.db['pacientes'].delete_many({})
    admin_dao.db['muestras'].delete_many({})
    admin_dao.db['analisis'].delete_many({})
    admin_dao.db['alertas'].delete_many({})
    
    # Crear Clínicas
    clinicas_ids = []
    for nombre in ["Genómica Central", "Hospital Italiano BioLab"]:
        c_id = admin_dao.insertar_clinica(Clinica(nombre=nombre, direccion=fake.address()))
        clinicas_ids.append(c_id)
        
    print(f"Creadas {len(clinicas_ids)} clínicas.")
    
    # Para cada clínica generar datos
    for c_id in clinicas_ids:
        dao = BioTraceDAO(clinica_id=c_id)
        print(f"Generando datos para clínica {c_id}...")
        
        # Crear bucket en MinIO
        bucket_name = f"genomic-data-{c_id.lower()}"
        storage.asegurar_bucket(bucket_name)
        
        num_pacientes = 5
        tipos_muestra = ["Sangre", "Saliva", "Tejido Tumoral", "Hisopado Nasofaríngeo"]
        tipos_analisis = ["Secuenciación WGS", "PCR Multiplex", "Panel Genético Oncológico"]
        
        for _ in range(num_pacientes):
            # Crear Paciente
            fecha_nac = fake.date_of_birth(minimum_age=18, maximum_age=90)
            paciente = Paciente(
                clinica_id=c_id,
                dni=str(fake.random_int(min=10000000, max=99999999)),
                nombre=fake.first_name(),
                apellido=fake.last_name(),
                fecha_nacimiento=datetime(fecha_nac.year, fecha_nac.month, fecha_nac.day),
                genero=random.choice(["M", "F", "X"])
            )
            p_id = dao.insertar_paciente(paciente)
            
            # Crear muestras
            for _ in range(random.randint(1, 3)):
                dias_atras = random.randint(1, 365)
                fecha_ext = datetime.utcnow() - timedelta(days=dias_atras)
                
                # Ocasionalmente forzar una temperatura mala para disparar alerta
                mala_temp = random.random() > 0.8
                temp = random.uniform(10.0, 30.0) if mala_temp else random.uniform(-80.0, 4.0)
                
                muestra = Muestra(
                    clinica_id=c_id,
                    paciente_id=p_id,
                    tipo_muestra=random.choice(tipos_muestra),
                    fecha_extraccion=fecha_ext,
                    medico_solicitante=f"Dr. {fake.last_name()}",
                    estado="Analizada",
                    temperatura_almacenamiento=temp
                )
                m_id = dao.insertar_muestra(muestra)
                
                # Crear análisis y archivo dummy en MinIO
                analisis = Analisis(
                    clinica_id=c_id,
                    muestra_id=m_id,
                    tipo_analisis=random.choice(tipos_analisis),
                    fecha_analisis=fecha_ext + timedelta(days=random.randint(1, 10)),
                    laboratorio_origen="Lab Central",
                    investigador_responsable=fake.name(),
                    metricas_calidad={"q_score": round(random.uniform(20.0, 40.0), 2)}
                )
                
                # Subir archivo dummy a MinIO
                file_name = f"{m_id}_{analisis.tipo_analisis.replace(' ', '_')}.fastq"
                dummy_content = f"@SEQ_ID\n{fake.password(length=100, special_chars=False).upper()}\n+\n!''*((((***+))%%%++)(%%%%).1***-+*''))**55CCF>>>>>>CCCCCCC65\n".encode('utf-8')
                storage.subir_archivo_bytes(bucket_name, file_name, dummy_content)
                analisis.resultados_crudos_path = f"{bucket_name}/{file_name}"
                
                dao.insertar_analisis(analisis)

    admin_dao.cerrar_conexion()
    print("Datos (MongoDB) y Archivos Físicos (MinIO) generados exitosamente.")

if __name__ == "__main__":
    generar_datos_prueba()
