# Democracy watchdog toolkit (CZ)

This is a handful of Python scripts for downloading and analysing votes
in Czech parliament.

## parlament.py

Common class and function library for other scripts

## psp.py

Functions for scraping vote results from website of Lower house of Czech Parliament. Pass stenoprotocol URLs as arguments when calling from command line, the script will automatically process all subsequent stenoprotocol pages of the same Lower house session.

## senat.py

Functions for scraping vote results from Czech Senate website. Pass stenoprotocol URLs as arguments when calling from command line.
