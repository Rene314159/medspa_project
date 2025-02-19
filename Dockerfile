FROM python:3.10-slim

WORKDIR /app

# Install system dependencies needed for psycopg2
RUN apt-get update && \
    apt-get install -y libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy wait-for-it.sh into the container and make it executable
COPY wait-for-it.sh /app/wait-for-it.sh
RUN chmod +x /app/wait-for-it.sh

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project code into the container
COPY . /app/

# Expose the port for Django
EXPOSE 8000

# Use wait-for-it to delay starting Django until the db is ready
CMD ["/app/wait-for-it.sh", "db:5432", "--", "python", "manage.py", "runserver", "0.0.0.0:8000"]
