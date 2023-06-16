# Redis Stack
## Overview
Redis is an in-memory data structure store. It is used for storing user data and image embeddings in SVR, as well as for performing approximate nearest neighbor search for image embeddings.

## Users
Redis users are defined in `users.acl` file. It contains definitions for users and their permissions. It is used to configure Redis on startup.
- **worker** - user for ML processor and Search Engine. Default password: `worker`.
- **exporter** - user for Prometheus. Default password: `exporter`.


## Deployment
Redis stack configuration is stored in `redis-stack.conf` file, redis users are defined in `users.acl` file.

To deploy Redis stack, run the following command:
```bash
bash inti.sh
docker-compose up --build -d
```

After Redis stack is deployed, you can access its management interface at `http://localhost:8001`. Default credentials: `worker:worker`.