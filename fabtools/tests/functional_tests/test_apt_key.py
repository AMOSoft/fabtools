import pytest

from fabric.api import run

from fabtools.deb import del_apt_key
from fabtools.files import is_file, is_dir

pytestmark = pytest.mark.network


@pytest.fixture(scope='module', autouse=True)
def check_for_debian_family():
    from fabtools.system import distrib_family
    if distrib_family() != 'debian':
        pytest.skip("Skipping apt-key test on non-Debian distrib")


def _apt_key_finger_grep(grep_expr):
    """
    Checks if the expr can be found in apt keyring.

    NB: Replaces the `apt-key finger | grep -q -E "<expr>"` tests

    :type grep_expr: str
    """
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
        gpg_cmd = 'gpg --ignore-time-conflict --no-options --no-default-keyring --keyring %s' % keyring
        res = run('%s --fingerprint | grep -q -E "%s"' % (gpg_cmd, grep_expr), quiet=True)
        if res.succeeded:
            return True

    raise ValueError('Could not match "%s" expression in fingerprints' % grep_expr)


def test_add_apt_key_with_key_id_from_url():
    from fabtools.deb import add_apt_key
    try:
        add_apt_key(keyid='A750EDCD', url='https://packagecloud.io/varnishcache/varnish60lts/gpgkey')
        _apt_key_finger_grep('A750 ?EDCD')
    finally:
        del_apt_key('A750EDCD')


def test_add_apt_key_with_key_id_from_specific_key_server():
    from fabtools.deb import add_apt_key
    try:
        add_apt_key(keyid='7BD9BF62', keyserver='keyserver.ubuntu.com')
        _apt_key_finger_grep('7BD9 ?BF62')
    finally:
        del_apt_key('7BD9BF62')


def test_add_apt_key_with_key_id_from_file():
    from fabtools.deb import add_apt_key
    try:
        run('wget https://packagecloud.io/varnishcache/varnish60lts/gpgkey -O /tmp/tmp.fabtools.test.key')
        add_apt_key(keyid='A750EDCD', filename='/tmp/tmp.fabtools.test.key')
        _apt_key_finger_grep('A750 ?EDCD')
    finally:
        del_apt_key('A750EDCD')
        run('rm -f /tmp/tmp.fabtools.test.key')


def test_add_apt_key_without_key_id_from_url():
    from fabtools.deb import add_apt_key
    try:
        add_apt_key(url='https://packagecloud.io/varnishcache/varnish60lts/gpgkey')
        _apt_key_finger_grep('A750 ?EDCD')
    finally:
        del_apt_key('A750EDCD')


def test_add_apt_key_without_key_id_from_file():
    from fabtools.deb import add_apt_key
    try:
        run('wget https://packagecloud.io/varnishcache/varnish60lts/gpgkey -O /tmp/tmp.fabtools.test.key')
        add_apt_key(filename='/tmp/tmp.fabtools.test.key')
        _apt_key_finger_grep('A750 ?EDCD')
    finally:
        del_apt_key('A750EDCD')
        run('rm -f /tmp/tmp.fabtools.test.key')


def test_require_deb_key_from_url():
    from fabtools.require.deb import key as require_key
    try:
        require_key(keyid='A750EDCD', url='https://packagecloud.io/varnishcache/varnish60lts/gpgkey')
        _apt_key_finger_grep('A750 ?EDCD')
    finally:
        del_apt_key('A750EDCD')


def test_require_deb_key_from_specific_keyserver():
    from fabtools.require.deb import key as require_key
    try:
        require_key(keyid='7BD9BF62', keyserver='keyserver.ubuntu.com')
        _apt_key_finger_grep('7BD9 ?BF62')
    finally:
        del_apt_key('7BD9BF62')


def test_require_deb_key_from_file():
    from fabtools.require.deb import key as require_key
    try:
        run('wget https://packagecloud.io/varnishcache/varnish60lts/gpgkey -O /tmp/tmp.fabtools.test.key')
        require_key(keyid='A750EDCD', filename='/tmp/tmp.fabtools.test.key')
        _apt_key_finger_grep('A750 ?EDCD')
    finally:
        del_apt_key('A750EDCD')
        run('rm -f /tmp/tmp.fabtools.test.key')
