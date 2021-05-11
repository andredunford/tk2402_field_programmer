# tk2402_radio_programmer

## Introduction
This software was developed to program the settings and channel memory of a Kenwood 2402 VHF radio via serial protocol. Channel information is stored in a local PostgreSQL database, and a UI is provided via custom web interface.

The original intention was to have a portable programmer running on a _raspberry pi_, and interface with it via phone/lapblet/laptop. However, it can can be run direcly on any any system with the requirements indicated within this document.

## Disclaimer
*tk2402_radio_programmer* directly overwrites the contents of the TK2402's integrated EEPROM. *This software is strictly for educational and research purposes, and has the potential to render your radio unusable and void any warranty.* I assume no responsibility or liability for any damages or loss of use to property. Use this software at your own risk. This software may not be used for any commercial application. 

## Hardware Requirements
- Kenwood TK 2402 (I suspect this may work with other 2400 / 3400 series handheld radios, but has not been tested on any other model).  _Please see Disclaimer_.
- Prolific USB-to-Serial cable with Kenwood two-pin connector

## Technologies / Frameworks
- Python 3
- Flask
- Javascript
- PostgreSQL 9

## Installation
Clone the repository and install all python package requirements listed in *requirements.txt*.  It is recommended that a new Python virtual environment is created for this purpose.
### Database Setup
Install PostreSQL and create a database with the structure provided in "pg_dump.sql".  This dump file can be reconstituted with the pg_restore command provided with PostgreSQL.

## Launch
Simply run the script *kenwood_interface.py* which will start a Flask development server on your host computer at 0.0.0.0 port: 5050.
From any browser with network access to the server, navigate to the host adress and port. In the exanple provided, this would be:
> raspi.local:5050



