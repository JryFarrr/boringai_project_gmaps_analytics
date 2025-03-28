# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app  

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 9975 for the Flask app
EXPOSE 9975

# Define environment variable for Flask
ENV FLASK_APP=boring_ai_gmaps_analytics.app
ENV FLASK_RUN_PORT=9975
ENV FLASK_RUN_HOST=0.0.0.0

# Run the application
CMD ["flask", "run"]
