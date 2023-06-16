# Monitoring
Monitoring for SVR is done using Prometheus and Grafana.

To set up monitoring, follow these steps:
1. Deploy node exporter on all nodes that you want to monitor. Node exporter is a Prometheus exporter that exports metrics about the node. It can be simply deployed using docker compose. (`node_exporter/docker-compose.yml`) 
2. Deploy gpu exporter on all nodes from which you want to export GPU metrics. GPU exporter is a Prometheus exporter that exports metrics about the GPU. It can be simply deployed using docker compose. (`node_exporter/gpu/docker-compose.yml`)
3. Fill in `prometheus/prometheus.yml` file with the addresses of node exporters, GPU exporters, redis, rabbitmq, and ml_processing services.
4. Deploy Prometheus and Grafana using docker compose. (`docker-compose.yml`)
5. Import optional Grafana dashboards:
    - Redis - `ID: 11835`
    - NVIDIA DCGM - `ID: 12239`

After that, you can access Grafana at `http://<host>:3000` and Prometheus at `http://<host>:9090`.