import time
import os
from pyspark.sql import SparkSession

def main():
    # Inicializar la sesión de Spark para Streaming
    spark = SparkSession.builder \
        .appName('Flume_Streaming_Sim') \
        .getOrCreate()

    # Reducir verbosidad de logs
    spark.sparkContext.setLogLevel("WARN")

    spool_dir = "/workspace/flume_ingest"
    hdfs_target = "hdfs://namenode:9000/user/iabd_admin/ingesta/weblogs"

    print(f"--> Escuchando eventos/ficheros en: {spool_dir}...")

    processed_files = set()

    while True:
        if os.path.exists(spool_dir):
            files = [f for f in os.listdir(spool_dir) if f.endswith('.txt')]
            for f in files:
                if f not in processed_files:
                    path = os.path.join(spool_dir, f)
                    print(f"--> Ingeriendo archivo local: {f} hacia HDFS...")
                    
                    df = spark.read.text(path)
                    df.write.mode('append').text(hdfs_target)
                    
                    print(f"--> [OK] Fichero ingerido en HDFS: {f}")
                    processed_files.add(f)
        
        time.sleep(2)

if __name__ == '__main__':
    main()