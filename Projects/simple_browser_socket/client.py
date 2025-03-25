#!/usr/bin/env python3

import signal
import time

STATUS_RATE = 1/5 # [Hz] -- How fast we'll publish status messages

# ----------------------
import socketio

sio = socketio.Client(ssl_verify=False)  # , logger=True, engineio_logger=True)

@sio.event
def connect():
    print('socket connection established')

@sio.event
def disconnect():
	print('socket disconnected from server')
# ----------------------

class GracefulShutdown:
	# A class-based solution to exit gracefully on sigint/sigterm:
	# https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully	
	def __init__(self):
		self.is_shutdown = False
		self.shutdownFunc = self._shutdownFunc

		signal.signal(signal.SIGINT,  self.exit_gracefully)
		signal.signal(signal.SIGTERM, self.exit_gracefully)
	
	def _shutdownFunc(self):
		self.is_shutdown = True
		
	def exit_gracefully(self, signum, frame):
		self.is_shutdown = True
		self.shutdownFunc()
		
	def on_shutdown(self, func):
		self.shutdownFunc = func
		
				
	'''
	# In Main:
	monitor = GracefulShutdown()
	
	# Set shutdown function
	monitor.on_shutdown(self.shutdown)
	
	while not monitor.is_shutdown
	
	'''



class Main:
	def __init__(self):
		# Set the shutdown function
		monitor = GracefulShutdown()
		monitor.on_shutdown(self.shutdown)
		
		# Subscribe to topics:
		@sio.on('chat')
		def on_message(data):
			self.callback_chat(data)
	
		@sio.on('direction')
		def on_message(data):
			print(f'I received this direction message: {data[0]}')
			sio.emit('reply', {'data': data[0]})
			
		'''
		# If we had a topic named 'xyz', we'd define a listener for it here:
		@sio.on('xyz')
		def on_message(data):
			print(f'received xyz message: {data}')
		'''		
		
		# FIXME -- We need to provide IP address as input argument (rather than using localhost)
		sio.connect('https://localhost:8080', transports=['websocket'])
		print('my sid is', sio.get_sid())
		
		statusRate = 1/STATUS_RATE # convert Hz to seconds
		while not monitor.is_shutdown:
			try:
				'''
				...
				Here's where you'd put some code to run forever inside a loop
				...
				'''
				self.doSomething()
			except Exception as e:
				self.pubNotice(f'Error in while loop: {e}')
			
			# Keep the loop looping at a reasonable pace	
			time.sleep(statusRate)
			
		# When infinite loop is done, call the `shutdown` function	
		self.shutdown()
		
		
	def callback_chat(self, data):
		print(f'received chat message: {data}')
		sio.emit('reply', {'data': data[0]})
				
	def doSomething(self):
		''' 
		A dummy function that actually does nothing
		'''
		pass
		

	def pubNotice(self, txt):
		'''
		Publishes a socket message to `notices` topic, with payload:
		{'data': <string>}
		'''
		print(f'Notice: {txt}')
		# Emit notices message:
		sio.emit('notices', {'data': txt})
					
			
	def shutdown(self):
		# Gracefully shut things down.
		# Close files/processes, end loops, etc.
		print('shutting down')
			
		try:
			time.sleep(1)
			sio.disconnect()
		except Exception as e:
			self.pubNotice(f'Socket Disconnect Error: {e}')


if __name__ == "__main__":
	Main()
