import pytest


pytestmark = pytest.mark.network


@pytest.fixture(scope='module', autouse=True)
def check_for_debian_family():
    from fabtools.system import distrib_family
    if distrib_family() != 'debian':
        pytest.skip("Skipping Nginx test on non-Debian distrib")


def test_require_nginx_server():
    try:
        from fabtools.require.nginx import server
        server()
    finally:
        uninstall_nginx()


@pytest.yield_fixture
def nginx_server():
    from fabtools.require.nginx import server
    server()
    yield
    uninstall_nginx()


def uninstall_nginx():
    from fabtools.require.deb import nopackage
    nopackage('nginx')


def test_site_disabled(nginx_server):

    from fabtools.require.nginx import disabled as require_nginx_site_disabled
    from fabtools.files import is_link

    require_nginx_site_disabled('default')
    assert not is_link('/etc/nginx/sites-enabled/default')


def test_site_enabled(nginx_server):

    from fabtools.require.nginx import enabled as require_nginx_site_enabled
    from fabtools.files import is_link

    require_nginx_site_enabled('default')
    assert is_link('/etc/nginx/sites-enabled/default')
