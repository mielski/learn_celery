# Use the official Python image
FROM python:3.9-alpine

RUN pip install -U pip

# Set the working directory inside the container
WORKDIR /app

# Copy the Pipfile and Pipfile.lock to the container
COPY Pipfile Pipfile.lock ./

# Install dependencies from the Pipfile
RUN pip install pipenv && pipenv install --deploy --ignore-pipfile --system

# Copy the Python application code
COPY src ./

# Expose the port for the Celery worker
EXPOSE 5050

# Set to use with minimal privilages
USER nobody

# Start the Celery worker and the Python app
CMD ls && celery -A app worker --loglevel=info