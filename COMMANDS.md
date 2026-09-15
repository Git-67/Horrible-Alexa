# Commands for Pluto
## What are commands?
Commands are hard-coded strings the code in `main.py` detects for which will then act out as said by Pluto. There are concurrently 9 different commands, each may have their own arguments with Pluto can use.
> We are coming up with **more** commands Pluto can use, which can make it even more dynamic and useful.
## What's the structure of the commands?
Every command must be used at the end of Pluto's reply, meaning it must also be seperate from the actual reply. Every command also starts with a /command as a baseline for checking whether there is a command Pluto wants to execute, as not every reply necessarily needs a command.
## What are some commands Pluto has?
Pluto has several commands, here's the list of them and their arguments:
- /command brightness <up/down>: Increases / Decreases Brightness by 25%
- /command volume <up/down>: Increases / Decreases Volume by 25%
- /command play <song-title>: Plays the song user requests, double checks before downloading, and wil queue the song instead if a song is already playing
- /command stop-music: Clears the queue and stops the song
- /command write <texts>: Generate Texts based on User's Requests and pastes into their clipboard
- /command alarm at <time-in-%H:%M> <purpose-of-alarm>: Sets an alarm for a specific clock time
- /command alarm in <minutes> <purpose-of-alarm>: Sets an alarm N minutes from now
- /command alarm-remove <time-in-%H:%M>: Removes an alarm if there is one set based on user's requested time
- /command quit: Ends the concurrent instance of the program
## Planned / In Progress commands
As this is a WIP, more and more commands will be added in the future, here's some of our concurrent ideas:
- /command remove-music <song-title>: Removes first instance of this music from song queue
- /command music-queue: Reads out concurrent music queue to user
- /command alarm-queue: Reads out all alarms set by the user
- /command zen <play/end/minutes/time-in-%H:%M>: plays lofi in the background, ends lofi in the background, plays lofi in the background N minutes from now, or plays lofi in the background for a specified duration
- /command alarm at <time-in-%H:%M> <purpose-of-alarm> important: Sets an alarm for a specific clock time & plays an actual alarm sound to wake user up
- /command alarm in <minutes> <purpose-of-alarm> important: Sets an alarm N minutes from now & plays an actual alarm sound to wake user up