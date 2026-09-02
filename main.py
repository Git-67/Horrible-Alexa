import os
import sys

import asyncio as sync
import edge_tts as e_tts
import keyboard as kb
import mouse as m
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

import numpy as np
import sounddevice as sd
import torch
import whisper

# List of Commands
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
        reply = reply.replace(reply.split("/command play", 1)[1].strip(), "")
        reply = reply.replace("/command play", "")

        id, title = get_yt_dict(song)

        if not confirm_song(title):
            sync.run(speak("Okay, cancelling that."))
            return reply, None

        ffmpeg_convert(id)
        if (not music_queue.empty()) and current_sound and current_sound.is_alive():
            reply += f"{title} has been added to the queue."
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

    def time(reply):
        current_time = t.strftime("%I:%M %p") # Format time as HH:MM AM/PM
        reply = reply.replace(reply, f"The current time is {current_time}.")
        return reply

    def set_alarm(reply):
        alarm_time.append(reply.split("/command alarm", 1)[1].strip())
        reply = reply.replace(f"/command alarm {alarm_time[-1]}", "")
        return reply, alarm_time

# Records audio from mic until user releases esc, transcribes using whisper, returns transcribed text
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
        fp16=(device == "cuda")
    )
    text = result["text"].strip()
    print(f"User: {text}")
    return text

# Sends transcribed text to Ollama and returns the assistant's reply, also keeps track of conversation history
def new_message(content):
    global conversation_history
    conversation_history.append({
        "role": "user", 
        "content": content
    })
    conversation_history = conversation_history[-50:]   # keeps memory of the last 50 messages to avoid context overflow
    response = chat(
        model='qwen2.5:7b',
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            *conversation_history
        ],
        options={
            "temperature": 0.1
        },
        keep_alive=-1
    )
    assistant_reply = response["message"]["content"]
    conversation_history.append({
        "role": "assistant",
        "content": assistant_reply
    })
    return assistant_reply

# Confirms the song with the user and parses confirmation check to is_affirmative
def confirm_song(title):
    """Speak the found title back to the user and wait for a push-to-talk yes/no."""
    sync.run(speak(f"I found {title}. Hold escape and say yes to confirm, or no to cancel."))
    print("Hold esc to confirm song...")
    while not kb.is_pressed("esc"):
        t.sleep(0.01)
    response = listen()
    return is_affirmative(response)

# Confirms if the user said yes or no, returns True for yes and False for no
def is_affirmative(text):
    """Very simple yes/no interpretation of a spoken confirmation."""
    text = text.lower()
    negative_words = ["no", "nope", "nah", "wrong", "cancel", "don't", "dont"]
    affirmative_words = ["yes", "yeah", "yep", "yup", "correct", "right", "sure", "confirm", "play it"]
    if any(w in text for w in negative_words):
        return False
    if any(w in text for w in affirmative_words):
        return True
    # If unclear, default to "no" so we never download the wrong thing silently
    return False

# Retrieves the youtube id and title of the song, returns them as a tuple (id, title)
def get_yt_dict(song):
    sync.run(speak("Retrieving Song ID"))
    search_results = YoutubeSearch(song, max_results=10).to_dict()
    for i in range(10):
        if search_results[i]['duration'].count(':') > 1:
            continue
        id = search_results[i]['id']
        title = search_results[i]['title']
        break
    return id, title

# Downloads the mp3 from youtube and converts it to mkv with ffmpeg, returns the id of the song
def ffmpeg_convert(id, bitrate=192):
    sync.run(speak("Downloading mp3"))
    with YoutubeDL(ydl_opts) as YDL:
        YDL.download('https://music.youtube.com/watch?v=' + id)
    sync.run(speak("Converting mp3 to mkv"))
    filename = id + '.mp3'
    ffmpeg.input(filename).audio.filter('volume', 0.1).output(
        f"{id}.mkv",
        acodec="libopus",
        audio_bitrate=f"{bitrate}k"
    ).run()
    os.remove(f"{id}.mp3")
    return id

# Plays music from the queue on another thread, waits for it to finish, then deletes the files on a seperate thread to avoid blocking the main thread
def music_player():
    global current_sound
    while True:
        music_id = music_queue.get()
        sync.run(speak(f"Now playing {music_id}"))
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

# Clears music queue and kills current sound if applicable, used for /command stop-music
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

# Parses commands by Ollama and executes them to the respective class functions, returns the modified reply and music_id if applicable
def command_parser(reply):
    global alarm_time
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
    if "/command time" in speech:
        speech = Commands.time(speech)
    if "/command alarm" in speech:
        speech, alarm_time = Commands.set_alarm(speech)
    print(f"Sugoi: {speech.strip()}")
    return speech, music_id

# Starts async for edge_tts to convert reply to speech and plays it, detects Chinese characters and switches to a Chinese voice if applicable
async def speak(text):
    voice = "en-IE-EmilyNeural"
    if any('\u4e00' <= char <= '\u9fff' for char in text):  # Detect Chinese characters
        voice = "zh-CN-YunxiNeural"
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as file:
        filename = file.name
    try:
        tts = e_tts.Communicate(text, voice, rate="+10%", pitch="-2Hz", volume="-60%")
        await tts.save(filename)
        playsound3.playsound(filename)
    finally:
        os.remove(filename)

# Options for youtube-dl and sys.argv for cookiefile and deno path, defaults to "yummy_youtube_cookies.txt" and "C:\Users\HP\.deno\bin\deno.exe" if not provided
# Also runs deno on js_runtimes to avoid the "deno not found" error when using youtube-dl
ydl_opts = {
    'cookiefile': sys.argv[1] if len(sys.argv) > 1 else "yummy_youtube_cookies.txt",
    'format': 'bestaudio',
    'embed-thumbnail': True,
    'outtmpl': '%(id)s.mp3',
    'js_runtimes': {
        'deno': {
            'path': sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\HP\.deno\bin\deno.exe",
        }
    },
    'remote_components': ['ejs:github'],
    "extractor_args": {
        "youtube": {
            "player_client": ["web_embedded"]
        }
    }
}

# Start music_player thread
threading.Thread(
    target=music_player,
    daemon=True
).start()

# Load system prompt from file
with open ('system-prompt.txt', 'r') as file:
    system_prompt = file.read()

# Load Whisper model
device = "cuda" if torch.cuda.is_available() else "cpu"; print("Loading Whisper...")
whisper_model = whisper.load_model("large-v3-turbo", device=device); print("Whisper loaded.")

# Variable Initialization
music_queue = q()
current_sound = None
generated_text = None
alarm_time = []
conversation_history = []

# Start greeting
print("Sending greeting to Ollama...")
greeting = new_message(f"The user just entered the room. Please greet them. The current time is {t.strftime('%I:%M %p')}.")
print(f"Sugoi: {greeting.strip()}")
sync.run(speak(greeting))

# Main Loop
while True:
    print("\nHold esc to talk...")

    # Wait for user to hold esc to talk AND checks for alarms
    while not kb.is_pressed("esc"):
        if t.strftime("%H:%M") in alarm_time:
            sync.run(speak(new_message(f"The user's alarm is going off, remind him and tell him the current time is {t.strftime('%I:%M %p')}.")))
            alarm_time.remove(t.strftime("%H:%M"))
        t.sleep(0.01)

    # Reruns loop if content is empty, otherwise sends content to Ollama and gets a reply
    content = listen()
    if not content:
        continue

    # Generates reply, parses commands, speaks filtered reply with edge_tts, queues music if applicable
    reply = new_message(content)
    speech, music_id = command_parser(reply)
    sync.run(speak(speech))

    # Queues music if a music_id was returned from the command parser
    if music_id:
        music_queue.put(music_id)