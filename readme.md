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
    - At the moment the program must be modified to contain the static ip of the vehicle. Ideally the main.py should be able to use the rout Blueos.local and communicate with the boat.
- Fix Docker networking to allow for the tcp server to be hosted within the container.
    - Currently, the docker container can only host a tcp client rather than a server. This makes it difficult to have a communication system that is persistent between different operators and communication loss.

## Usage
### Running via command line:
- Clone repository
- navigate to `app_server` folder and open `main.py`
- change the ip of the vehicle for mavlink2rest as well as the tcp connection

```
boat_url = ("http://<blueosipaddress>/mavlink2rest/mavlink/vehicles/1/components/1/messages/")
```

```
# Code here to start communication with backseat  
   HOST = "0.0.0.0"
```
- in the `app_server` directory run
```
python3 -u main.py
```

### Docker information
A version of this application has been built as a docker image that can be downloaded via [docker hub](https://hub.docker.com/r/werjer19/tcp-mavlink-driver).

This can also be pulled locally using the following command
```
docker pull werjer19/tcp-mavlink-driver:serverbuild-latest
```
It is important to note that this docker image is still a work in progress. 

