# Podcatch: Podcast Aggregator

A command line podcast manager for posix systems coded in Python3 and sql for data management. The program manages subscriptions, downloads episodes, and maintains a database of all tracks. Will also transfer these to your android phone via SSH and, in the future, bluetooth.

## Getting Started

Download the project to your chosen directory and unzip the archive. From there you will need to open a terminal (usually ctrl+alt+t on linux based systems) and install the requirements. 

### Prerequisites

Things you will need to run this program:

Note: If you use a non-debian based system (e.g. fedora, redhat, etc.) please substitute the required super user notation and program commands.

1. Python 3.5+

If you don't know if you have it open a terminal (CTRL+ALT+T) and type python3 --version
Most posix systems run some version of python. MacOSx has Python 2.7 installed by default though 3.5+ is still necessary. Depending on your linux distribution 3.5 might already exist.

```
cpiccirilli1@netbook:~⟫ python3 --version
Python 3.5.2
```

To get python3 on linux enter the following:

```
sudo apt-get update
sudo apt-get install python3.5
```

2. pip or your choice of Python package manager.

To see if you have pip (as that is my preferred manager).

```
cpiccirilli1@netbook:~⟫ pip3 --version
pip 8.1.1 from /usr/lib/python3/dist-packages (python 3.5)
```

To install this on your linux system enter the following:

```
sudo apt-get update
sudo apt-get install python-pip
```

3. An internet connection.

Be mindful if you are trying to populate your database or download files without a stable connection. This will throw errors. Error handling is a work in progress. 


### Installing

After you have python3 and pip installed on your system:


* Install 3rd party dependencies:
	* paramiko
	* requests
	* feedparser

```
sudo pip install -r requirements.txt
```

* Move to the directory where it is installed and run without flags.

This will add an alias to your .bash_aliases (Linux) or .bash_profile (MacOSx) and set up the database.

```
python3 podcatch.py
```

* Source your .bash_aliases file or .bash_profile file

```
cpiccirilli1@netbook:~⟫ source .bash_aliases
```

* After, begin by feeding your favorite podcast rss feed. URLs and strings must be in "quotations" 

Familiarize yourself with the argument flags. Sample below.

```
cpiccirilli1@netbook:~⟫ pod -h
usage: podcatch.py [-h] [-f FEED] [--name NAME] [-r] [--update] [--view] [-v]
                   [--recent] [--load] [--series] [--delete] [--current]
                   [--remove] [--sshsend] [--host HOST] [--port PORT]
                   [--user USER] [--pkey PKEY] [-k KEY] [--sshrem REM]
                   [--version]

optional arguments:
  -h, --help    show this help message and exit
  -f FEED       Adds a new feed to the subscription list. Must be used with
                --name. -v is optional use.
  --name NAME   Identifies feed subscription by name you gave when
                subscribing. Names must be in quotation marks.
  -r            Removes a feed from the subscription list. Must be in
                quotation marks.
  --update      Checks for new updates. Can be used with -v
  --view        Displays current subscriptions.
  -v            Displays more information about what the database is doing.
  --recent      Gets the most recent episode.
         --name.

  cont.                
```


* Running commands after set up is a breeze:

```
cpiccirilli1@netbook:~⟫ pod --recent
Updating Database... This may take a moment.
[0] This American Life
        636: I Thought It Would Be Easier 2018/01/21

[1] This American Life
        636: I Thought It Would Be Easier 2018/01/19

```

## Running the tests

To verify that your system is working run:
```
cpiccirilli1@netbook:~⟫ pod --version
version: 0.9.1
```

If you are not on a posix system you will receive an error message.


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* pythonprogramming.net for help with the database calls.
* My family and coworkers for encouragement

## Contact

Feel free to message me here or contact me via email cpiccirilli1@gmail.com for any bugs located.