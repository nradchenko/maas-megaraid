#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Nikita Radchenko"
__email__ = "nradchenko@protonmail.com"

# --- Start MAAS 1.0 script metadata ---
# name: 00-maas-00-megaraid
# title: Configure LSI MegaRAID
# description: Configures LSI MegaRAID (creates RAID)
# tags: commissioning
# type: commissioning
# timeout: 30
# destructive: False
# packages:
#   apt:
#     - python3
#     - alien
#   url:
#     - https://docs.broadcom.com/docs-and-downloads/raid-controllers/raid-controllers-common-files/8-07-14_MegaCLI.zip
#     - https://github.com/nradchenko/megacli-python/archive/raid10.zip
# for_hardware:
#   - pci:1000
# parallel: disabled
# may_reboot: False
# recommission: False
# script_type: commissioning
# --- End MAAS 1.0 script metadata ---

import os
import sys
import subprocess

from glob import glob
from collections import Counter

DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH')

try:
    assert (len(DOWNLOAD_PATH))
except AssertionError:
    raise RuntimeError("'DOWNLOAD_PATH' environment variable is empty (this should never happen)")

try:
    sys.path.insert(0, glob("{}/megacli-python-*".format(DOWNLOAD_PATH))[0])
    from megacli import MegaCLI
except (IndexError, ImportError):
    raise RuntimeError("Could not find megacli-python module at DOWNLOAD_PATH (this should never happen)")

# RAID level (e.g. 0, 1, 5, 6, 10)
RAID_LEVEL = 10
# Minimum required number of drives to use (depends on RAID level)
MIN_DRIVES = 4
# Maxumim number of drives to use (depends on RAID level)
MAX_DRIVES = 8

# Device write policy (WT or WB)
WRITE_POLICY = 'WB'
# Device read policy (NORA, RA or ADRA)
READ_POLICY = 'RA'
# Device cache policy (Direct or Cached)
CACHE_POLICY = 'Direct'
# Enable write cache if BBU is bad (True or False)
CACHED_BAD_BBU = False
# Device stripe size (8, 16, 32, 64, 128, 256, 512, or 1024)
STRIPE_SIZE = 1024

# MegaCli64 utility path
MEGACLI = "/opt/MegaRAID/MegaCli/MegaCli64"


def install_megacli():
    """Installs megacli utility package (downloaded by MAAS)
    """
    if not os.path.exists(MEGACLI):
        subprocess.check_output("alien -d -i {}/Linux/MegaCli-*.noarch.rpm".format(DOWNLOAD_PATH), shell=True,
                                stderr=subprocess.PIPE)


def main():
    install_megacli()

    cli = MegaCLI(MEGACLI)

    adapters = cli.adapters()
    logicaldrives = cli.logicaldrives()
    physicaldrives = cli.physicaldrives()

    if not len(adapters):
        print("No adapters detected")
        return

    for adapter in adapters:
        print("Examining adapter #{} ({})".format(adapter["id"], adapter["product_name"]))

        if [x for x in logicaldrives if x["adapter_id"] == adapter["id"] and len(x) > 1]:
            print("Found existing logical drives, skipping")
            continue

        # Find unconfigured physical drives
        unconfigured = [x for x in physicaldrives if
                        x["adapter_id"] == adapter["id"] and x["firmware_state"] == "unconfigured(good), spun up"]

        if not len(unconfigured):
            print("No drives to build array from, skipping")
            continue
        else:
            print("Found {} unconfigured drives".format(len(unconfigured)))

        # Pick a bunch of drives of the same size
        size, count = Counter([x["raw_size"] for x in unconfigured]).most_common(1)[0]
        drives = [x for x in unconfigured if x["raw_size"] == size]
        print("Found {} drives of size {} GiB".format(count, int(size // 1024 ** 3)))

        # Do checks
        if MIN_DRIVES and len(drives) < MIN_DRIVES:
            print("Not enough drives to build RAID {} from (have {}, required {})".format(RAID_LEVEL, len(drives),
                                                                                          MIN_DRIVES))
            continue

        drives = drives[:MAX_DRIVES]
        print("Ready to build RAID {} from {} drives".format(RAID_LEVEL, len(drives)))

        # Build RAID
        cli.create_ld(raid_level=RAID_LEVEL,
                      devices=["{}:{}".format(x["enclosure_id"], x["slot_number"]) for x in drives],
                      adapter=adapter["id"],
                      write_policy=WRITE_POLICY, read_policy=READ_POLICY,
                      cache_policy=CACHE_POLICY, cached_bad_bbu=CACHED_BAD_BBU,
                      stripe_size=STRIPE_SIZE)

        print("Created RAID {}, no errors reported".format(RAID_LEVEL))

    print("DONE")


if __name__ == "__main__":
    main()
