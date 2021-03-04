# gmsh Terminal

A (more or less simple) bot that I am building for a server that I moderate. Its main features include:
- A shell-like syntax for a variety of techy commands
- Some auto-reactions to certain keywords (most of them UNDERTALE themed, others are server specific)
- A special viral role that spreads through reactions
- Tutoring infrastructure:
  * roles denoting proficiency (plus role reactions to obtain them)
  * breakout rooms a la Zoom
  * commands to manage these features

# Installation

All the required libraries are listed in the requirements.txt file.
The project requires at least Python 3.5.3 to run because of Discord.py.
It has been only tested with Python 3.6.9 and Python 3.8.

Some user ids used are hardcoded: this should be replaced by a database-managed system in the future, combined with a possible web interface.

With the latest rewrite I have added Docker infrastructure, so it should now be possible
to simply set up this bot using `docker-compose`. I have not worked out a way to efficiently migrate
the legacy or development databases to the new PostgreSQL container, and I am also not sure
how to make the DB persist after downing and redeploying the network.

# License

I wrote all the code in this repository purely for private use. If any of this turns out to be useful for your project, feel free to yoink it.

_Just don't tell anyone about K's real name._
