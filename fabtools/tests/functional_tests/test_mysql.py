import pytest

from fabric.api import run, settings

from fabtools.require import file as require_file


pytestmark = pytest.mark.network


MYSQL_ROOT_PASSWORD = 's3cr3t'


# # Not necessary : see mysql_server fixture
# def test_require_mysql_server():
#     from fabtools.require.mysql import server
#     server(password=MYSQL_ROOT_PASSWORD)


@pytest.fixture
def mysql_server():
    from fabtools.system import distrib_family
    version = '5.6'
    if distrib_family() == 'debian':
        from fabtools.require.mysql import server
        server(password=MYSQL_ROOT_PASSWORD)
    elif distrib_family() == 'redhat':
        from fabtools.system import distrib_release, get_arch
        from fabtools.utils import run_as_root
        from fabtools.rpm import install as rpm_install, is_installed as rpm_is_installed
        from fabtools.require.rpm import package as require_rpm_package
        from fabtools.require.service import started as require_service_started
        require_rpm_package('redhat-lsb-core')
        distrib_major_rel = distrib_release().split('.')[0]
        mysql_major_ver = version.split('.')[0]
        mysql_flat_ver = version.replace('.', '')
        pkg = 'mysql-community-release-el%s-%s.noarch' % (distrib_major_rel, mysql_major_ver)
        if not rpm_is_installed(pkg):
            repo = 'http://repo.mysql.com/yum/mysql-%s-community/el/%s/%s/%s.rpm' % (version, distrib_major_rel, get_arch(), pkg)
            rpm_install(repo)
            run_as_root('yum-config-manager --enable mysql%s-community' % mysql_flat_ver)
            require_rpm_package('mysql-community-server')
            require_service_started('mysqld')
            init_pwd_sql = "UPDATE mysql.user SET Password=PASSWORD('%s') WHERE User='root'; " \
                           "FLUSH PRIVILEGES;" % MYSQL_ROOT_PASSWORD
            run('mysql -uroot -e "%s"' % init_pwd_sql)
    else:
        pytest.skip("Skipping MySQL test on non-Debian and non-Redhat distrib")


def test_create_user(mysql_server):

    from fabtools.mysql import create_user, query, user_exists

    with settings(mysql_user='root', mysql_password=MYSQL_ROOT_PASSWORD):
        try:
            create_user('bob', 'password', host='host1')
            create_user('bob', 'password', host='host2')
            assert user_exists('bob', host='host1')
            assert user_exists('bob', host='host2')
            assert not user_exists('bob', host='localhost')
        finally:
            query('DROP USER bob@host1;')
            query('DROP USER bob@host2;')


def test_require_user(mysql_server):

    from fabtools.mysql import query, user_exists
    from fabtools.require.mysql import user

    with settings(mysql_user='root', mysql_password=MYSQL_ROOT_PASSWORD):
        try:
            user('myuser', 'foo')
            assert user_exists('myuser')
        finally:
            query('DROP USER myuser@localhost;')


@pytest.yield_fixture
def mysql_user():

    from fabtools.mysql import query
    from fabtools.require.mysql import user

    username = 'myuser'
    password = 'foo'

    with settings(mysql_user='root', mysql_password=MYSQL_ROOT_PASSWORD):
        user(username, password)

    yield username, password

    with settings(mysql_user='root', mysql_password=MYSQL_ROOT_PASSWORD):
        query('DROP USER {0}@localhost;'.format(username))


def test_require_database(mysql_server, mysql_user):

    from fabtools.mysql import database_exists, query
    from fabtools.require.mysql import database

    with settings(mysql_user='root', mysql_password=MYSQL_ROOT_PASSWORD):
        try:
            database('mydb', owner='myuser')
            assert database_exists('mydb')
        finally:
            query('DROP DATABASE mydb;')


def test_run_query_as_a_specific_user(mysql_server, mysql_user):

    from fabtools.mysql import query

    with settings(mysql_user='myuser', mysql_password='foo'):
        query('select 1;')


def test_run_query_on_a_specific_port(mysql_server, mysql_user):

    from fabtools.mysql import query

    with settings(mysql_user='myuser', mysql_password='foo', mysql_port=3306):
        query('select 3;')


def test_run_query_without_supplying_the_password(mysql_server, mysql_user):

    from fabtools.mysql import query

    username, password = mysql_user

    try:
        require_file('.my.cnf', contents="[mysql]\npassword={0}".format(password))
        with settings(mysql_user=username):
            query('select 2;', use_sudo=False)
    finally:
        run('rm -f .my.cnf')
