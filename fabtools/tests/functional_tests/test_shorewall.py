import pytest


pytestmark = pytest.mark.network


@pytest.fixture(scope='module', autouse=True)
def check_for_debian_family():
    from fabtools.system import distrib_family
    if distrib_family() != 'debian':
        pytest.skip("Skipping Redis test on non-Debian distrib")


@pytest.fixture(scope='module')
def firewall():
    from fabtools.require.shorewall import firewall
    import fabtools.shorewall
    firewall(
        rules=[
            fabtools.shorewall.Ping(),
            fabtools.shorewall.SSH(),
            fabtools.shorewall.HTTP(),
            fabtools.shorewall.HTTPS(),
            fabtools.shorewall.SMTP(),
            fabtools.shorewall.rule(
                port=1234,
                source=fabtools.shorewall.hosts(['python.org']),
            ),
        ]
    )


def test_require_firewall_started(firewall):
    from fabtools.require.shorewall import started
    from fabtools.shorewall import is_started
    started()
    assert is_started()


def test_require_firewall_stopped(firewall):
    from fabtools.require.shorewall import stopped
    from fabtools.shorewall import is_stopped
    stopped()
    assert is_stopped()
