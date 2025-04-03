# Use the official Python 3.11 slim image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, including ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir cogs
RUN mkdir bin

# Copy the files into the container
COPY requirements.txt .
COPY cogs/*.py cogs/
COPY bin/* bin/
COPY *.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the bot
CMD ["python", "main.py"]
