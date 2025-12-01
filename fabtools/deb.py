"""
Debian packages
===============

This module provides tools to manage Debian/Ubuntu packages
and repositories.

"""

from hashlib import md5

from fabric.api import hide, run, settings

from fabtools.utils import run_as_root
from fabtools.files import getmtime, is_file, is_dir, copy, remove


MANAGER = 'DEBIAN_FRONTEND=noninteractive apt-get'


def update_index(quiet=True):
    """
    Update APT package definitions.
    """
    options = "--quiet --quiet" if quiet else ""
    run_as_root("%s %s update" % (MANAGER, options))


def upgrade(safe=True):
    """
    Upgrade all packages.
    """
    manager = MANAGER
    if safe:
        cmd = 'upgrade'
    else:
        cmd = 'dist-upgrade'
    run_as_root("%(manager)s --assume-yes %(cmd)s" % locals(), pty=False)


def is_installed(pkg_name):
    """
    Check if a package is installed.
    """
    with settings(
            hide('running', 'stdout', 'stderr', 'warnings'), warn_only=True):
        res = run("dpkg -s %(pkg_name)s" % locals())
        for line in res.splitlines():
            if line.startswith("Status: "):
                status = line[8:]
                if "installed" in status.split(' '):
                    return True
        return False


def install(packages, update=False, options=None, version=None):
    """
    Install one or more packages.

    If *update* is ``True``, the package definitions will be updated
    first, using :py:func:`~fabtools.deb.update_index`.

    Extra *options* may be passed to ``apt-get`` if necessary.

    Example::

        import fabtools

        # Update index, then install a single package
        fabtools.deb.install('build-essential', update=True)

        # Install multiple packages
        fabtools.deb.install([
            'python-dev',
            'libxml2-dev',
        ])

        # Install a specific version
        fabtools.deb.install('emacs', version='23.3+1-1ubuntu9')

    """
    manager = MANAGER
    if update:
        update_index()
    if options is None:
        options = []
    if version is None:
        version = ''
    if version and not isinstance(packages, list):
        version = '=' + version
    if not isinstance(packages, basestring):
        packages = " ".join(packages)
    options.append("--quiet")
    options.append("--assume-yes")
    options = " ".join(options)
    cmd = '%(manager)s install %(options)s %(packages)s%(version)s' % locals()
    run_as_root(cmd, pty=False)


def uninstall(packages, purge=False, options=None):
    """
    Remove one or more packages.

    If *purge* is ``True``, the package configuration files will be
    removed from the system.

    Extra *options* may be passed to ``apt-get`` if necessary.
    """
    manager = MANAGER
    command = "purge" if purge else "remove"
    if options is None:
        options = []
    if not isinstance(packages, basestring):
        packages = " ".join(packages)
    options.append("--assume-yes")
    options = " ".join(options)
    cmd = '%(manager)s %(command)s %(options)s %(packages)s' % locals()
    run_as_root(cmd, pty=False)


def preseed_package(pkg_name, preseed):
    """
    Enable unattended package installation by preseeding ``debconf``
    parameters.

    Example::

        import fabtools

        # Unattended install of Postfix mail server
        fabtools.deb.preseed_package('postfix', {
            'postfix/main_mailer_type': ('select', 'Internet Site'),
            'postfix/mailname': ('string', 'example.com'),
            'postfix/destinations': ('string', 'example.com, localhost.localdomain, localhost'),
        })
        fabtools.deb.install('postfix')

    """
    for q_name, _ in preseed.items():
        q_type, q_answer = _
        run_as_root('echo "%(pkg_name)s %(q_name)s %(q_type)s %(q_answer)s" | debconf-set-selections' % locals())


def get_selections():
    """
    Get the state of ``dkpg`` selections.

    Returns a dict with state => [packages].
    """
    with settings(hide('stdout')):
        res = run_as_root('dpkg --get-selections')
    selections = dict()
    for line in res.splitlines():
        package, status = line.split()
        selections.setdefault(status, list()).append(package)
    return selections


def apt_key_exists(keyid):
    """
    Check if the given key id exists in apt keyring.
    """
    if locate_apt_key(keyid) is not None:
        return True

    return False


def locate_apt_key(keyid):
    """
    Locate the given key id in apt keyring.
    """
    from fabtools.require.deb import package as require_package
    require_package('gpg')

    keyring_list = []

    trusted_file = '/etc/apt/trusted.gpg'
    if is_file(trusted_file):
        keyring_list.append(trusted_file)

    trusted_parts = '/etc/apt/trusted.gpg.d'
    if is_dir(trusted_parts):
        res = run('(shopt -s dotglob; ls -N -d -1 %s/*.gpg)' % trusted_parts, quiet=True)
        if res.succeeded:
            keyring_list.extend(res.splitlines())

    for keyring in keyring_list:
        # Command extracted from apt-key source
        gpg_cmd = 'gpg --ignore-time-conflict --no-options --no-default-keyring --keyring %s' % keyring

        res = run('%s --fingerprint %s' % (gpg_cmd, keyid), quiet=True)
        if res.succeeded:
            return keyring


def _check_pgp_key(path, keyid):
    with settings(hide('everything')):
        return not run('set -o pipefail; gpg --quiet --with-colons %s | cut -d: -f 5 | grep -q \'%s$\'' % (path, keyid))


def _dearmor_pgp_key(filename):
    tmp_filename = '/tmp/tmp.fabtools.apt_key.%s.gpg' % md5(filename).hexdigest()
    with settings(hide('everything')):
        run_as_root('gpg --yes --output %s --dearmor %s' % (tmp_filename, filename))
    return tmp_filename


def _get_pubid_gpg_key(filename):
    with settings(hide('everything')):
        res = run_as_root('set -o pipefail; gpg --quiet --with-colons %s | egrep -o "pub:.*" | cut -d: -f 5' % filename)
    return str(res)


def _add_pgp_key(filename):
    pubid = _get_pubid_gpg_key(filename)
    destname = 'imported_key_%s.gpg' % pubid
    with settings(hide('everything')):
        copy(filename, '/etc/apt/trusted.gpg.d/%s' % destname, use_sudo=True)
        remove(filename, force=True, use_sudo=True)
    return destname


def add_apt_key(filename=None, url=None, keyid=None, keyserver='subkeys.pgp.net', update=False):
    """
    Trust packages signed with this public key.

    Example::

        import fabtools

        # Varnish signing key from URL and verify fingerprint)
        fabtools.deb.add_apt_key(keyid='C4DEFFEB', url='http://repo.varnish-cache.org/debian/GPG-key.txt')

        # Nginx signing key from default key server (subkeys.pgp.net)
        fabtools.deb.add_apt_key(keyid='7BD9BF62')

        # From custom key server
        fabtools.deb.add_apt_key(keyid='7BD9BF62', keyserver='keyserver.ubuntu.com')

        # From a file
        fabtools.deb.add_apt_key(keyid='7BD9BF62', filename='nginx.asc'
    """
    from fabtools.require.deb import package as require_package
    require_package('gpg')

    if keyid is None:
        if filename is not None:
            _add_pgp_key(_dearmor_pgp_key(filename))
        elif url is not None:
            tmp_key = '/tmp/tmp.fabtools.apt_key.%s.key' % md5(url).hexdigest()
            run_as_root('wget %s -O %s' % (url, tmp_key))
            _add_pgp_key(_dearmor_pgp_key(tmp_key))
            remove(tmp_key, force=True, use_sudo=True)
        else:
            raise ValueError(
                'Either filename, url or keyid must be provided as argument')
    else:
        if filename is not None:
            _check_pgp_key(filename, keyid)
            _add_pgp_key(_dearmor_pgp_key(filename))
        elif url is not None:
            tmp_key = '/tmp/tmp.fabtools.apt_key.%s.key' % md5(keyid).hexdigest()
            run_as_root('wget %s -O %s' % (url, tmp_key))
            _check_pgp_key(tmp_key, keyid)
            _add_pgp_key(_dearmor_pgp_key(tmp_key))
            remove(tmp_key, force=True, use_sudo=True)
        else:
            require_package('dirmngr')
            run_as_root('gpg -k')
            keyserver_opt = '--keyserver %s' % keyserver if keyserver is not None else ''
            # Import key to tmp keyring file
            tmp_keyring = '/tmp/tmp.fabtools.apt_key.%s.keyring' % md5(keyid).hexdigest()
            run_as_root('gpg --no-default-keyring --keyring %s %s --recv-keys %s' % (tmp_keyring, keyserver_opt, keyid))
            # Export key from tmp keyring file
            tmp_gpg = '/tmp/tmp.fabtools.apt_key.%s.gpg' % md5(keyid).hexdigest()
            run_as_root('gpg --no-default-keyring --keyring %s --yes --output %s --export' % (tmp_keyring, tmp_gpg))
            _add_pgp_key(tmp_gpg)
            # `tmp_gpg` is cleaned by `_add_pgp_key()`
            remove(tmp_keyring, force=True, use_sudo=True)

    if update:
        update_index()


def del_apt_key(keyid):
    """
    Remove this public key from trusted ones.
    """
    filename = locate_apt_key(keyid)
    if filename is not None:
        if filename != '/etc/apt/trusted.gpg':
            remove(filename, force=True, use_sudo=True)
        else:
            raise ValueError('Deleting a key from `/etc/apt/trusted.gpg` is no more supported.')


def last_update_time():
    """
    Get the time of last APT index update

    This is the last modification time of ``/var/lib/apt/periodic/fabtools-update-success-stamp``.

    Returns ``-1`` if there was no update before.

    Example::

        import fabtools

        print(fabtools.deb.last_update_time())
        # 1377603808.02

    """
    STAMP = '/var/lib/apt/periodic/fabtools-update-success-stamp'
    if not is_file(STAMP):
        return -1
    return getmtime(STAMP)
