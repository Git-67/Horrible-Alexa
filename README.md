## Versions
Python: 3.14\
Ollama: Qwen3:14b

## Create a Cookie File
Install "cookies.txt" Firefox extension and then open the extension whilst on your Youtube Music. Press copy on current site cookies. Add a new file titled "yummy-youtube-cookies.txt" in this repo, inside with your pasted cookies.

## Dependencies
Install Ollama [HERE](https://ollama.com/download/windows)\
Install Deno [HERE](https://docs.deno.com/runtime/getting_started/installation/)\
A python virtual environment is recommended

### Windows
Here is how to create & activate a virtual environment before installing requirements.txt\
```Bash
cd alexa-shenanigans
python -m venv .alexa-venv
.alexa-venv\Scripts\Activate
```
> cd into the file path of alexa-shenanigans beforehand, you can use cd .. to go back one directory and ls to list current directory's files click [HERE](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands) to find out more.

Next, make sure you have deno installed on your computer. Locate your deno.exe file in your computer, copy it's path, open your Windows Powershell and run `py main.py -c **insert-cookie-path** -d **insert-deno-path** -s`, afterwards you can just run `py main.py` unless you'd like to modify file paths.

### Linux
```Bash
python3 -m venv alexa-shenanigans
cd alexa-shenanigans && source bin/activate
git clone https://github.com/Git-67/Horrible-Alexa.git && cd Horrible-Alexa
```
To run the python code, use `py main.py -c **insert-cookie-path** -d **insert-deno-path** -s`. afterwards you can just run `py main.py` to execute the code unless you'd like to modify file paths.

### Installing dependencies
```Bash
pip install -r requirements.txt
python3 main.py
ollama pull qwen3:14b
```

## Default File Paths
Cookie Path: "yummy_youtube_cookies.txt"\
Deno Path: "C:\Users\HP\.deno\bin\deno.exe"\
> These paths are located in config.json

## Available CLI Arguments
Modify Cookie File Path: `-c **insert-cookie-path**` or `--cookiefile **insert-cookie-path**`\
Modify Deno Path: `-d **insert-deno-path**` or `--deno **insert-deno-path**`\
Saving Configurations: `-s` or `--save`\
Example Usage:`py main.py -c **insert-cookie-path** -d **insert-deno-path** -s`

## Specs
Here are the documentations on the specifications of your device to run this program\
### Recommended
GPU VRAM: 16GB\
System RAM: 32GB\
CPU: 6+ cores\
SSD: 30GB free
### Minimum
GPU VRAM: 12GB\
System RAM: 16GB\
CPU: 4+ cores\
SSD: 20GB free