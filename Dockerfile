FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV HOME=/home/user
ENV APP_HOME=/home/user/app

# Set up a non-root user (Required by Hugging Face)
RUN useradd -m -u 1000 user

# Create app directory and set ownership
WORKDIR $APP_HOME
RUN chown -R user:user $APP_HOME

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Switch to the non-root user
USER user

# Install Python dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user gunicorn

# Copy project files
COPY --chown=user:user . .

# Collect static files
RUN ~/.local/bin/python manage.py collectstatic --noinput

# Expose port 7860 (Required by Hugging Face)
EXPOSE 7860

# Start Gunicorn server
CMD ["~/.local/bin/gunicorn", "agriai.wsgi:application", "--bind", "0.0.0.0:7860", "--workers", "2", "--threads", "4", "--timeout", "120"]
