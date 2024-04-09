import pytest

from fabric.api import run

from fabtools.utils import run_as_root
from fabtools.deb import del_apt_key

pytestmark = pytest.mark.network


@pytest.fixture(scope='module', autouse=True)
def check_for_debian_family():
    from fabtools.system import distrib_family
    if distrib_family() != 'debian':
        pytest.skip("Skipping apt-key test on non-Debian distrib")


def test_add_apt_key_with_key_id_from_url():
    from fabtools.deb import add_apt_key
    try:
        add_apt_key(keyid='A750EDCD', url='https://packagecloud.io/varnishcache/varnish60lts/gpgkey')
        run_as_root('apt-key finger | grep -q -E "A750 ?EDCD"')
    finally:
        del_apt_key('A750EDCD')


def test_add_apt_key_with_key_id_from_specific_key_server():
    from fabtools.deb import add_apt_key
    try:
        add_apt_key(keyid='7BD9BF62', keyserver='keyserver.ubuntu.com')
        run_as_root('apt-key finger | grep -q -E "7BD9 ?BF62"')
    finally:
        del_apt_key('7BD9BF62')


def test_add_apt_key_with_key_id_from_file():
    from fabtools.deb import add_apt_key
    try:
        run('wget https://packagecloud.io/varnishcache/varnish60lts/gpgkey -O /tmp/tmp.fabtools.test.key')
        add_apt_key(keyid='A750EDCD', filename='/tmp/tmp.fabtools.test.key')
        run_as_root('apt-key finger | grep -q -E "A750 ?EDCD"')
    finally:
        del_apt_key('A750EDCD')
        run_as_root('rm -f /tmp/tmp.fabtools.test.key')


def test_add_apt_key_without_key_id_from_url():
    from fabtools.deb import add_apt_key
    try:
        add_apt_key(url='https://packagecloud.io/varnishcache/varnish60lts/gpgkey')
        run_as_root('apt-key finger | grep -q -E "A750 ?EDCD"')
    finally:
        del_apt_key('A750EDCD')


def test_add_apt_key_without_key_id_from_file():
    from fabtools.deb import add_apt_key
    try:
        run('wget https://packagecloud.io/varnishcache/varnish60lts/gpgkey -O /tmp/tmp.fabtools.test.key')
        add_apt_key(filename='/tmp/tmp.fabtools.test.key')
        run_as_root('apt-key finger | grep -q -E "A750 ?EDCD"')
    finally:
        del_apt_key('A750EDCD')
        run_as_root('rm -f /tmp/tmp.fabtools.test.key')


def test_require_deb_key_from_url():
    from fabtools.require.deb import key as require_key
    try:
        require_key(keyid='A750EDCD', url='https://packagecloud.io/varnishcache/varnish60lts/gpgkey')
        run_as_root('apt-key finger | grep -q -E "A750 ?EDCD"')
    finally:
        del_apt_key('A750EDCD')


def test_require_deb_key_from_specific_keyserver():
    from fabtools.require.deb import key as require_key
    try:
        require_key(keyid='7BD9BF62', keyserver='keyserver.ubuntu.com')
        run_as_root('apt-key finger | grep -q -E "7BD9 ?BF62"')
    finally:
        del_apt_key('7BD9BF62')


def test_require_deb_key_from_file():
    from fabtools.require.deb import key as require_key
    try:
        run('wget https://packagecloud.io/varnishcache/varnish60lts/gpgkey -O /tmp/tmp.fabtools.test.key')
        require_key(keyid='A750EDCD', filename='/tmp/tmp.fabtools.test.key')
        run_as_root('apt-key finger | grep -q -E "A750 ?EDCD"')
    finally:
        del_apt_key('A750EDCD')
        run_as_root('rm -f /tmp/tmp.fabtools.test.key')
