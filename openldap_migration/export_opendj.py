#!/usr/bin/python

import traceback
import sys
import os
import shutil
import hashlib
import getpass
import tempfile
import logging

# Unix commands
mkdir = '/bin/mkdir'
cat = '/bin/cat'
hostname = '/bin/hostname'
grep = '/bin/grep'
ldapsearch = "/opt/opendj/bin/ldapsearch"
unzip = "/usr/bin/unzip"
find = "/usr/bin/find"
mkdir = "/bin/mkdir"

log = "./export_opendj.log"
logError = "./export_opendj.error"
bu_folder = "./opendj_export"
propertiesFn = "%s/setup.properties" % bu_folder

# LDAP Stuff
password_file = tempfile.mkstemp()[1]
ldap_creds = ['-h', 'localhost', '-p', '1636', '-Z', '-X', '-D',
              '"cn=directory manager"', '-j', password_file]
base_dns = ['ou=people',
            'ou=groups',
            'ou=attributes',
            'ou=scopes',
            'ou=clients',
            'ou=scripts',
            'ou=uma',
            'ou=hosts',
            'ou=u2f']

# configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    filename='export_24.log',
                    filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


def clean(s):
    return s.replace('@', '').replace('!', '').replace('.', '')


def copyFile(fn, dir):
    parent_Dir = os.path.split(fn)[0]
    bu_dir = "%s/%s" % (bu_folder, parent_Dir)
    if not os.path.exists(bu_dir):
        runCommand([mkdir, "-p", bu_dir])
    bu_fn = os.path.join(bu_dir, os.path.split(fn)[-1])
    shutil.copyfile(fn, bu_fn)


def getOrgInum():
    args = [ldapsearch] + ldap_creds + ['-s', 'one', '-b', 'o=gluu',
                                        'o=*', 'dn']
    output = runCommand(args)
    return output.split(",")[0].split("o=")[-1]


def getLdif():
    logging.info('Creating backup of LDAP data')
    orgInum = getOrgInum()
    # Backup the data
    for basedn in base_dns:
        args = [ldapsearch] + ldap_creds + [
            '-b', '%s,o=%s,o=gluu' % (basedn, orgInum), 'objectclass=*']
        output = runCommand(args)
        ou = basedn.split("=")[-1]
        f = open("%s/ldif/%s.ldif" % (bu_folder, ou), 'w')
        f.write(output)
        f.close()

    # Backup the appliance config
    args = [ldapsearch] + ldap_creds + \
           ['-b',
            'ou=appliances,o=gluu',
            '-s',
            'one',
            'objectclass=*']
    output = runCommand(args)
    f = open("%s/ldif/appliance.ldif" % bu_folder, 'w')
    f.write(output)
    f.close()

    # Backup the oxtrust config
    args = [ldapsearch] + ldap_creds + \
           ['-b',
            'ou=appliances,o=gluu',
            'objectclass=oxTrustConfiguration']
    output = runCommand(args)
    f = open("%s/ldif/oxtrust_config.ldif" % bu_folder, 'w')
    f.write(output)
    f.close()

    # Backup the oxauth config
    args = [ldapsearch] + ldap_creds + \
           ['-b',
            'ou=appliances,o=gluu',
            'objectclass=oxAuthConfiguration']
    output = runCommand(args)
    f = open("%s/ldif/oxauth_config.ldif" % bu_folder, 'w')
    f.write(output)
    f.close()

    # Backup the trust relationships
    args = [ldapsearch] + ldap_creds + ['-b', 'ou=appliances,o=gluu',
                                        'objectclass=gluuSAMLconfig']
    output = runCommand(args)
    f = open("%s/ldif/trust_relationships.ldif" % bu_folder, 'w')
    f.write(output)
    f.close()

    # Backup the org
    args = [ldapsearch] + ldap_creds + ['-s', 'base', '-b',
                                        'o=%s,o=gluu' % orgInum,
                                        'objectclass=*']
    output = runCommand(args)
    f = open("%s/ldif/organization.ldif" % bu_folder, 'w')
    f.write(output)
    f.close()

    # Backup o=site
    args = [ldapsearch] + ldap_creds + ['-b', 'ou=people,o=site',
                                        '-s', 'one', 'objectclass=*']
    output = runCommand(args)
    f = open("%s/ldif/site.ldif" % bu_folder, 'w')
    f.write(output)
    f.close()


def runCommand(args, return_list=False):
        try:
            logging.debug("Running command : %s", " ".join(args))
            output = None
            if return_list:
                output = os.popen(" ".join(args)).readlines()
            else:
                output = os.popen(" ".join(args)).read().strip()
            return output
        except:
            logging.error("Error running command : %s", " ".join(args))
            logging.debug(traceback.format_exc())
            sys.exit(1)


def getProp(prop):
    with open('/install/community-edition-setup/setup.properties.last', 'r') \
            as sf:
        for line in sf:
            if "{0}=".format(prop) in line:
                return line.split('=')[-1].strip()


def genProperties():
    logging.info('Creating setup.properties backup file')
    props = {}
    props['ldapPass'] = runCommand([cat, password_file])
    props['hostname'] = runCommand([hostname])
    props['inumAppliance'] = runCommand(
        [grep, "^inum", "%s/ldif/appliance.ldif" % bu_folder]
    ).split("\n")[0].split(":")[-1].strip()
    props['inumApplianceFN'] = clean(props['inumAppliance'])
    props['inumOrg'] = getOrgInum()
    props['inumOrgFN'] = clean(props['inumOrg'])
    props['baseInum'] = props['inumOrg'][:21]
    props['encode_salt'] = runCommand(
        [cat, "/opt/tomcat/conf/salt"]).split("=")[-1].strip()

    props['oxauth_client_id'] = getProp('oxauth_client_id')
    props['scim_rs_client_id'] = getProp('scim_rs_client_id')
    props['scim_rp_client_id'] = getProp('scim_rp_client_id')
    props['version'] = getProp('githubBranchName').split('_')[-1]
    # As the certificates are copied over to the new installation, their pass
    # are required for accessing them and validating them
    props['httpdKeyPass'] = getProp('httpdKeyPass')
    props['shibJksPass'] = getProp('shibJksPass')
    props['asimbaJksPass'] = getProp('asimbaJksPass')

    # Preferences for installation of optional components
    installSaml = raw_input("\tIs Shibboleth SAML IDP installed? (Y/N):")
    props['installSaml'] = 'y' in installSaml.lower()
    props['installAsimba'] = os.path.isfile('/opt/tomcat/webapps/asimba.war')
    props['installCas'] = os.path.isfile('/opt/tomcat/webapps/cas.war')
    props['installOxAuthRP'] = os.path.isfile(
        '/opt/tomcat/webapps/oxauth-rp.war')

    f = open(propertiesFn, 'a')
    for key in props.keys():
        # NOTE: old version of setup.py will interpret any string as True
        #       Hence, store only the True values, the defaults are False
        if props[key]:
            f.write("%s=%s\n" % (key, props[key]))
    f.close()


def hash_file(filename):
    # From http://www.programiz.com/python-programming/examples/hash-file
    h = hashlib.sha1()
    with open(filename, 'rb') as file:
        chunk = 0
        while chunk != b'':
            chunk = file.read(1024)
            h.update(chunk)
    return h.hexdigest()


def makeFolders():
    folders = [bu_folder, "%s/ldif" % bu_folder]
    for folder in folders:
        try:
            if not os.path.exists(folder):
                runCommand([mkdir, '-p', folder])
        except:
            logging.error("Error making folder: %s", folder)
            logging.debug(traceback.format_exc())
            sys.exit(3)


def prepareLdapPW():
    ldap_pass = None
    # read LDAP pass from setup.properties
    with open('/install/community-edition-setup/setup.properties.last', 'r') \
            as sfile:
        for line in sfile:
            if 'ldapPass=' in line:
                ldap_pass = line.split('=')[-1]
    # write it to the tmp file
    with open(password_file, 'w') as pfile:
        pfile.write(ldap_pass)
    # perform sample search
    sample = getOrgInum()
    if not sample:
        # get the password from the user if it fails
        ldap_pass = getpass.getpass("Enter LDAP Passsword: ")
        with open(password_file, 'w') as pfile:
            pfile.write(ldap_pass)


def main():
    prepareLdapPW()
    makeFolders()
    getLdif()
    genProperties()

    # remove the tempfile with the ldap password
    os.remove(password_file)

if __name__ == "__main__":
    main()
