FROM python:3.9-slim-bullseye

COPY app_server /app_server

WORKDIR /app_server

LABEL version="1.0.1"

EXPOSE 80 29217

LABEL permissions='{\
  "ExposedPorts": {\
  "80/tcp": {},\
  "29217/tcp": {}\
  },\
  "HostConfig": {\
  "ExtraHosts": ["host.docker.internal:host-gateway"],\
  "PortBindings": {\
  "80/tcp": [{"HostIP": ""}],\
  "29217/tcp": [{"HostPort": "29217", "HostIP": ""}]\
  },\
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

RUN apt-get update && apt-get install -y net-tools

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["sh", "-c", "python -u -m main"]