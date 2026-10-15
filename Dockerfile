# Python 3.10 Base Image
FROM python:3.10-slim

# Set up working directory that will work in container
WORKDIR /app

# Copy requirements.txt and install necessary libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy python code into the container
COPY main.py .

# When container starts, run main.py
CMD ["python", "main.py"]