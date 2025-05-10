# Dev flow

## Key Files to Implement

 - [x]    app.py - Main entry point for your Flask application
 - [x]    app/__init__.py - Flask application factory
 - [x]    app/api/routes.py - Define your CRUD endpoints
 - [x]    app/services/quickwit_service.py - Quickwit integration logic
 - [x]    data_pipeline/fetcher.py - PokéAPI data fetching
 - [x]    docker/Dockerfile - Container configuration
 - [ ]    kubernetes/app-deployment.yaml - Kubernetes deployment

## Development Flow

 - [x]    Start by implementing the data pipeline to fetch Pokémon data
 - [x]    Set up Quickwit integration services
 - [x]    Develop Flask CRUD API endpoints
 - [x]    Containerize the application
 - [ ]    Create Kubernetes deployment files
 - [ ]    Set up scripts for easy deployment

This structure provides a clean separation of concerns and follows best practices for a Flask
application with a data pipeline component.



## Setup test env
```bash
mkdir qwdata
docker run -d --rm -v $(pwd)/qwdata:/quickwit/qwdata -p 127.0.0.1:7280:7280 quickwit/quickwit run
```
