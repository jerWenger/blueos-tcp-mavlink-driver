# BlueOS Backseat Bridge
Author: Jeremy Wenger

Contact: jwenger@mit.edu

## Purpose
The purpose of this program is to act as a communication bridge between the BlueOS software stack and a backseat controller via a tcp connection.

## Key Functionalities
- Sending a list of desired messages the backseat would like to receive.
- Handling RC signals to allow for maual or autonomous operation.
- Archtecture agnostic communication. 

## TO DO
- Fix static ip routing of Mavlink2Rest API.
    - at the moment the code has only been tested with one bluos vehicle on the network. This should be made more robust to allow for multiple vehicles

## Usage

### Docker information
A version of this application has been built as a docker image that can be downloaded via [docker hub](https://hub.docker.com/r/werjer19/tcp-mavlink-driver).

To pull and run this image via the command line:

```
docker pull werjer19/tcp-mavlink-driver:latest

docker run -d --name tcp-server -p 29217:29217 werjer19/tcp-mavlink-driver:latest
```

the tcp server is then hosted on \<host machine ip>:29217