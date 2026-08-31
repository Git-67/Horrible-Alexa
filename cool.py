import asyncio as sync
import edge_tts as e_tts
import keyboard as kb
import mouse as m
import os
from ollama import chat
import playsound3
import pyperclip as pc
from queue import Queue as q
import screen_brightness_control as sbc
import tempfile
import threading
import time as t

import ffmpeg
from youtube_search import YoutubeSearch
from yt_dlp import YoutubeDL 

import whisper
import sounddevice as sd
import numpy as np

#import anthropic as ant
#with open (".env", "r") as file:
#   api_key = file.read().split(" ")[2]
#
#client = ant.Anthropic(api_key=api_key)

whisper_model = whisper.load_model("medium") # "tiny" is faster, "small"/"medium" more accurate
conversation_history = []
music_queue = q()
current_sound = None
generated_text = ""
with open ('system-prompt.txt', 'r') as file:
    system_prompt = file.read()

def new_message(content):
    global conversation_history

    conversation_history.append({
        "role": "user", 
        "content": content
    })

    response = chat(
        model='qwen3:4b',
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            *conversation_history
        ],
        options={
            "temperature": 0.3
        }
    )

    assistant_reply = response["message"]["content"]

    conversation_history.append({
        "role": "assistant",
        "content": assistant_reply
    })

    return assistant_reply

def listen(samplerate=16000):
    print("Recording...")
    frames = []

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    stream = sd.InputStream(
        samplerate=samplerate, 
        channels=1, 
        dtype='float32', 
        callback=callback
    )

    with stream:
        while kb.is_pressed("esc"):
            t.sleep(0.01)

    print("Transcribing...")

    if not frames:
        return ""

    audio = np.concatenate(frames, axis=0)
    audio = np.squeeze(audio)

    result = whisper_model.transcribe(
        audio=audio,
        language=None,
        task='transcribe',
        fp16=False
    )
    
    text = result["text"].strip()
    print(f"User: {text}")
    return text

ydl_opts = {
    'cookiefile': "yummy_youtube_cookies.txt",
    'format': 'bestaudio',
    'embed-thumbnail': True,
    'outtmpl': '%(id)s.mp3',
    "js_runtimes": {
        "deno": {
            "path": r"C:/Users/HP/.deno/bin/deno.exe"
        }
    },
    "extractor_args": {
        "youtube": {
            "player_client": ["default", "web_embedded"]
        }
    }
}

def get_yt_dict(song):
    sync.run(speak("Retrieving Song ID"))
    search_results = YoutubeSearch(song, max_results=10).to_dict()
    for i in range(10):
        if search_results[i]['duration'].count(':') > 1:
            continue
        id = search_results[i]['id']
        break
    return id

def ffmpeg_convert(id, bitrate=128):
    with YoutubeDL(ydl_opts) as YDL:
        YDL.download('https://music.youtube.com/watch?v=' + id)
    sync.run(speak("Conerting mp3 to mkv"))
    filename = id + '.mp3'
    ffmpeg.input(filename).audio.filter('volume', 0.1).output(
        f"{id}.mkv",
        acodec="libopus",
        audio_bitrate=f"{bitrate}k"
    ).run()
    os.remove(f"{id}.mp3")
    return id

def music_player():
    global current_sound
    while True:
        music_id = music_queue.get()
        current_sound = playsound3.playsound(
            f"{music_id}.mkv",
            block=False
        )
        while current_sound.is_alive():
            t.sleep(0.1)
        current_sound = None
        try:
            os.remove(f"{music_id}.mkv")
        except FileNotFoundError:
            pass
        music_queue.task_done()

def stop_music():
    global current_sound
    if current_sound and current_sound.is_alive():
        current_sound.stop()
    while not music_queue.empty():
        try:
            music_queue.get_nowait()
            music_queue.task_done()
        except:
            break

class Commands:

    def brightness_up(reply):
        sbc.set_brightness('+25')
        reply = reply.replace("/command brightness up", "")
        return reply

    def brightness_down(reply):
        sbc.set_brightness('-25')
        reply = reply.replace("/command brightness down", "")
        return reply

    def volume_up(reply):
        for _ in range(5):
            kb.press_and_release("volume up")
        reply = reply.replace("/command volume up", "")
        return reply

    def volume_down(reply):
        for _ in range(5):
            kb.press_and_release("volume down")
        reply = reply.replace("/command volume down", "")
        return reply

    def download_and_mkv(reply):
        song = reply.split("/command play", 1)[1].strip()
        id = get_yt_dict(song)
        ffmpeg_convert(id)
        music_queue.put(id)
        reply = reply.replace(reply.split("/command play", 1)[1].strip(),"")
        reply = reply.replace("/command play","")
        return reply, id

    def music_quit(reply):
        stop_music()
        reply = reply.replace("/command stop-music", "")
        return reply

    def write(reply):
        global generated_text
        generated_text = reply.split("/command write ")[1]
        reply = reply.replace(f"/command write {generated_text}", "")
        pc.copy(generated_text)
        sync.run(speak("Generated Text is Copied to Clipboard"))
        return reply

def command_parser(reply):
    music_id = None
    speech = reply
        
    if "/command brightness up" in speech:
        speech = Commands.brightness_up(speech)
    if "/command brightness down" in speech:
        speech = Commands.brightness_down(speech)
    if "/command volume up" in speech:
        speech = Commands.volume_up(speech)
    if "/command volume down" in speech:
        speech = Commands.volume_down(speech)
    if "/command play" in speech:
        speech, music_id = Commands.download_and_mkv(speech)
    if "/command stop-music" in speech:
        speech = Commands.music_quit(speech)
    if "/command write" in speech:
        speech = Commands.write(speech)

    print(f"Sugoi: {speech.strip()}")

    return speech, music_id


async def speak(text):
    voice = "en-US-GuyNeural"

    # Detect Chinese characters
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        voice = "zh-CN-YunxiNeural"

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as file:
        filename = file.name

    try:
        tts = e_tts.Communicate(text, voice, rate="+40%", pitch="+2Hz", volume="-60%")
        await tts.save(filename)

        playsound3.playsound(filename)

    finally:
        os.remove(filename)

threading.Thread(
    target=music_player,
    daemon=True
).start()

generated_text = "hello world!"

while True:
    print("\nHold esc to talk...")
    kb.wait("esc")
    content = listen()
    if not content:
        continue
    reply = new_message(content)
    speech, music_id = command_parser(reply)
    sync.run(speak(speech))
    if music_id:
        music_queue.put(music_id)

