# Docker Compose

## Requirements

The task requires a minimal Docker infrastructure with HDFS or MinIO for storage, Kafka for real-time messaging and NiFi for data ingestion. All three are covered:

- HDFS: `namenode` and `datanode` services (Hadoop 3.2.1)
- Kafka: `kafka` service (KRaft mode, no Zookeeper)
- NiFi: `nifi` service (version 2.4.0 with Hadoop extensions)

## Network

All services share the `data_pipeline` bridge network, so inside the network they reach each other by service name (for example, NiFi reaches HDFS at `namenode:9000`).
The `ports` section (format `host_port:container_port`) exposes a port on the host machine, for access from a browser or a local Python script.

## Services

### namenode

The HDFS master node. It stores metadata (which files and folders exist and on which datanode their blocks are), not the file contents.

- Port 9870: web UI at `http://localhost:9870`, where files can be browsed under Utilities, Browse the file system.
- Port 9000: RPC port used by clients such as NiFi and Spark.
- The bde2020 image turns environment variables into XML configuration:
  - `CORE_CONF_fs_defaultFS` becomes `fs.defaultFS` in `core-site.xml`.
  - `HDFS_CONF_dfs_replication: 1` keeps one copy of each block, since there is only one datanode (the default is 3).
  - `..._ip___hostname_check: false` disables the IP/hostname check, which fails inside Docker. Triple underscore is translated to a dash.
- The `namenode_data` volume keeps metadata across container restarts.

### datanode

Stores the actual file blocks in the `datanode_data` volume.

- `depends_on` and `SERVICE_PRECONDITION: namenode:9870` make it wait for the namenode before registering.
- Port 9864: datanode web UI and the port clients use to read and write data directly.

### nifi

Built from [Dockerfile.nifi](../../Dockerfile.nifi) instead of a ready image. NiFi 2.x no longer ships HDFS processors, so the Dockerfile downloads `nifi-hadoop-nar` and `nifi-hadoop-libraries-nar`, which provide `PutHDFS`, `ListHDFS` and related processors.

- Port 8443: UI at `https://localhost:8443/nifi`.
- Credentials are read from `.env`. The `${NIFI_USERNAME:?...}` syntax makes compose refuse to start if the variable is missing.
- Volumes:
  - `./raw` is mounted read-only as the input folder for the local file to HDFS flow.
  - `./infrastructure/hadoop-conf` is mounted read-only and holds `core-site.xml` and `hdfs-site.xml`, which are referenced in the "Hadoop Configuration Resources" property of `PutHDFS`.
  - `nifi_conf`, `nifi_state` and the `*_repository` volumes hold NiFi internals (flow definition, processor state, queued FlowFiles, provenance), so flows survive restarts.

### kafka

Runs in KRaft mode (`KAFKA_PROCESS_ROLES: broker,controller`), meaning a single process acts as both broker and controller and Zookeeper is not needed.

Kafka has three listeners:

- `INTERNAL` at `kafka:29092`, used by containers in the Docker network, including NiFi.
- `EXTERNAL` at `localhost:9092`, used by programs on the host, such as a Python script with `kafka-python`.
- `CONTROLLER` at port 9093, used internally by KRaft.

Two client addresses are needed because Kafka returns an "advertised" address that the client then connects to. The name `kafka` does not resolve on the host, and `localhost` inside the NiFi container points to NiFi itself.

Other settings:

- `*_REPLICATION_FACTOR: 1` and `MIN_ISR: 1` are required with a single broker, since the defaults expect three.
- `KAFKA_NUM_PARTITIONS: 1` sets the default partition count for new topics.

## Known issues

1. Kafka has no volume, so topics and messages are lost when the container is recreated (`docker compose down`). Adding `kafka_data:/var/lib/kafka/data` fixes this.
2. The `apache/kafka:latest` image is not pinned and can change on the next pull. A fixed version such as `apache/kafka:3.9.1` is safer.
3. NiFi has no `depends_on` for `namenode` and `kafka`, so flows may report errors if NiFi starts first.
4. The `./raw` mount is only needed for the local file flow, since Bluesky data arrives over WebSocket.
