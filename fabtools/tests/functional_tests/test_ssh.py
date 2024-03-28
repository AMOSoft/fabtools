"""
Test SSH hardening operations
"""

from textwrap import dedent

import pytest

from fabric.api import quiet

from fabric.contrib.files import contains


from fabtools.require import file as require_file


SSHD_CONFIG = '/tmp/sshd_config'


SSHD_CONFIG_CONTENTS = [
    """
    """,

    """
    PasswordAuthentication yes
    PermitRootLogin yes
    """,

    """
    PasswordAuthentication yes
    PermitRootLogin no
    """,

    """
    PasswordAuthentication no
    PermitRootLogin yes
    """,

    """
    PasswordAuthentication no
    PermitRootLogin no
    """,
]


@pytest.fixture(scope='module', autouse=True)
def check_for_debian_family():
    from fabtools.system import distrib_family
    if distrib_family() != 'debian':
        pytest.skip("Skipping SSH test on non-Debian distrib")


@pytest.fixture(scope='module', params=SSHD_CONFIG_CONTENTS)
def sshd_config(request):
    from fabtools.service import stop
    stop('ssh')
    require_file(SSHD_CONFIG, contents=dedent(request.param), use_sudo=True)


def test_disable_password_auth(sshd_config):

    from fabtools.ssh import disable_password_auth

    disable_password_auth(sshd_config=SSHD_CONFIG)

    with quiet():
        assert contains(SSHD_CONFIG, 'PasswordAuthentication no', exact=True)
        assert not contains(SSHD_CONFIG, 'PasswordAuthentication yes', exact=True)


def test_disable_root_login(sshd_config):

    from fabtools.ssh import disable_root_login

    disable_root_login(sshd_config=SSHD_CONFIG)

    with quiet():
        assert contains(SSHD_CONFIG, 'PermitRootLogin no', exact=True)
        assert not contains(SSHD_CONFIG, 'PermitRootLogin yes', exact=True)


def test_enable_password_auth(sshd_config):

    from fabtools.ssh import enable_password_auth

    enable_password_auth(sshd_config=SSHD_CONFIG)

    with quiet():
        assert contains(SSHD_CONFIG, 'PasswordAuthentication yes', exact=True)
        assert not contains(SSHD_CONFIG, 'PasswordAuthentication no', exact=True)


def test_enable_root_login(sshd_config):

    from fabtools.ssh import enable_root_login

    enable_root_login(sshd_config=SSHD_CONFIG)

    with quiet():
        assert contains(SSHD_CONFIG, 'PermitRootLogin yes', exact=True)
        assert not contains(SSHD_CONFIG, 'PermitRootLogin no', exact=True)
