#!/usr/bin/env python

"""
This program will add an transfrom based on send2url.


"""

# Builtin modules
import os
import zipfile
import tempfile
from string import Template
import argparse

# 3rd party modules.
from lxml import etree
from termcolor import colored


DISCLAIMER = """

This program is tested on Maltego carbon (v3.5) and Maltego Chlorine (v3.6).

"""


"""The .transform represent the base definition of the transform, including
default values.  The base definition includes defining the TransformAdapter,
which is the Java class that is invoked when running the transform.

Here the JavaTransformAdapter will run the Java class given in the
'maltego.transform.java-class-name' property.

In theory we could probably have made some cleverness with abstract and
template, if we needed to define lots of these transforms, however this would
make this tool overly complicated and it doesn't really matter that much that we
generate a bunch of files.

"""
DOT_TRANSFORM = """
<MaltegoTransform name="$nameprefix.transform.$name" displayName="$displayname" abstract="false" template="false"
                  visibility="public" description="$desc" author="$author" requireDisplayInfo="false">
    <TransformAdapter>com.paterva.maltego.transform.runner.test.JavaTransformAdapter</TransformAdapter>
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


"""The .transformsetting represent the settings that the user may change inside
the Maltego GUI, and these will overwrite any settings defined in the .transform
file.  This is where we set the java class that should be executed and any
specific values of the properties that it may reference.

The WebTxTransform class references an 'url' property which it will POST all
selected elements of the current graph to.  The url should return another url,
which Maltego then opens in the users default browser.  If a valid url is not
returned, Maltego will write a warning to the log window containing the returned
text.

"""
DOT_TRANSFORMSETTINGS = """
<TransformSettings enabled="true" disclaimerAccepted="true" showHelp="false">
    <Properties>
        <Property name="url" type="string" popup="false">$url</Property>
        <Property name="maltego.transform.java-class-name" type="string" popup="false">
            com.paterva.maltego.webtx.WebTxTransform
        </Property>
    </Properties>
</TransformSettings>
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


def writetransforms(path, values):
    """Write the .transform and .transformsettings template for this new
    'send2url' transform.

    """
    tname = "%s.transform.%s" % (values.get('nameprefix'), values.get('name'))

    with open(os.path.join(path, "%s.transformsettings" % tname), "wb") as f:
        f.write(Template(DOT_TRANSFORMSETTINGS).safe_substitute(values))

    with open(os.path.join(path, "%s.transform" % tname), "wb") as f:
        f.write(Template(DOT_TRANSFORM).safe_substitute(values))



def updatetas(path, values):
    """Update the TAS file.

    Before transforms are shown inside Maltego, they need to be referenced by a
    transform application server.  In this case a Local "server".

    """
    tname = "%s.transform.%s" % (values.get('nameprefix'), values.get('name'))
    # http://stackoverflow.com/questions/7903759/pretty-print-in-lxml-is-failing-when-i-add-tags-to-a-parsed-tree
    parser = etree.XMLParser(remove_blank_text=True)
    dom = etree.parse(path, parser)
    transforms = dom.findall("./Transforms")

    # Insert a <Transform> element with name set to the name of the transform we
    # are adding.
    etree.SubElement(transforms[0], "Transform", {"name": tname})

    res = etree.tostring(dom, pretty_print=True, encoding='utf8')
    with open(path, "wb") as f:
        f.write(res)


def zip(in_path, file):
    """Add all files and directories inside the given directory to a ZipFile.

    """
    with zipfile.ZipFile(file, mode="w") as zfile:
        # Add files to the zip with write.
        for root, _, files in os.walk(in_path):
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


# Taken from canari.commands.common
def parse_str(question, default):
    """Parse a string from the user.

    If None is supplied, then default is returned.

    """
    return raw_input('%s [%s]: ' % (question, default)) or default

# Taken from canari.commands.common
def parse_bool(question, default=True):
    """Parse a Boolean from the user.

    The Boolean is parsed in the form of y/n or yes/no, with either Y or N as
    the default when the user just hits enter.

    """
    choices = 'Y/n' if default else 'y/N'
    default = 'Y' if default else 'N'
    while True:
        answer = raw_input('%s [%s]: ' % (question, choices)).upper() or default
        if answer.startswith('Y'):
            return True
        elif answer.startswith('N'):
            return False
        else:
            print("Invalid selection: '%s'. Must be either [y]es or [n]o."
                  % answer)

def ask_user(values):
    """Ask the user about information to put into the templates.

    """

    # This code looks ugly and nasty, deal with it.  Keep asking the user until
    # she is happy with the result.
    while True:
        while not values.get('displayname', '').strip():
            values['displayname'] = parse_str("Display name", \
                values.get('displayname', '')).strip()
        # Generate a 'friendly' name from the display name
        values['defaultname'] = values['displayname'].lower().replace(' ', '-')
        values['name'] = parse_str("Name", \
            values.get('name', values.get('defaultname'))).strip().lower()

        # If the user didn't specify a name, use the default generated from
        # displayname.
        if not values['name']:
            values['name'] = values['defaultname']

        while not values.get('nameprefix', '').strip():
            values['nameprefix'] = parse_str("Name prefix", \
                values.get('nameprefix', 'send2url')).strip().lower()
        print("Transform name: %s.transform.%s" %
              (values['nameprefix'], values['name']))
        while not values.get('url', '').strip():
            values['url'] = parse_str("URL", values.get('url', ''))
        values['desc'] = parse_str("Description", values.get('desc', ''))
        values['author'] = parse_str("Author", values.get('author', ''))
        # Keep looping if user aren't happy with the supplied info
        if parse_bool("Are you satisfied with this information? ", True):
            print '' # Make pretty newline...
            break

def main(args):
    """Generates send2url transforms according to the given arguments.

    """
    print colored(DISCLAIMER, "red")


    # Sanity check. If we don't have an input file and an output file, then it
    # gets a bit hard to update the input file with the newly created mtz
    # content.
    if not args.mtz and not args.out:
        print ("%s You must specify either an input file, an output file, or both." %
               colored("[Error]:", "red", None, ['bold']))
        exit(1)

    # Create temporary directory to store the intermediate files.
    tmp_dir = tempfile.mkdtemp()

    if args.mtz:
        # The .mtz file is actually just a zip file. Unpack it so we may add our
        # send2url transforms to it.
        unzip(args.mtz, tmp_dir)

    # Ask the user for values to insert into the send2url templates.
    values = {}
    ask_user(values)

    repo_local_dir = os.path.join(tmp_dir, "TransformRepositories", "Local")
    servers_dir = os.path.join(tmp_dir, "Servers")
    servers_local_tas = os.path.join(servers_dir, "Local.tas")

    # Make sure the directory exists, before we try to write files into it.
    if not os.path.exists(repo_local_dir):
        os.makedirs(repo_local_dir)

    # Write the two templates describing the send2url local transform.
    writetransforms(repo_local_dir, values)

    # By default local transform (seeds) are stored in 'Local.tas'.  If this
    # file doesn't exist, then write a default one.
    if not os.path.exists(servers_dir):
        os.makedirs(servers_dir)
    if not os.path.exists(servers_local_tas):
        with open(servers_local_tas, "wb") as f:
            f.write(LOCALTAS)

    # Add a reference to the newly created transforms inside the 'Local.tas'
    # file.
    updatetas(servers_local_tas, values)

    if not args.out:
        print ("Input file '%s' was updated with the new transform %s." %
               (args.mtz, values.get('displayname')))
        zip(tmp_dir, args.mtz)
    elif args.out == '-':
        # TODO: Implement this
        print colored("Not implemented. Can't write resulting zip file to "
                      "stdout.", 'red')
    elif args.out:
        print ("The new transform %s was merged with input file and written "
               "to '%s'." % (values.get('displayname'), args.out))
        zip(tmp_dir, args.out)



if __name__ == '__main__':
    DESCRIPTION = """
    Generate send2url local-transforms that may be imported into maltego.

    Will unzip the given .mtz file into a temporary location, make the needed
    changes, and write the result back into the given out file.

    """
    PARSER = argparse.ArgumentParser(description=DESCRIPTION)
    PARSER.add_argument('mtz', nargs='?',
                        help='The input .mtz file.')
    PARSER.add_argument('-o', '--out', metavar="file",
                        help='The output file.  If not specified, then the ' \
                             'input file is updated.')

    main(PARSER.parse_args())
