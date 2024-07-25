FROM python:3.9-slim-bullseye

# Install system dependencies for lxml and other potential build requirements

COPY app /app

WORKDIR /app

LABEL version="1.0.1"

LABEL permissions='{\
  "ExposedPorts": {\
  "80/tcp": {}\
  },\
  "HostConfig": {\
  "ExtraHosts": ["host.docker.internal:host-gateway"],\
  "PortBindings": {\
  "80/tcp": [\
  {\
  "HostPort": ""\
  }\
  ]\
  }\
  }\
  }'

LABEL company='{\
  "about": "",\
  "name": "MIT",\
  "email": "jwenger@mit.edu"\
  }'
LABEL type="example"
LABEL readme='https://raw.githubusercontent.com/jerWenger/blueos-mavlink-parser/blob/main/README.md'
LABEL links='{\
  "website": "https://github.com/jerWenger/blueos-mavlink-parser/tree/main",\
  "support": "https://github.com/jerWenger/blueos-mavlink-parser/tree/main"\
  }'
LABEL requirements="core >= 1.1"

EXPOSE 80

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["sh", "-c", "python -u -m main"]