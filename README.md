# Project Setup with Docker

## Running the Application

### Development Mode
To run the application in development mode with live reloading:
```bash
docker-compose watch
```

### Production Mode
To run the application in detached mode using Docker:
```bash
docker-compose up -d
```

### Configuration
All environment variables and settings can be customized in the `docker-compose.yml` file.  
To view or modify all available variables, check the `config.py` file.
