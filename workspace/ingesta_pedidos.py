from pyspark.sql import SparkSession

def main():
    # Inicializar la sesión de Spark incluyendo el paquete JDBC de MySQL
    spark = SparkSession.builder \
        .appName('Ingesta_MySQL_a_HDFS') \
        .config("spark.jars.packages", "mysql:mysql-connector-java:8.0.28") \
        .getOrCreate()

    # Reducir verbosidad de los logs
    spark.sparkContext.setLogLevel("WARN")

    # Configuración de parámetros de conexión a MySQL
    jdbc_url = "jdbc:mysql://mysql:3306/ventas_db"
    db_properties = {
        "user": "sqoopuser",
        "password": "sqooppassword",
        "driver": "com.mysql.cj.jdbc.Driver"
    }

    print("--> Leyendo datos desde MySQL (tabla: pedidos)...")
    
    # Leer la tabla 'pedidos' de MySQL a un DataFrame de Spark
    df_pedidos = spark.read.jdbc(
        url=jdbc_url,
        table="pedidos",
        properties=db_properties
    )

    # Definir la ruta de destino en HDFS
    hdfs_target_path = "hdfs://namenode:9000/user/iabd_admin/ingesta/ventas/pedidos"

    print(f"--> Escribiendo datos en HDFS: {hdfs_target_path}...")

    # Guardar en HDFS en formato CSV
    df_pedidos.coalesce(1) \
        .write \
        .mode('overwrite') \
        .option('header', 'true') \
        .csv(hdfs_target_path)

    print("--> ¡Ingesta completada con éxito!")

    spark.stop()

if __name__ == '__main__':
    main()