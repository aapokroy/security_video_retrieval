# Security Video Retrieval
Security Video Retrieval (SVR) is a project that aims to create a natural language interface for
searching security camera footage. The project is currently in its early stages, and is not yet ready for use.

## Architecture

The project is split into two four main components:
- **Search Engine** - server-side application that stores processed data
    and provides a natural language interface for searching the data. The search
    engine is hosted on a single server, and is shared by all users. 
- **Source Manager** - client-side application that manages the security camera sources,
    captures video, stores it, and sends it to the server for processing. The source manager
    is more of a dummy application that simulates the security camera sources. Each
    user hosts their own source manager and links it to their accaunt on the search engine.
- **ML Processor** - group of stateless microservices that process the video data
    and extract information from it. The ML processor can be easily scaled horizontally
    and vertically.
- **RabbitMQ** - AMQP message broker that is used to communicate between different
    components of the system. It acts as a unified interface for all components, and
    also as a buffer for the ML processor.

![Security Video Retrieval (6)](https://github.com/TLMOS/security_video_retrieval/assets/44904798/862b16a8-53d5-41fa-afbc-3d7b750873e0)

## Installation
Each component of the system is a separate dockerized application. The easiest way to
install the system is to use docker-compose. Each component has its own docker-compose
file in its root directory. Yet, there are configuration files that need to be edited
manually before running the system. You can read more about the configuration files
in the README.md files of each component.
