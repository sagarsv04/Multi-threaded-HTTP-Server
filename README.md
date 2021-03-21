# Multi-threaded HTTP Server

A simple multi-threaded HTTP server that only accepts HTTP GET requests and returns the desired content to the client.


Author :
============
Sagar Vishwakarma (svishwa2@binghamton.edu)

State University of New York, Binghamton


File :
============

1)	server.py                  - Contains implementation of HTTP Server
2)	./www/                     - Contains resources files


Run :
============

- Open a terminal in project directory
- To run HTTP Server                        : python server.py
- Open another terminal
- To access any file from resources         : wget http://<ip address of server machine>:<port number>/<file name dot extention>
- To limit the download speed               : wget --limit-rate 60k <http link>
