FROM python:3.11-slim


# Install postgresql-client for pg_isready and libpq for the app drivers
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /vortex
# we use /app because we dont know the default folder
# what if defaul folder was user/bin
# if we did app/ then it would be usr/bin/app
# but / means stat at root level
# so /app -> create app folder at root level
# and /app/ is same as /app
    

# install dependanacies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# copy only the fastapi code
# imp fix -> all our code uses imports like app.xyz
# so we need an app folder or we wil have to change the entire codebase
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./alembic.ini .
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]

CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" ]