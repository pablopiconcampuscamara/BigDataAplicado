FROM eclipse-temurin:8-jdk AS jdk

FROM apache/hadoop:3.4.0
USER root
COPY --from=jdk /opt/java/openjdk /opt/java/openjdk
COPY start-hadoop.sh /opt/start-hadoop.sh
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=/opt/java/openjdk/bin:$PATH
RUN chmod +x /opt/start-hadoop.sh
