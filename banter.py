# import openai
# from tenacity import *
# from elevenlabs import generate, play, set_api_key
# import os
# from dotenv import load_dotenv
# import json

# load_dotenv()
# openai.api_key = os.getenv('OPENAI_API_KEY')
# set_api_key(os.getenv('ELEVEN_LABS_API_KEY'))

# class Banter:
# 	def __init__(self, system_prompt: str
# 				, chat_model: str
# 				, voice: str
# 				, tts_model: str
# 				, out_dir: str):
# 	    self.system_prompt = system_prompt
# 	    self.chat_model = chat_model
# 	    self.voice = voice
# 	    self.tts_model = tts_model
# 	    self.chat_history = [{"role": "system", "content": self.system_prompt}]
# 	    self.out_dir = out_dir
# 	    if not os.path.exists(self.out_dir):
# 	    	os.makedirs(self.out_dir)

# 	@retry(stop=(stop_after_delay(10) | stop_after_attempt(20)))
# 	def transcribe(self, path_to_mp3: str) -> str:
# 		try:
# 		    if not os.path.exists(path_to_mp3):
# 		        raise FileNotFoundError(f"File not found: {path_to_mp3}")

# 		    audio_file = open(path_to_mp3, "rb")
# 		    transcript = openai.Audio.transcribe("whisper-1", audio_file)['text']
# 		    return transcript
# 		except FileNotFoundError as e:
# 		    # Handle file not found error
# 		    print(f"Error occurred: {e}")
# 		    raise
# 		except (openai.error.APIError, openai.error.AuthenticationError, open.error.RateLimitError, openai.error.ServiceUnavailableError) as e:
# 		    # Handle specific OpenAI API errors
# 		    print(f"Error occurred: {e}")
# 		    raise

# 	@retry(stop=(stop_after_delay(10) | stop_after_attempt(20)))
# 	def tts(self, text: str):
# 		audio = generate(
# 		  text=text,
# 		  voice=self.voice,
# 		  model=self.tts_model
# 		)
# 		out_file = f'{self.out_dir}/response_{(len(self.chat_history) - 1)/2}.mp3'
# 		with open(out_file, 'wb') as f:
# 			f.write(audio)
# 		return out_file

# 	@retry(stop=(stop_after_delay(10) | stop_after_attempt(20)))
# 	def get_text_response(self, text: str) -> str:
# 		try:
# 			self.chat_history.append({"role":"user", "content": text})
# 			response = openai.ChatCompletion.create(
# 											model=self.chat_model,
# 											messages=self.chat_history
# 											)['choices'][0]['message']['content']
# 			self.chat_history.append({"role":"assistant", "content": response})
# 			with open(f'{self.out_dir}/chat.json', 'w') as f:
# 				json.dump(self.chat_history, f)
# 			return response
# 		except (openai.error.APIError, openai.error.AuthenticationError, open.error.RateLimitError, openai.error.ServiceUnavailableError) as e:
# 		    # Handle specific OpenAI API errors
# 		    self.chat_history.pop()
# 		    print(f"Error occurred: {e}")
# 		    raise

# 	def respond_to_text(self, text: str):
# 		response = self.get_text_response(text)
# 		audio_path = self.tts(response)
# 		return response, audio_path

# 	def respond_to_audio(self, path_to_mp3: str):
# 		text = self.transcribe(path_to_mp3)
# 		return self.respond_to_text(text)
