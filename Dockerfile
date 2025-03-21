# Set the python version as a build-time argument
# with Python 3.12 as the default
ARG PYTHON_VERSION=3.12-slim-bullseye
FROM python:${PYTHON_VERSION}

# Create a virtual environment
RUN python -m venv /opt/venv

# Set the virtual environment as the current location
ENV PATH=/opt/venv/bin:$PATH

# Upgrade pip
RUN pip install --upgrade pip

# Set Python-related environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install OS dependencies for our mini VM
RUN apt-get update && apt-get install -y \
    # for postgres
    libpq-dev \
    # for Pillow
    libjpeg-dev \
    # for CairoSVG
    libcairo2 \
    # other
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create the mini VM's code directory
RUN mkdir -p /code

# Set the working directory to that same code directory
WORKDIR /code

# Copy the requirements file into the container
COPY requirements.txt /tmp/requirements.txt

# Copy the project code into the container's working directory
COPY ./src /code

# Install the Python project requirements
RUN pip install -r /tmp/requirements.txt

# Set environment variables for the Django app (build-time and runtime)
ARG DJANGO_SECRET_KEY
ENV DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}

ARG DJANGO_DEBUG=0
ENV DJANGO_DEBUG=${DJANGO_DEBUG}

ARG DATABASE_URL
ENV DATABASE_URL=${DATABASE_URL}

ARG COINPAYMENTS_PUBLIC_KEY
ENV COINPAYMENTS_PUBLIC_KEY=${COINPAYMENTS_PUBLIC_KEY}

ARG COINPAYMENTS_PRIVATE_KEY
ENV COINPAYMENTS_PRIVATE_KEY=${COINPAYMENTS_PRIVATE_KEY}

ARG STRIPE_SECRET_KEY
ENV STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}

ARG STRIPE_PUBLISHABLE_KEY
ENV STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY}

ARG EMAIL_HOST_USER
ENV EMAIL_HOST_USER=${EMAIL_HOST_USER}

ARG EMAIL_HOST_PASSWORD
ENV EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}

ARG PUSHOVER_API_TOKEN
ENV PUSHOVER_API_TOKEN=${PUSHOVER_API_TOKEN}

ARG EXCHANGE_RATE_API_KEY
ENV EXCHANGE_RATE_API_KEY=${EXCHANGE_RATE_API_KEY}

ARG SUPABASE_URL
ENV SUPABASE_URL=${SUPABASE_URL}

ARG SUPABASE_API_KEY
ENV SUPABASE_API_KEY=${SUPABASE_API_KEY}

# Database isn't available during build
# Run any other commands that do not need the database
# such as:
RUN python manage.py vendor_pull
RUN python manage.py collectstatic --noinput
RUN python manage.py compress --force

# Set the Django default project name
ARG PROJ_NAME="discbot"

# Create a bash script to run the Django project
# This script will execute at runtime when
# the container starts and the database is available
RUN printf "#!/bin/bash\n" > ./paracord_runner.sh && \
    printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./paracord_runner.sh && \
    printf "sync\n" >> ./paracord_runner.sh && \
    printf "sleep 2\n" >> ./paracord_runner.sh && \
    printf "python manage.py migrate --no-input\n" >> ./paracord_runner.sh && \
    printf "gunicorn ${PROJ_NAME}.wsgi:application --bind \"0.0.0.0:\$RUN_PORT\"\n" >> ./paracord_runner.sh

# Make the bash script executable
RUN chmod +x paracord_runner.sh

# Clean up apt cache to reduce image size
RUN apt-get remove --purge -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add a health check to ensure the app is ready
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:$RUN_PORT/ || exit 1

# Run the Django project via the runtime script
# when the container starts
CMD ./paracord_runner.sh
