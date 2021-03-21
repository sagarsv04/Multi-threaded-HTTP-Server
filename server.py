#!/usr/bin/env python3
import os
import sys
import time
import socket
import signal
import threading
from mimetypes import MimeTypes


HOST = ""
PORT = 8069
TIMEOUT = 1
BUFFER_SIZE = 1024
RES_DIR = "./www/"

RES_DICT = {}



access_lock = threading.Lock()


def get_resources():

	res_dict = {}

	if os.path.isdir(RES_DIR):
		file_list = os.listdir(RES_DIR)
		if len(file_list)>0:
			for file in file_list:
				res_dict[file] = 0
		else:
			print("Directory {0} is Empty".format(RES_DIR))
			return False, res_dict
	else:
		print("Directory {0} Does not Exist".format(RES_DIR))
		return False, res_dict

	return True, res_dict


def parse_request(req_string):

	get_req_type = False
	req_file = ""

	res_match_str = req_string.split("HTTP/1.1")[0].strip()
	if res_match_str.split(" ")[0]=="GET":
		get_req_type = True
		req_file = res_match_str.split(" ")[-1].split("/")[-1]
		# print("{0}".format(req_resorce_info))
		if req_file=="":
			req_file = "index.html"
	return get_req_type, req_file



def get_send_responce(status_code):
	# status_code = 200
	default_res = ""

	if status_code==200:
		default_res = default_res + "HTTP/1.1 {0} {1}\r\n".format(status_code, "OK")
	elif status_code==404:
		default_res = default_res + "HTTP/1.1 {0} {1}\r\n".format(status_code, "Not Found")
	elif status_code==400:
		default_res = default_res + "HTTP/1.1 {0} {1}\r\n".format(status_code, "Bad Request")
	elif status_code==505:
		default_res = default_res + "HTTP/1.1 {0} {1}\r\n".format(status_code, "HTTP Version Not Supported")

	default_res = default_res + "Date: {0}\r\n".format(time.strftime("%a, %d %b %Y %I:%M:%S %p %Z", time.gmtime()))
	default_res = default_res + "Server: {0}\r\n".format(os.getenv("COMPUTERNAME"))
	default_res = default_res + "Last-Modified: {mod_date}\r\n"
	default_res = default_res + "Accept-Ranges: bytes\r\n"
	default_res = default_res + "Content-Length: {res_size}\r\n"
	default_res = default_res + "Content-Type: {res_type}\r\n\n"
	# default_res = default_res + "{res_html}"

	return default_res


def add_file_info(res_string, file_path):
	# file_path = "{0}index.html".format(RES_DIR)
	mod_date = time.strftime("%a, %d %b %Y %I:%M:%S %p %Z", time.gmtime(os.path.getmtime(file_path)))
	res_size = os.path.getsize(file_path)
	chk_type = MimeTypes()
	res_type = chk_type.guess_type(file_path)[0]

	res_string = res_string.format(mod_date=mod_date, res_size=res_size, res_type=res_type)
	# print(res_string)
	return res_string


def log_resource_access(addr, req_file, file_path):
	global RES_DICT

	print("{0} | {1} | {2} | {3}".format(file_path, addr[0], addr[-1], RES_DICT[req_file]))
	return 0


def send_recources(conn, file_path):

	with open(file_path, "rb") as f:
		while True:
			res_data = f.read(BUFFER_SIZE)
			if res_data==b"":
				break
			else:
				conn.send(res_data)
	# print("Resorce {0}".format(file_path))
	return 0


def send_basic_responce(conn, status_code, file_path=""):

	if status_code==200:
		if file_path=="":
			file_path = "{0}index.html".format(RES_DIR)
	else:
		file_path = "{0}404.html".format(RES_DIR)

	res_string = get_send_responce(status_code)
	res_string = add_file_info(res_string, file_path)
	# print("Basic Res {0}".format(res_string))
	res_string = res_string.encode()
	conn.sendall(res_string)
	return file_path


def read_connection(conn, addr):
	global RES_DICT

	req = conn.recv(BUFFER_SIZE)
	req_string = req.decode()
	# req_string = "GET / HTTP/1.1"
	if req_string != "":
		req_type, req_file = parse_request(req_string)
		if req_type:
			file_path = "{0}{1}".format(RES_DIR, req_file)
			if os.path.isfile(file_path):
				access_lock.acquire()
				RES_DICT[req_file] += 1
				access_lock.release()
				log_resource_access(addr, req_file, file_path)
				send_basic_responce(conn, 200, file_path)
				send_recources(conn, file_path)
			else:
				# print("Invalid Request for file : {0}".format(req_file))
				file_path = send_basic_responce(conn, 404)
				send_recources(conn, file_path)
		else:
			# print("Not a GET Request : {0}".format(req_string))
			file_path = send_basic_responce(conn, 505)
			send_recources(conn, file_path)
	else:
		# print("Empty Request : {0}".format(req_string))
		file_path = send_basic_responce(conn, 400)
		send_recources(conn, file_path)
	conn.shutdown(socket.SHUT_RDWR)
	conn.close()
	return 0


def run_server(server):

	run_flag = True

	while run_flag:
		try:
			conn, addr = server.accept()
			if conn:
				thread = threading.Thread(target=read_connection, args=(conn, addr))
				thread.start()
		except socket.timeout:
			pass
		except KeyboardInterrupt as ex:
			print("You Pressed Ctrl+C")
			run_flag = False
		time.sleep(0.01)
	return 0


def main():
	global RES_DICT

	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.settimeout(TIMEOUT)
	server.bind((HOST, PORT))
	print("Use 'http://127.0.0.1:<port>/resource=<file name>' to access files.")
	print("Server Host : {0}".format(server.getsockname()[0]))
	print("Server Port : {0}".format(server.getsockname()[-1]))
	server.listen(5)
	res_flag, RES_DICT = get_resources()
	if res_flag:
		try:
			print("Running the Server !")
			run_server(server)
		except KeyboardInterrupt as ex:
			print("You Pressed Ctrl+C")
	else:
		print("No Resources found to run Server")
	server.close()
	print("Server Closed Bye !")
	return 0


if __name__ == '__main__':
	main()
