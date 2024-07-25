FROM python:3.9-slim-bullseye

COPY app /app

WORKDIR /app

LABEL version="1.0.1"

EXPOSE 80 9090

LABEL permissions='{\
  "ExposedPorts": {\
  "80/tcp": {},\
  "9090/tcp": {}\
  },\
  "HostConfig": {\
  "ExtraHosts": ["host.docker.internal:host-gateway"],\
  "PortBindings": {\
  "80/tcp": [{"HostIP": ""}],\
  "9090/tcp": [{"HostPort": "9090", "HostIP": ""}]\
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

RUN chmod +x get_host_ip.sh

ENTRYPOINT ["/app/get_host_ip.sh"]