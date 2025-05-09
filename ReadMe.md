# Dev flow

## Key Files to Implement

 -    app.py - Main entry point for your Flask application
 -    app/__init__.py - Flask application factory
 -    app/api/routes.py - Define your CRUD endpoints
 -    app/services/quickwit_service.py - Quickwit integration logic
 -    data_pipeline/fetcher.py - PokéAPI data fetching
 -    docker/Dockerfile - Container configuration
 -    kubernetes/app-deployment.yaml - Kubernetes deployment

## Development Flow

 -    Start by implementing the data pipeline to fetch Pokémon data
 -    Set up Quickwit integration services
 -    Develop Flask CRUD API endpoints
 -    Containerize the application
 -    Create Kubernetes deployment files
 -    Set up scripts for easy deployment

This structure provides a clean separation of concerns and follows best practices for a Flask
application with a data pipeline component.



## Setup test env

mkdir qwdata
docker run -d --rm -v $(pwd)/qwdata:/quickwit/qwdata -p 127.0.0.1:7280:7280 quickwit/quickwit run
