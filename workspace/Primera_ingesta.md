# Primera ingesta con HDFS

## Paso A1: Explorar la Fuente (MySQL)

docker exec -it mysql mysql -u sqoopuser -p'sqooppassword'

### Testeo para las tablas

- Get-Content .\workspace\espiar_db.sql | 
docker exec -it mysql mysql -u sqoopuser -psqooppassword

---
## Paso A2: Ejecutar la Ingesta Batch a HDFS

Sqoop no viene instalado en las imágenes de este Compose. Para esta ingesta se usa el script PySpark, ejecutado desde el contenedor `workspace`. `--packages` descarga y añade el driver JDBC de MySQL al classpath de Spark:

```powershell
docker compose exec -e HADOOP_USER_NAME=hadoop workspace spark-submit --packages com.mysql:mysql-connector-j:8.0.33 /workspace/ingesta_pedidos.py
```

Se ejecuta como `hadoop` para poder escribir en el directorio HDFS creado para ese usuario. La URL JDBC usa `mysql:3306` (el nombre del servicio dentro de la red de Docker), no `localhost`. La base `ventas_db`, el usuario `sqoopuser` y las tablas deben estar creados antes de ejecutar el script.

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