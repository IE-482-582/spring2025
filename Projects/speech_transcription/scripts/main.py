#!/usr/bin/env python3

import sys

import pyaudio

import time
import threading 
import signal

import socketio

# sys.path.append("/home/cmurray3/Projects/WhisperLive/whisper_live")
# from whisper_live.clientROS import TranscriptionClient
from whisperLive_clientSocket import TranscriptionClient

STATUS_RATE = 1/5 # [Hz] -- How fast we'll publish status messages

audio = pyaudio.PyAudio()

# ----------------------
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
		
		# Define publishers
		# status
		
		# Subscribe to topics:
		# rospy.Subscriber('user_feedback', user_feedback, self.callback_user_feedback)
		@sio.on('user_feedback')
		def on_message(data):
			self.callback_user_feedback(data)
	
		self.mic_devices = self.get_devices()

		self.activeDevice = -1   # no mic yet.
		self.mic = None		
				
		# Initialize whisperLive (we'll do this later, instead)
		self.client = None
		'''
		self.client = TranscriptionClient(
		  "localhost",
		  9091,
		  lang="en",
		  translate=False,
		  model="tiny.en",                                      # also support hf_model => `Systran/faster-whisper-small`
		  use_vad=False,
		  save_output_recording=False,                         # Only used for microphone input, False by Default
		  output_recording_filename="./output_recording.wav", # Only used for microphone input
		  max_clients=4,
		  max_connection_time=600
		)
		'''
		
		self.trThread = None
		
		# FIXME -- We need to provide IP address as input argument (rather than using localhost)
		sio.connect('https://localhost:8080', transports=['websocket'])
		print('my sid is', sio.get_sid())
		
		statusRate = 1/STATUS_RATE # convert Hz to seconds
		while not monitor.is_shutdown:
			try:
				self.pubStatus()
			except Exception as e:
				self.pubNotice(f'Error in while loop: {e}')
				
			time.sleep(statusRate)
			
		self.shutdown()
		
		

	def _get_input_devices(self):
		'''
		This function was copied from the olab_audio package (where it is named `get_input_devices()`.
		It's the only function we were using from that package, so I just copied it here.
		'''
		print('NOTE: This function will not capture devices added/removed since pyaudio was imported.')
		# See https://stackoverflow.com/questions/72341919/python-pyaudio-updating-audio-devices-info-in-program-when-mic-disconnected 
		
		info = audio.get_host_api_info_by_index(0)
		numdevices = info.get('deviceCount')
		devices = []
		for i in range(0, numdevices):
				if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
					# print("Input Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))
					devices.append({'deviceID': i,
									'deviceType': 'mic', 
									'name': audio.get_device_info_by_host_api_device_index(0, i).get('name')})
		return devices		
						
	def get_devices(self):
		try:
			mic_devices_dict = self._get_input_devices()
			
			mic_devices = []
			for d in mic_devices_dict:
				mic_devices.append(f"{d['deviceID']}|{d['name']}")
			
			print(f"{mic_devices=}")
			
			return mic_devices
		except Exception as e:
			self.pubNotice(f'Error in get_devices: {e}')		
			return []
				
	def callback_user_feedback(self, msg):
		# For debugging purposes, we could print the message:
		# self.pubNotice(msg)
		'''
		Note, `msg` arrives as a list, like 
		[{'field_name': 'transcribe_start', 'values': ['0', '44100', '1', '44100', 'tiny']}]
		'''
		msg = msg[0]
		
		# Refresh mic list (will reply in pubAudioStatus)
		if (msg['field_name'] == 'get_devices'):
			self.mic_devices = self.get_devices()
				
		# Start transcribing
		if (msg['field_name'] == 'transcribe_start'):
			'''
			cmd.values = [str(deviceID.value), 	         // deviceID (from select list)		
						  str(samplerate.value),          // default 44100 [Hz]
						  str(channels.value),            // from select list of (1 or 2 disabled)
						  str(frames_per_buffer.value),   // default 44100?
						  str(model.value)];              // default tiny
			'''		
			try:
				deviceID = int(msg['values'][0])
			except Exception as e:
				deviceID = None
				self.pubNotice(f'Error setting deviceID: {e}')
									
			self.live_transcribe_start(deviceID=deviceID, model=msg['values'][4])
			
		# Stop transcribing
		if (msg['field_name'] == 'transcribe_stop'):
			self.live_transcribe_stop()
		
		# Start recording
		
		# Pause recording
		
		# Resume recording
		
		# Stop recording
		
	def live_transcribe_start(self, deviceID, model="tiny"):
		# FIXME -- Mention where there is documentation....
		self.client = TranscriptionClient(
		  "localhost",
		  9091,
		  lang="en",
		  translate=False,
		  model=f"{model}.en",                                      # also support hf_model => `Systran/faster-whisper-small`
		  use_vad=False,
		  save_output_recording=False,                         # Only used for microphone input, False by Default
		  output_recording_filename="./output_recording.wav", # Only used for microphone input
		  max_clients=4,
		  max_connection_time=600, 
		  deviceID=deviceID, 
		  sio=sio
		)
		
		self.trThread = threading.Thread(target=self._thread_transcribe, args=(deviceID,))
		self.trThread.daemon = True
		self.trThread.start()

	def _thread_transcribe(self, deviceID):
		self.client()

	def live_transcribe_stop(self):
		self.client.close_all_clients()
		self.trThread.join()

	def pubNotice(self, txt):
		'''
		Publishes a socket message to `notices` topic, with payload:
		{'data': <string>}
		'''
		print(f'Notice: {txt}')
		# Emit notices message:
		msg = {'data': txt}
		sio.emit('notices', msg)
		
	def pubStatus(self):
		'''
		Publishes a socket message to `status` topic, with payload described in `msg` dictionary below.
		'''
		
		msg = {'devices':           [],    # [id|description, id|description]
			   'activeDevice':      None,  # -1 means none
			   'sampleRate':        None,  # -1 means none
			   'isOn':              False, 
			   'isRecording':       False, 
			   'isRecordingPaused': False, 
			   'isTranscribing':    False}
		
		'''
		# This was just for debugging...
		if (self.client):
			print(self.client.client.recording)
		'''
		
		# Publish status info from WhisperLive
		msg['devices']	         = self.mic_devices	# [id|description, id|description]
		msg['activeDevice']      = self.activeDevice  # -1 means none
		if (self.mic is None):
			msg['samplerate']        = -1
			msg['isOn']              = False
			msg['isRecording']       = False
			msg['isRecordingPaused'] = False
			msg['isTranscribing']	 = False
		else:
			msg['samplerate']        = self.mic.samplerate
			msg['isOn']              = self.mic.micOn
			msg['isRecording']       = self.mic.isRecording
			msg['isRecordingPaused'] = False  # no longer defined in olab_audio.  self.mic._isRecordingPaused
			msg['isTranscribing']	 = self.mic.isTranscribing

		'''
		msg = {'text': '1234'}
		'''
		
		# Emit status message
		sio.emit('status', msg)
			
			
	def shutdown(self):
		# Gracefully shut things down.
		# Close files/processes, end loops, etc.
		self.pubNotice('shutting down')
			
		try:
			if (self.mic):
				self.mic.transcribeStop()
		except Exception as e:
			self.pubNotice(f'Shutdown Error: {e}')
			
		try:
			if (self.mic):
				self.mic.stop()
		except Exception as e:
			self.pubNotice(f'Shutdown Error: {e}')
		
		try:
			if (self.mic):
				self.mic.stop()
		except Exception as e:
			self.pubNotice(f'Shutdown Error: {e}')

		
		try:
			time.sleep(1)
			sio.disconnect()
		except Exception as e:
			self.pubNotice(f'Socket Disconnect Error: {e}')


if __name__ == "__main__":
	Main()
