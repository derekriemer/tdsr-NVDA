import threading
import os
import select
import socket
import speech
import tones
import queueHandler
import globalPluginHandler
import time
from NVDAObjects import NVDAObject
from NVDAObjects.behaviors import Terminal


class Server(object):

	def __init__(self, port, bind_host=''):
		self.port = port
		#Maps client sockets to clients
		self.clients = {}
		self.client_sockets = []
		self.running = False
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_socket.bind((bind_host, self.port))
		self.server_socket.listen(5)

	def run(self):
		self.running = True
		self.last_ping_time = time.time()
		while self.running:
			r, w, e = select.select(self.client_sockets+[self.server_socket], [], self.client_sockets, 60)
			if not self.running:
				break
			for sock in r:
				if sock is self.server_socket:
					self.accept_new_connection()
					continue
				self.clients[sock].handle_data()

	def accept_new_connection(self):
		client_sock, addr = self.server_socket.accept()
		client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		client = Client(server=self, socket=client_sock)
		self.add_client(client)

	def add_client(self, client):
		self.clients[client.socket] = client
		self.client_sockets.append(client.socket)

	def remove_client(self, client):
		del self.clients[client.socket]
		self.client_sockets.remove(client.socket)

	def client_disconnected(self, client):
		self.remove_client(client)

	def close(self):
		self.running = False
		self.server_socket.close()

class Client(object):
	id = 0

	def __init__(self, server, socket):
		self.server = server
		self.socket = socket
		self.buffer = ""
		self.authenticated = False
		self.id = Client.id + 1
		Client.id += 1

	def handle_data(self):
		try:
			data = self.buffer + self.socket.recv(16384)
		except:
			self.close()
			return
		data = str(data);print data
		if data == '': #Disconnect
			self.close()
			return
		if '\n' not in data:
			self.buffer = data
			return
		self.buffer = ""
		while '\n' in data:
			line, sep, data = data.partition('\n')
			self.parse(line)
		self.buffer += data

	def parse(self, line):
		line = line.decode('utf-8')
		if not line:
			return
		if line[0] == U"s" or line[0] == u'l':
			#print repr(line)
			if line[1:].strip() == u'':
				return
			speechFunc = (speech.speakMessage if line[0] == 's' else speech.speakSpelling)
			queueHandler.queueFunction(queueHandler.eventQueue, speechFunc, (line[1:]))
		elif line[0] == u'x':
			speech.cancelSpeech()

	def close(self):
		self.socket.close()
		self.server.client_disconnected(self)

class TDSRConsoleNuker(NVDAObject):
	category = "TDSR"
	TDSROn = False

	def event_gainFocus(self):
		#If things get added in the future, I don't want to reimplement them.
		#This is a horrible cheese, but it'll save my but from a few lines of typing.
		super(TDSRConsoleNuker, self).event_gainFocus()
		if self.TDSROn:
			self.stopMonitoring()

	def event_loseFocus(self):
		#If things get added in the future, I don't want to reimplement them.
		#This is a horrible cheese, but it'll save my but from a few lines of typing.
		if self.TDSROn:
			self.startMonitoring()
		super(TDSRConsoleNuker, self).event_loseFocus()

	def script_caret_on(self, gesture):
		gesture.send()

	def getScript(self, gesture):
		identifyer = ""
		for i in gesture.normalizedIdentifiers:
			if i in self._gestureMap:
				identifyer = i
				break
		#someone   is going to kill me after this hack ...
		if self.TDSROn and "script_caret_" in self._gestureMap.get(identifyer,lambda:1).__name__:
			return self.script_caret_on.__get__(self, self.__class__)
		return super(TDSRConsoleNuker, self).getScript(gesture)

	def script_toggleTDSR(self, gesture):
		if self.TDSROn:
			self.startMonitoring()
			tones.beep(500, 500)
		else:
			self.stopMonitoring()
			tones.beep(1000, 500)
		TDSRConsoleNuker.TDSROn = not self.TDSROn

	__gestures = {
		"kb:nvda+f5" : "toggleTDSR",
	}

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super(GlobalPlugin, self).__init__()
		self.thread = threading.Thread(target = self)
		self.thread.start()

	def __call__(self):
		self.server = Server(64111, '127.0.0.1')
		self.server.run()

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if Terminal in clsList or obj.windowClassName in (u"ConsoleWindowClass"):
			clsList.insert(0, TDSRConsoleNuker)

	def terminate(self):
		self.server.close()
		self.thread.join()
		super(GlobalPlugin, self).terminate()
