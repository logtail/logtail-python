# Logtail Django Demo

This is a sample Django application that demonstrates how to integrate Logtail for structured logging in a Django project.

## Features

- Structured logging with Logtail
- Different log levels (INFO, WARNING, ERROR)
- Custom context and extra data in logs
- Exception handling and logging
- Docker support
- Django 5.1.3 with Python 3.12

## Prerequisites

- Docker
- A Better Stack account

## Setup

1. Go to Better Stack -> Telemetry -> [Sources](https://telemetry.betterstack.com/team/260195/sources/new?platform=python), and create new Python source
2. Clone this repository
3. Copy `.env.example` to `.env` and update the values:
   ```
   BETTER_STACK_SOURCE_TOKEN=your-source-token-here
   BETTER_STACK_INGESTING_HOST=your-source-ingesting-host-here
   ```

## Running with Docker

1. Build the Docker image:
   ```bash
   docker build -t logtail-django-demo .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env logtail-django-demo
   ```

3. Visit http://localhost:8000 in your browser

## Testing the Logging

The demo includes three endpoints that trigger different types of logs:

1. **Info Log** (Homepage): Logs basic request information
2. **Warning Log** (/trigger-warning/): Logs a warning with custom data
3. **Error Log** (/trigger-error/): Triggers and logs an exception

Check your Logtail dashboard to see the logged events.

## Project Structure

```
example-django/
├── demo/
│   ├── templates/
│   │   └── index.html
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   └── wsgi.py
├── .env
├── Dockerfile
├── README.md
├── manage.py
└── requirements.txt
```

## Logging Configuration

The logging configuration can be found in `settings.py`. It sets up both console and Logtail handlers with a verbose formatter.
