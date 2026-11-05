# Primera ingesta con HDFS

## Paso A1: Explorar la Fuente (MySQL)

docker exec -it mysql mysql -u sqoopuser -p'sqooppassword'

### Testeo para las tablas

- Get-Content .\workspace\espiar_db.sql | 
docker exec -it mysql mysql -u sqoopuser -psqooppassword

---
## Paso A2: Ejecutar la Ingesta Batch a HDFS

### Creado el script de python para la ingesta de archivos
---

### Acceder al bash del workspace
hdfs dfs -ls /user/iabd_admin/ingesta/ventas

---
### Usar spark-submit para ejecutar el script

- spark-submit /workspace/ingesta_pedidos.py

## Paso A3: Verificación del destino en HDFS

### Directorio y archivos

Validar la presencia del marcador _SUCCESS y del fichero de datos .csv

- docker exec -it namenode hdfs dfs -ls /user/iabd_admin/ingesta/ventas/pedidos

Inspeccionar datos en el Datalake (10 filas)

- docker exec -it namenode bash -c "hdfs dfs -cat /user/iabd_admin/ingesta/ventas/pedidos/part-*.csv | head -n 10"

--- 
# Parte B
## Paso B1: Diseño del Agente (Source, Channel, Sink)

Puramente informativo, checkear documento

## Paso B2: Crear el Fichero de Configuración

Directorio donde configuraremos Flume

- docker exec -it workspace bash 

---

Crea la carpeta para la configuración y la carpeta que Flume estará vigilando (spoolDir)

- mkdir -p /workspace/flume_configs /workspace/flume_ingest

---

Crear el weblogs.conf

- `cat << 'EOF' > /workspace/flume_configs/weblogs.conf

(Pegar lo que hemos visto en el documento)

---

## Paso B3: Preparar el Directorio de Ingesta

Confirmar que existe

- docker exec -it workspace ls -ld /workspace/flume_ingest

---

## Paso B4: Lanzar el Agente de Flume

Lanzar el agente en el workspace

- docker exec -it `
  -e JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 `
  -e FLUME_HOME=/opt/apache-flume-1.11.0-bin `
  -e HADOOP_USER_NAME=hadoop `
  workspace flume-ng agent `
  --conf /workspace/flume_configs/ `
  --conf-file /workspace/flume_configs/weblogs.conf `
  --name agent `
  -Dflume.root.logger=INFO,console

Nota: No deberia ser tan complicado, pero parece funcionar