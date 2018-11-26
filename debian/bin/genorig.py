#!/usr/bin/python3

import sys
import tempfile
import subprocess
import re
import os
import glob
import shutil

def main(tarball):
    target_dir = tempfile.mkdtemp(prefix='genorig', dir='debian')

    print("Extracting tarball %s" % tarball)
    cmdline = ['tar', '-xaf', tarball, '-C', target_dir]
    subprocess.check_call(cmdline)

    print("Excluding file patterns specified in debian/copyright")
    match = re.search('Files-Excluded:(?P<files>[ a-zA-Z0-9/\.\*\n]*)Comment:',
                      open('debian/copyright', 'r').read())

    files_excluded = match.group('files').split('\n')
    # For all pattern
    for pattern in files_excluded:
        pattern = pattern.replace(" ", "")

        if not pattern:
            continue

        # Resolve the sub glob patterns and remove all subtrees and files
        global_pattern = target_dir + "/firmware-*/" + pattern
        for f in glob.glob(global_pattern):
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)

        # Once done, resolve the directory itself
        if global_pattern.endswith("/*"):
            global_pattern = glob.glob(global_pattern.replace("/*", ""))[0]

        # if the global pattern was a directory, remove it (empty)
        if os.path.isdir(global_pattern):
            os.rmdir(global_pattern)

    print("Including brcm80211 firmwares")
    brcm_dir = glob.glob(target_dir + "/firmware-*")[0] + "/brcm80211"
    os.mkdir(brcm_dir)
    cmdline = [
        'wget',
        '-q',
        'https://raw.githubusercontent.com/RPi-Distro/firmware-nonfree/master/brcm/brcmfmac43430-sdio.txt',
        '-O',
        brcm_dir + "/brcmfmac43430-sdio.txt"
    ]
    subprocess.check_call(cmdline)
    cmdline = [
        'wget',
        '-q',
        'https://raw.githubusercontent.com/RPi-Distro/firmware-nonfree/master/LICENCE.broadcom_bcm43xx',
        '-O',
        brcm_dir + "/LICENSE"
    ]
    subprocess.check_call(cmdline)


    match = re.match("firmware-(?P<version>[0-9\.]+).tar.gz", os.path.basename(tarball))
    if not match:
        print("Unable to extract version from %s" % tarball)
        os.exit(1)
    version = match.group("version")
    new_tarball = "../raspi3-firmware_" + version + ".orig.tar.xz"

    print("Generate tarball %s" % new_tarball)
    cmdline = [
        'tar',
        '-C', target_dir,
        '--sort=name',
        '--owner=root',
        '--group=root',
        '--use-compress-program=xz -T0',
        '-cf',
        new_tarball,
        'firmware-' + version
    ]
    subprocess.check_call(cmdline)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('''\
Usage: {} TARBALL"
TARBALL is the new upstream tarball to repack'''.format(sys.argv[0]),
              file=sys.stderr)
        sys.exit(1)
    main(*sys.argv[1:])
