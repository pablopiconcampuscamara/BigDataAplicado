FROM apache/hadoop:3.4.0
USER root
ARG FLUME_VERSION=1.11.0
RUN curl -fsSL https://archive.apache.org/dist/flume/${FLUME_VERSION}/apache-flume-${FLUME_VERSION}-bin.tar.gz | tar -xz -C /opt \
 && ln -s /opt/apache-flume-${FLUME_VERSION}-bin /opt/flume \
 && rm -f /opt/flume/lib/guava-*.jar
COPY flume-env.sh /opt/flume/conf/flume-env.sh
ENV FLUME_HOME=/opt/flume
ENV HADOOP_HOME=/opt/hadoop
ENV PATH=$PATH:/opt/flume/bin
