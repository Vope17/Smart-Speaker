from tqdm import tqdm
from gpiozero import RGBLED
import RPi.GPIO as GPIO
import threading
import pyaudio
import time
import wave
import speech_recognition as sr
import jieba
from pypinyin import pinyin


def led_status(arg):
		led = RGBLED(22,23,27)
		shutdown = True
		i, j = 0, 0
		status = ""

		#led breathing
		while shutdown:
			action, shutdown = arg()

			action_list = action.split(':')
			if status != action_list[0]:
				led.color = (0, 0, 0)
				status = action_list[0]

			if action_list[0] == 'wait':
				led.color = (i/100, 0, 0)
			elif action_list[0] == 'record':
				led.color = (0, i/100, 0)
			elif action_list[0] == 'play':
				led.color = (0, 0, i/100)
			else:
				led.color = (i/100, 0, 0)

			if i == 0:
				j = 1
			elif i == 100:
				j = -1

			i += j
			time.sleep(float(action_list[1]))
class _TextProcess:
			
	def WordToPinyin(self, text):
		return (pinyin(text))
			
	def JiebaCutWord(self, text):
		return (' '.join(jieba.cut(text, cut_all=False, HMM=True)))

		
#audio save、read
class audio_class:
	def __init__(self):
		self.CHUNK = 1024
		self.FORMAT = pyaudio.paInt16
		self.CHANNELS = 1
		self.RATE =  16000 #16000
		self.RECORD_SECONDS = 5
		self.wave_path = r'./record.wav'
		self.p = pyaudio.PyAudio()
		self.str_VoiceToText = ""
		self.str_CuttedText = ""
		self.d2list_TextToPinyin = []

	def SpeechToText(self):
		r = sr.Recognizer()
		WAV = sr.AudioFile('./record.wav')
		with WAV as source:
			audio = r.record(source)
		return (r.recognize_google(audio, show_all=True, language='zh-tw'))['alternative'][0]['transcript']

	def SelectSong(self, text):
		dict_singers = { 
				'Jay' : ['zhōu', 'jié', 'lún'],
				'Lin' : ['cài', 'yī', 'lín'],
		}

		new_list = []
		# for the string match
		for l in text:
			new_list.append(''.join(l))
		cmp_str = ''.join(new_list)	

		for key in dict_singers:
				if ''.join(dict_singers[key]) in cmp_str:
					self.wave_path = f"./{key}.wav"
					print(f"Playing {key} Song...")	
					return
					
		print("fail")


	def record_audio(self):
		stream = self.p.open(format=self.FORMAT,
				channels=self.CHANNELS,
				rate=self.RATE,
				input=True,
				frames_per_buffer=self.CHUNK)

		print("Recording...")
		frames = []


		for _ in tqdm(range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS))):
			data = stream.read(self.CHUNK)
			frames.append(data)
		print("Finished recording")


		with wave.open(self.wave_path, 'wb') as wf:
			wf.setnchannels(self.CHANNELS)
			wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
			wf.setframerate(self.RATE)
			wf.writeframes(b''.join(frames))
		#wf.close()
		stream.stop_stream()
		stream.close()

		# Select Song
		c_TP = _TextProcess()
		self.str_VoiceToText = self.SpeechToText()
		print(self.str_VoiceToText)
		str_CuttedWord = c_TP.JiebaCutWord(self.str_VoiceToText)		
		d2list_Pinyin = c_TP.WordToPinyin(str_CuttedWord)
		self.SelectSong(d2list_Pinyin)


	def play_audio(self):


		wf = wave.open(self.wave_path, 'rb')
		stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()),
				channels=wf.getnchannels(),
				rate=wf.getframerate(),
				output=True,
				frames_per_buffer=self.CHUNK)

		print("Playing...")

		data = wf.readframes(self.CHUNK)
		while data:
			stream.write(data)
			data = wf.readframes(self.CHUNK)

		print("finished playing")

		stream.close()

	def cleanup(self):
		self.p.terminate()



def main():
	action = "wait:0.03"
	shutdown = True
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(24, GPIO.IN ,pull_up_down=GPIO.PUD_DOWN)
	t = threading.Thread(target = led_status, args = (lambda: (action, shutdown),))
	t.start()

	recorder = audio_class()


	try:
		while True:
			if GPIO.input(24) == True:
				action = "record:0.005"
				recorder.record_audio()
				action = "play:0.005"
				recorder.play_audio()
				action = "wait:0.03"

	except KeyboardInterrupt:
		shutdown = False
		print("close")
		t.join()
		#break
	except Exception as e:
		print(e)
		#break
	finally:
		#p.terminate()
		shutdown = False
		recorder.cleanup()
		GPIO.cleanup(24)
		t.join()


if __name__ == '__main__':
	main()
