# Versions
Python : 3.14

## Create Cookie File

Install "cookies.txt" Firefox extension and then open the extension whilst on your Youtube Music. 
Afterwards, press copy on current site cookies. Add a new file titled "yummy-youtube-cookies.txt" 
in this repo, inside with your pasted cookies. Then you can run the python code.

## Dependencies
Install Deno [READ HERE](#deno-linking) and ffmpeg
A python virtual environment is recommended on linux
### Linux
```Bash
python3 -m venv alexasugoi
cd alexasugoi && source bin/activate
git clone https://github.com/Git-67/Horrible-Alexa.git && cd Horrible-Alexa
```
### Installing dependencies
```Bash
pip install -r requirements.txt
python3 cool.py
```
### The author of this commit does not have a windows or a mac machine and as such cannot document for them.
###
## Deno Linking

Make sure you have deno installed on your computer, if not, download it from [here](https://docs.deno.com/runtime/getting_started/installation/). 
On Windows, Locate your deno.exe file in your computer, copy it's path, open your terminal and run `py cool.py **insert-path**`. Linux is the 
same process but it's not in .exe format.
