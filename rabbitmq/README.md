# RabbitMQ
## Overview
RabbitMQ is a message broker that implements Advanced Message Queuing Protocol (AMQP). It is used for queuing video data in SVR.

### Queues and Exchanges
- **video_chunks** - queue for storing video chunks. Source managers send video chunks to this queue. Detection service consumes video chunks from this queue. It has a direct exchange with the same name bound to it.
- **frame_crops** - queue for storing frame crops. Detection service sends frame crops to this queue. Encoder service consumes frame crops from this queue. It has a direct exchange with the same name bound to it.

### Users
- **admin** - user for managing RabbitMQ. Default password: `admin`.
- **source_manager** - user for source managers. Default password: `source_manager`.
- **ml_processing** - user for ML processor. Default password: `ml_processing`.

## Deployment
RabbitMQ does not need any special configuration. It can be used "out of the box".

RabbitMQ configuration is stored in `definitions.json` file. It contains definitions for users, virtual hosts, exchanges, queues, and bindings. It is used to configure RabbitMQ on startup. If you make any changes in rabbitmq management interface, don't forget to export the configuration and save it to `definitions.json` file.

To deploy RabbitMQ, run the following command:
```bash
docker-compose up --build -d
```

After RabbitMQ is deployed, you can access its management interface at `http://localhost:15672`. Default credentials: `admin:admin`.