# gmsh Terminal

A (more or less simple) bot that I am building for a server that I moderate. Its main features include:
- A shell-like syntax for a variety of techy commands
- Some auto-reactions to certain keywords (most of them UNDERTALE themed, others are server specific)
- A special viral role that spreads through reactions
- Tutoring infrastructure:
  * roles denoting proficiency (plus role reactions to obtain them)
  * breakout rooms a la Zoom
  * commands to manage these features

Some user ids used are hardcoded: this should be replaced by a database-managed system in the future, combined with a possible web interface.

# Installation

All the required libraries are listed in the `requirements.txt` file.
The project requires at least Python 3.5.3 to run because of Discord.py.
It has been tested with Python 3.8 and 3.9.

To simply run the bot in a docker container, execute `run_container.sh`.
This will build the container from source, and deploy it mounting the provided default paths.

Some information I cannot provide in this repository for security reasons:
this naturally includes the bot token, as well as some private information regarding our server.
Example files starting with _ are provided to detail the required file structure,
fill in your own details to execute. None of this should require changing the container itself.

# License

I wrote all the code in this repository purely for private use.
If any of this turns out to be useful for your project, feel free to yoink it.

_Just don't tell anyone about K's real name._
