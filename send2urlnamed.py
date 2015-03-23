#!/usr/bin/env python

"""
This program will add an transfrom based on send2url.


"""

# Builtin modules
import os
import sys
import zipfile
import tempfile
import shutil
import platform
import glob
from string import Template
import argparse

# 3rd party modules.
from lxml import etree
from termcolor import colored


DISCLAIMER = "This program is tested on  Maltego carbon and Maltego Chlorine."


DOT_TRANSFORMSETTINGS = """
<TransformSettings enabled="true" disclaimerAccepted="true" showHelp="false">
    <Properties>
        <Property name="url" type="string" popup="false">$link</Property>
        <Property name="maltego.transform.java-class-name" type="string" popup="false">
            com.paterva.maltego.webtx.WebTxTransform
        </Property>
    </Properties>
</TransformSettings>
"""


DOT_TRANSFORM = """
<MaltegoTransform name="maltego.transform.$name" displayName="$name" abstract="false" template="false"
                  visibility="public" description="$desc" author="$author" requireDisplayInfo="false">
    <TransformAdapter>
        com.paterva.maltego.transform.runner.test.JavaTransformAdapter
    </TransformAdapter>
    <Properties>
        <Fields>
            <Property name="url" type="string" nullable="false" hidden="false" readonly="false"
                      popup="false" abstract="false" visibility="public" displayName="URL">
                <SampleValue></SampleValue>
            </Property>
            <Property name="maltego.transform.java-class-name" type="string" nullable="false"
                      hidden="false" readonly="true" popup="false" abstract="false"
                      visibility="hidden" displayName="Class">
                <SampleValue></SampleValue>
            </Property>
        </Fields>
    </Properties>
    <InputConstraints>
        <Entity min="1" max="0"/>
    </InputConstraints>
    <OutputEntities/>
    <defaultSets/>
    <StealthLevel>0</StealthLevel>
</MaltegoTransform>
"""


LOCALTAS = """
<MaltegoServer name="Local" enabled="true" description="Local transforms hosted on this machine"
               url="http://localhost">
    <LastSync>2015-01-01 00:00:00.000 CEST</LastSync>
    <Protocol version="0.0"/>
    <Authentication type="none"/>
    <Transforms>
    </Transforms>
</MaltegoServer>
"""


def writetransforms(name, link, desc, author, path):
    """Write the .transform and .transformsettings template for this new send2url
    transform.

    """

    out = Template(DOT_TRANSFORMSETTINGS).safe_substitute({'name':name, 'link':link})
    with open(os.path.join(path, "maltego.transform." + name + ".transformsettings"), "wb") as f:
        f.write(out)

    out = Template(DOT_TRANSFORM).safe_substitute({'name':name, 'link':link, 'desc':desc, 'author':author})
    with open(os.path.join(path, "maltego.transform." + name + ".transform"), "wb") as f:
        f.write(out)



def insert_transform(e, name):
    """use this if actions is defined

    """




def updateTAS(path, name, link):
    """Update the TAS file.

    Before transforms are shown inside Maltego, they need to be referenced by a
    transform application server.  In this case a Local "server".

    """
    dom = etree.parse(path)
    actions = dom.findall("./Transforms")

    # Insert the reference to the transform.
    name = "maltego.transform." + name
    etree.SubElement(actions[0], "Transform", {"name": name})

    res = etree.tostring(dom)
    with open(path, "wb") as fil:
        fil.write(res)


def zip(in_path, file):
    """Add all files and directories inside the given directory to a ZipFile.

    """
    with zipfile.ZipFile(file, mode="w") as zfile:
        # Add files to the zip with write.
        for root, dirs, files in os.walk(in_path):
            for file in files:
                filepath = os.path.join(root, file)
                # We need to store the file relative to the in_path folder,
                # inside the zipfile.
                arcname = os.path.relpath(filepath, in_path)
                zfile.write(filepath, arcname=arcname)


def unzip(file, out_path):
    """Unzip all files of a given ZipFile into the specified directory.

    """
    with zipfile.ZipFile(file) as zfile:
        zfile.extractall(path=out_path)


def main(args):
    print colored(DISCLAIMER,"red")

    infile = args.mtz

    # Create temporary directory to store the intermediate files.
    tmp_dir = tempfile.mkdtemp()

    # The .mtz file is actually just a zip file. Unpack it so we may add our
    # send2url transforms to it.
    unzip(infile, tmp_dir)

    # Ask the user for values to insert into the send2url templates.
    author  = raw_input("Author        : ")
    name = raw_input("Name          : ")
    link = raw_input("Link          : ")
    desc = raw_input("Description   : ")

    repo_local_dir = os.path.join(tmp_dir, "TransformRepositories", "Local")
    servers_dir = os.path.join(tmp_dir, "Servers")
    servers_local_tas = os.path.join(servers_dir, "Local.tas")

    # Make sure the directory exists, before we try to write files into it.
    if not os.path.exists(repo_local_dir):
        os.makedirs(repo_local_dir)

    # Write the two templates describing the send2url local transform.
    writetransforms(name, link, desc, author, repo_local_dir)

    # By default local transform (seeds) are stored in 'Local.tas'.  If this
    # file doesn't exist, then write a default one.
    if not os.path.exists(servers_dir):
        os.makedirs(servers_dir)
    if not os.path.exists(servers_local_tas):
        with open(servers_local_tas, "wb") as f:
            f.write(LOCALTAS)


    updateTAS(servers_local_tas, name, link)

    if args.out:
        zip(tmp_dir, args.out)
        print colored("File is done...", "blue")



if __name__ == '__main__':
    description = """
    Generate send2url local-transforms that may be imported into maltego.

    Will unzip the given .mtz file into a temporary location, make the needed
    changes, and write the result back into the given out file.

    """
    PARSER = argparse.ArgumentParser(description=description)
    PARSER.add_argument('mtz', help='The input .mtz file.')
    PARSER.add_argument('-o', '--out', metavar="file",
                        help='The output file.  If not specified, then the input file is updated.')

    main(PARSER.parse_args())
