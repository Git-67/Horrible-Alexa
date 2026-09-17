import os

import argparse as ap
import asyncio as sync
from supertonic import TTS
from datetime import datetime, timedelta
import json
import keyboard as kb
import logging
import mouse as m
from ollama import chat
import playsound3
import pyperclip as pc
from queue import Queue as q
import random as ran
import screen_brightness_control as sbc
import sys
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
import supertonic.config as _st_config
_st_config.DEFAULT_ONNX_PROVIDERS = ["CUDAExecutionProvider", "CPUExecutionProvider"]

from supertonic import TTS

# Variable Initialization
music_queue = q()
current_sound = None
generated_text = None
shutdown = False
alarm_time = []
conversation_history = []
song_cache = []
zen_thread = None
zen_running = threading.Event()
current_zen = None  # tracks the currently playing zen sound handle

# CLI Arguments & JSON Initialization Config Handling 
with open('config.json', 'r') as f:
    config = json.load(f)
parser = ap.ArgumentParser()
parser.add_argument("-c", "--cookiefile", type=str, default=config.get("cookiefile", "yummy_youtube_cookies.txt"))
parser.add_argument("-d", "--deno", type=str, default=config.get("deno_path", r"C:\Users\HP\.deno\bin\deno.exe"))
parser.add_argument("-s", "--save", action="store_true", help="Save the provided -c/-d values as the new defaults in config.json")
args = parser.parse_args()
if args.save:
    config["cookiefile"] = args.cookiefile
    config["deno_path"] = args.deno
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print("Saved new defaults to config.json")

# Class of Commands
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
            sync.run(speak(f"Cancelling {title}."))
            return "", None

        if (id, title) in song_cache:
            logger.debug(f"{title} already cached, skipping re-download")
        else:
            ffmpeg_convert(id)
        if (not music_queue.empty()) and current_sound and current_sound.is_alive():
            reply += f"{title} has been added to the queue."
        return reply, (id, title)

    def music_quit(reply):
        stop_music()
        reply = reply.replace("/command stop-music", "")
        return reply

    def write(reply):
        global generated_text
        parts = reply.split("/command write", 1)
        if len(parts) < 2:
            return reply
        generated_text = parts[1].strip()
        logger.debug(f"Copying to clipboard: {generated_text!r}")
        reply = reply.replace(f"/command write{parts[1]}", "").strip()
        pc.copy(generated_text)
        logger.debug(f"Clipboard now contains: {pc.paste()!r}")
        return reply

    def set_alarm(reply):
        args = reply.split("/command alarm", 1)[1].strip()
        mode, rest = args.split(" ", 1)
        rest = rest.strip()
        parts = rest.split(" ", 1)
        value = parts[0]
        reason = parts[1].strip() if len(parts) > 1 else ""

        if mode == "in":
            minutes = int(value)
            target = datetime.now() + timedelta(minutes=minutes)
            alarm_clock = target.strftime("%H:%M")
        else:  # mode == "at"
            alarm_clock = value

        alarm_time.append([alarm_clock, reason])
        logging.debug(f"alarm list: {alarm_time}")
        reply = reply.replace(f"/command alarm {args}", "")
        return reply, alarm_time

    def remove_alarm(reply):
        args = reply.split("/command alarm-remove", 1)[1].strip()
        checked_alarms = [element for element in alarm_time if element[0] == args]
        for i in range(len(checked_alarms)):
            alarm_time.remove(checked_alarms[i])
        logging.debug(f"alarm list: {alarm_time}")
        reply = reply.replace(f"/command alarm-remove {args}", "")
        return reply

    def zen(reply):
        global zen_thread, zen_running, current_zen
        args = reply.split("/command zen", 1)[1].strip()

        if args == "play":
            stop_music_playback()  # toggle off regular music first
            if zen_thread is None or not zen_thread.is_alive():
                zen_running.clear()
                zen_thread = threading.Thread(
                    target=zen_player,
                    args=(zen_running,),
                    daemon=True
                )
                zen_thread.start()
                logging.debug("Zen player started")
            else:
                logging.debug("Zen player already running, ignoring play")
        elif args == "stop":
            stop_zen_playback()
            logging.debug("Zen player stopped")

        reply = reply.replace(f"/command zen {args}", "")
        return reply

    def alarm_check(reply):
        reply = new_message(f"User is requesting for you to list all alarms, here's the list of alarm times, and their reasons: {alarm_time}")
        return reply

    def shutdown(reply):
        global shutdown
        reply = reply.replace(f"/command quit", "")
        logger.debug(f"Initializing Shutdown at {t.strftime('%H:%M:%S')!r}")
        shutdown = True
        return reply

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
        callback=callback,
        device=None # choose device default
    )
    with stream:
        while kb.is_pressed("esc"):
            t.sleep(0.01)
    print("Transcribing...")
    if not frames:
        return ""
    audio = np.concatenate(frames, axis=0)
    audio = np.squeeze(audio)
    logging.info(f"Audio max amplitude: {np.abs(audio).max():.4f}, mean: {np.abs(audio).mean():.4f}")
    result = whisper_model.transcribe(
        audio=audio,
        language='en',
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
    conversation_history = conversation_history[-250:]   # keeps memory of the last 250 messages to remove old information
    response = chat(
        model='qwen3.5:9b',
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            *conversation_history
        ],
        think=False,
        options={
            "temperature": 0.1,
            "num_ctx": 8192
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
    sync.run(speak(f"I found {title}. Hold escape and say yes to confirm, or no to cancel."))
    print("Hold esc to confirm song...")
    kb.wait("esc")
    playsound3.playsound("audio/mic-recording.wav", block=False)
    response = listen()
    return is_affirmative(response)

# Confirms if the user said yes or no, returns True for yes and False for no
def is_affirmative(text):
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
    search_results = YoutubeSearch(song, max_results=20).to_dict()
    for i in range(20):
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
        music_id, title = music_queue.get()
        song_cache.append((music_id, title))
        sync.run(speak(f"Now playing {title}"))
        current_sound = playsound3.playsound(
            f"{music_id}.mkv",
            block=False
        )
        while current_sound.is_alive():
            t.sleep(0.1)
        current_sound = None
        try:
            if len(song_cache) > 10:
                old_id, old_title = song_cache.pop(0)
                os.remove(f"{old_id[0][0]}.mkv")
                logging.debug(f"Removed {old_title[0][1]} from cache")
        except FileNotFoundError:
            pass
        music_queue.task_done()

# Plays ambient zen tracks on a loop until stop_event is set; runs on its own daemon thread
def zen_player(stop_event):
    global current_zen
    zen_queue = [f"{ran.randint(1,16)}.mp3" for _ in range(10)]
    while not stop_event.is_set():
        if len(zen_queue) < 10:
            zen_queue.append(f"{ran.randint(1,16)}.mp3")
        current_zen = playsound3.playsound(
            f"./lofi-audio/{zen_queue.pop(0)}",
            block=False
        )
        while current_zen.is_alive():
            if stop_event.is_set():
                break
            t.sleep(0.1)
        current_zen = None
    logging.debug("Zen player thread exiting")

# Stops only the regular music queue/playback
def stop_music_playback():
    global current_sound
    if current_sound and current_sound.is_alive():
        current_sound.stop()
    while not music_queue.empty():
        try:
            music_queue.get_nowait()
            music_queue.task_done()
        except:
            break

# Stops only the zen/lofi player
def stop_zen_playback():
    global current_zen, zen_thread, zen_running
    zen_running.set()
    if current_zen and current_zen.is_alive():
        current_zen.stop()
    if zen_thread is not None and zen_thread.is_alive():
        zen_thread.join(timeout=2)
    zen_thread = None
    current_zen = None

# Stops both, used for /command stop-music
def stop_music():
    stop_music_playback()
    stop_zen_playback()

# Parses commands by Ollama and executes them to the respective class functions, returns the modified reply and music_id if applicable
def command_parser(reply):
    global alarm_time
    music_item = None
    speech = reply
    had_command = False

    if "/command brightness up" in speech:
        speech = Commands.brightness_up(speech)
        had_command = True
    if "/command brightness down" in speech:
        speech = Commands.brightness_down(speech)
        had_command = True
    if "/command volume up" in speech:
        speech = Commands.volume_up(speech)
        had_command = True
    if "/command volume down" in speech:
        speech = Commands.volume_down(speech)
        had_command = True
    if "/command play" in speech:
        speech, music_item = Commands.download_and_mkv(speech)
        had_command = True
    if "/command stop-music" in speech:
        speech = Commands.music_quit(speech)
        had_command = True
    if "/command write" in speech:
        speech = Commands.write(speech)
        had_command = True
    if "/command alarm" in speech:
        had_command = True
        if "/command alarm-remove" in speech:
            speech = Commands.remove_alarm(speech)
        elif "/command alarm-queue" in speech:
            speech = Commands.alarm_check(speech)
        else:
            speech, alarm_time = Commands.set_alarm(speech)
    if "/command zen" in speech:
        speech = Commands.zen(speech)
        had_command = True
    if "/command quit" in speech:
        speech = Commands.shutdown(speech)
        had_command = True

    # Fallback: if a command fired but stripped the reply down to nothing,
    # give the user some audio confirmation instead of dead silence
    if had_command and not speech.strip():
        speech = "Done."

    print(f"\nPluto: {speech.strip()}\n")
    return speech, music_item

# Checks if any alarms are due and triggers the alarm if applicable, runs on a separate thread
def alarm_check():
    while True:
        t.sleep(0.1)
        now = t.strftime("%H:%M")
        for alarm in list(alarm_time):  
            if alarm[0] == now:
                reason_clause = f" about {alarm[1]}" if alarm[1] else ""
                # Ensure that speech synthesis is not overlapping by using a loc
                with speech_lock:
                    playsound3.playsound("./audio/alarm.mp3", block=False)
                    sync.run(speak(new_message(f"The user's alarm is going off{reason_clause}, remind him and tell him the current time is {t.strftime('%I:%M %p')}.")))
                alarm_time.remove(alarm)

# Starts async for supertonic 3 to convert reply to speech and plays it
async def speak(text):
    with tempfile.NamedTemporaryFile(suffix=".mp3") as file:
        filename = file.name
    try:
        wav, duration = tts.synthesize(text, voice_style=style, lang="en")
        tts.save_audio(wav, filename)
        playsound3.playsound(filename)
    finally:
        file.close()

# Options for youtube-dl and sys.argv for cookiefile and deno path, defaults to "yummy_youtube_cookies.txt" and "C:\Users\HP\.deno\bin\deno.exe" if not provided
# Also runs deno on js_runtimes to avoid the "deno not found" error when using youtube-dl
ydl_opts = {
    'cookiefile': args.cookiefile,
    'format': 'bestaudio',
    'embed-thumbnail': True,
    'outtmpl': '%(id)s.mp3',
    'js_runtimes': {
        'deno': {
            'path': args.deno,
        }
    },
    'remote_components': ['ejs:github'],
    "extractor_args": {
        "youtube": {
            "player_client": ["web_embedded"]
        }
    }
}

# Initialize a lock for speech synthesis to prevent overlapping speech
speech_lock = threading.Lock()
# Start music_player thread
threading.Thread(
    target=music_player,
    daemon=True
).start()
# Start alarm_check thread
threading.Thread(
    target=alarm_check,
    daemon=True
).start()

# Initialize logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(funcName)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pluto")

# Initialize TTS
tts = TTS(auto_download=True)
style = tts.get_voice_style(voice_name="F5")

# Overall Initialization
# Load system prompt for Qwen from file
with open('system-prompt.txt', 'r') as file:
    system_prompt = file.read()
# Load Whisper model
if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"
playsound3.playsound("./audio/startup-sound.mp3", block=False)
logging.info(f"Initializing Whisper with {device!r}")
whisper_model = whisper.load_model("large-v3-turbo", device=device)
logging.info("Whisper model fully loaded")
# Start greeting
logging.info("Sending Greeting to Ollama")
greeting = new_message(f"The user just entered the room. Please greet them. The current time is {t.strftime('%I:%M %p')}.")
speech, _ = command_parser(greeting)
if speech:
    sync.run(speak(speech))

# Main Loop
while True:
    print("\nHold esc to talk...\n")
    kb.wait("esc")
    playsound3.playsound("./audio/mic-recording.wav", block=False)
    content = listen()
    if not content:
        playsound3.playsound("./audio/mic-no-detect.wav", block=False)
        continue
    # Ensure that speech synthesis is not overlapping by using a lock
    with speech_lock:
        logging.info(f"Sending user input to Ollama: {content!r}")
        reply = new_message(content + f"(The current time is {t.strftime('%I:%M %p')})")
        speech, music_id = command_parser(reply)
        if speech:
            sync.run(speak(speech))
        if shutdown:
            playsound3.playsound("audio/shutdown-sound.mp3")
            logging.debug("Shutting Down")
            sys.exit(0)
    if music_id:
        music_queue.put(music_id)