maas-megaraid
=============
[MAAS](https://maas.io) commissioning script that configures LSI MegaRAID

Installation
------------
1. Edit `maas-megaraid.py` according to your needs (set `RAID_LEVEL`, `MIN_DRIVES`, `MAX_DRIVES`, etc)
2. Upload the script in MAAS web interface: Settings - Commissioning scripts - Upload

You can also create a set of scripts to configure different RAID levels and choose between them when
commissioning new nodes.

Having multiple scripts requires setting a unique `name` metadata field value for each script before upload
(e.g. `00-maas-00-megaraid-raid10`, `00-maas-00-megaraid-raid6`).

How it works?
-------------
The script finds a set of unconfigured drives of the same size and creates a logical drive
with settings specified.

If number of drives is insufficient to build a logical drive or any logical drives are present
then nothing would be done.

Existing logical drives are never removed, so you might need to remove them manually (using MegaCli or WebBIOS)
before running a commissioning procedure.

References
----------
https://maas.io/docs/commissioning-and-hardware-testing-scripts
