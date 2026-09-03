# Horrible Alexa **WIP**
Quite literally what the name says, but homemade by a student. It can adjust your screen's brightness and device volume, play and queue music to your liking, talk with you, and help you write the essay your teacher gave you as homework! (please don't, it's for comedic effect). The future is now!

## Versions
- Python: 3.14 (recommended)
- Ollama: v0.6.6+ (click [here](https://github.com/ollama/ollama/releases) for version info)

## Create a Cookie File
Install the **cookies.txt** Firefox extension, then open the extension while on YouTube Music. Press Copy on Current Site Cookies. Create `yummy_youtube_cookies.txt` locally in the project directory and paste your exported YouTube Music cookies into it. Do not commit this file to Git or share it publicly, as it contains authentication/session data.
>`.gitignore` already excludes `yummy_youtube_cookies.txt`. If you change the cookie filename, remember to update `.gitignore` as well.
> You may use other methods to get your cookies, this is just the one that worked flawlessly for me.

## Dependencies
Install Ollama [HERE](https://ollama.com/download)\
Install Deno [HERE](https://docs.deno.com/runtime/getting_started/installation/)\
A Python virtual environment is heavily recommended

### Windows
Here is how to create & activate a virtual environment before installing requirements.txt
```powershell
git clone https://github.com/Git-67/Horrible-Alexa.git
cd Horrible-Alexa
py -m venv .alexa-venv
.alexa-venv\Scripts\Activate
pip install -r requirements.txt
ollama pull qwen3:14b
```
> Unsure on how to navigate the powershell? Click [HERE](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands) to find out more.
Run the following command to save your cookie and Deno paths and to run the program:
```powershell
py main.py -c "<insert-cookie-path>" -d "<insert-deno-path>" -s
```
For subsequent instances you can simply use:
```powershell
py main.py
```
### Linux
```bash
git clone https://github.com/Git-67/Horrible-Alexa.git
cd Horrible-Alexa
python3 -m venv .alexa-venv
source .alexa-venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3:14b
```

Run the following command to save your cookie and Deno paths and to run the program:
```bash
python3 main.py -c "<insert-cookie-path>" -d "<insert-deno-path>" -s
```
For subsequent instances you can simply use:
```bash
python3 main.py
```

## Default File Paths
Cookie Path: `yummy_youtube_cookies.txt`\
Deno Path: `C:\Users\<USERNAME>\.deno\bin\deno.exe`\
> The default Deno path shown above is for Windows. Linux users should set their Deno path using the `-d` argument. These paths are located in config.json.

## Available CLI Arguments
- Modify Cookie File Path: `-c <insert-cookie-path>` or `--cookiefile <insert-cookie-path>`
- Modify Deno Path: `-d <insert-deno-path>` or `--deno <insert-deno-path>`
- Save Configurations: `-s` or `--save`

## Specs
Here are the recommended and minimum hardware specifications for running this program.
### Recommended
- GPU VRAM: 16GB
- System RAM: 32GB
- CPU: 6+ cores
- SSD: 30GB free
### Minimum
- GPU VRAM: 12GB
- System RAM: 16GB
- CPU: 4+ cores
- SSD: 20GB free
> Lots of VRAM is required due to Qwen3:14b, but trust me, it's worth it.