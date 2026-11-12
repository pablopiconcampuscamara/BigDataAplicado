FROM continuumio/anaconda3:2024.02-1
RUN conda install -y -c conda-forge openjdk=11 \
 && conda clean -afy
ENV JAVA_HOME=/opt/conda
RUN pip install --no-cache-dir pyspark==3.4.2 kafka-python pymongo psycopg2-binary pymysql sqlalchemy hdfs
WORKDIR /opt/notebooks
EXPOSE 8888
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--ServerApp.token=", "--ServerApp.password="]
