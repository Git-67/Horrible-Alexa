# Commands for Pluto
## What are commands?
Commands are hard-coded strings the code in `main.py` detects for which will then act out as said by Pluto. There are concurrently 9 different commands, each may have their own arguments with Pluto can use.
> We are coming up with **more** commands Pluto can use, which can make it even more dynamic and useful. It may look overwhelming and you may think it's feature bloat. Usually, multiple commands come together to make one feature so it's actually pretty decent.
## What's the structure of the commands?
Every command must be used at the end of Pluto's reply, meaning it must also be seperate from the actual reply. Every command also starts with a `/command` as a baseline for checking whether there is a command Pluto wants to execute, as not every reply necessarily needs a command.
## What are some commands Pluto has?
Pluto has several commands, here's the list of them and their arguments:
| Command | Arguments | Description | Status |
| --- | --- | --- | :---: |
| `/command brightness` | `up/down` | Changes brightness by 25% | ✔️ |
| `/command volume` | `up/down` | Changes volume by 25% | ✔️ |
| `/command play` | `<song-title>` | Plays or queues a song | ✔️ |
| `/command stop-music` | None | Stops music and clears the queue | ✔️ |
| `/command write` | `<text>` | Generates text and copies it to the clipboard | ✔️ |
| `/command alarm at` | `<HH:MM> <purpose>` | Sets an alarm for a specific time | ✔️ |
| `/command alarm in` | `<minutes> <purpose>` | Sets an alarm after a duration | ✔️ |
| `/command alarm-remove` | `<HH:MM>` | Removes an alarm | ✔️ |
| `/command quit` | None | Exits Pluto | ✔️ |
## Planned / In Progress commands
As this is a WIP, more and more commands will be added in the future, here's some of our concurrent ideas:
| Command | Arguments | Description | Status |
| --- | --- | --- | :---: |
| `/command remove-music` | `<song-title>` | Removes the first instance of the specified song from the music queue. | WIP |
| `/command music-queue` | None | Reads out the current music queue to the user. | WIP |
| `/command alarm-queue` | None | Reads out all alarms currently set by the user. | WIP |
| `/command zen` | `<play/end/minutes/time-in-%H:%M>` | Plays lofi in the background, ends lofi playback, starts lofi after N minutes, or plays lofi for a specified duration. | Debating |
| `/command alarm at` | `<time-in-%H:%M> <purpose-of-alarm> important` | Sets an important alarm for a specific clock time and plays an actual alarm sound when triggered. | Debating |
| `/command alarm in` | `<minutes> <purpose-of-alarm> important` | Sets an important alarm N minutes from now and plays an actual alarm sound when triggered. | Debating |