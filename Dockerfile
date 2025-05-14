# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
# This assumes your application code is in an 'app' directory and you have a 'run.py' at the root.
COPY ./app ./app
COPY run.py .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV PYTHONPATH=/app

# Run run.py when the container launches
# We'll use the host 0.0.0.0 to be accessible from outside the container
# Also, we'll remove reload=True for a typical production/staging build
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 