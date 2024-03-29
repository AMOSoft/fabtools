import pytest

from fabric.api import run, settings

from fabtools.require import file as require_file


pytestmark = pytest.mark.network


MYSQL_ROOT_PASSWORD = 'th!sIsMyS3cr3t'


@pytest.fixture
def mysql_server():
    from fabtools.system import distrib_family
    if distrib_family() == 'debian':
        from fabtools.require.mysql import server
        server(password=MYSQL_ROOT_PASSWORD)

    elif distrib_family() == 'redhat':
        from fabtools.system import distrib_release
        from fabtools.utils import run_as_root
        from fabtools.rpm import install as rpm_install, is_installed as rpm_is_installed
        from fabtools.require.rpm import package as require_rpm_package
        from fabtools.require.service import started as require_service_started

        # Available RPM :
        #  - https://repo.mysql.com/mysql-community-release-el7.rpm
        #  - https://repo.mysql.com/mysql57-community-release-el7.rpm
        #  - https://repo.mysql.com/mysql80-community-release-el7.rpm
        #  - https://repo.mysql.com/mysql80-community-release-el8.rpm
        #  - https://repo.mysql.com/mysql80-community-release-el9.rpm

        distrib_major_rel = distrib_release().split('.')[0]
        mysql_ver = '8.0'
        mysql_flat_ver = mysql_ver.replace('.', '')
        pkg = 'mysql%s-community-release-el%s' % (mysql_flat_ver, distrib_major_rel)
        repo = 'http://repo.mysql.com/%s.rpm' % pkg
        if not rpm_is_installed(pkg):
            rpm_install(repo)
            run_as_root('yum-config-manager --enable mysql%s-community' % mysql_flat_ver)
            if distrib_major_rel == '8':
                require_rpm_package('mysql-server')
            else:
                require_rpm_package('mysql-community-server')
            require_service_started('mysqld')
            if distrib_major_rel == '8':
                init_pwd_sql = "ALTER USER 'root'@'localhost' IDENTIFIED BY '%s'; " \
                               "FLUSH PRIVILEGES;" % MYSQL_ROOT_PASSWORD
                run('mysql -uroot --skip-password -e "%s"' % init_pwd_sql)
            else:
                tmp_pwd = run_as_root("grep 'A temporary password' /var/log/mysqld.log |tail -1 |awk '{split($0,a,\": \"); print a[2]}'", quiet=True)
                init_pwd_sql = "ALTER USER 'root'@'localhost' IDENTIFIED BY '%s'; " \
                               "FLUSH PRIVILEGES;" % MYSQL_ROOT_PASSWORD
                run("mysql -uroot -p'%s' --connect-expired-password -e \"%s\"" % (tmp_pwd, init_pwd_sql))

    else:
        pytest.skip("Skipping MySQL test on non-Debian and non-Redhat distrib")


def test_create_user(mysql_server):

    from fabtools.mysql import create_user, query, user_exists

    with settings(mysql_user='root', mysql_password=MYSQL_ROOT_PASSWORD):
        try:
            create_user('bob', 'TH!sISmyPassw0rd', host='host1')
            create_user('bob', 'TH!sISmyPassw0rd', host='host2')
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
            user('myuser', 'TH!sISan0therS3Cr3t')
            assert user_exists('myuser')
        finally:
            query('DROP USER myuser@localhost;')


@pytest.yield_fixture
def mysql_user():

    from fabtools.mysql import query
    from fabtools.require.mysql import user

    username = 'myuser'
    password = 'TH!sISan0therS3Cr3t'

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

    with settings(mysql_user='myuser', mysql_password='TH!sISan0therS3Cr3t'):
        query('select 1;')


def test_run_query_on_a_specific_port(mysql_server, mysql_user):

    from fabtools.mysql import query

    with settings(mysql_user='myuser', mysql_password='TH!sISan0therS3Cr3t', mysql_port=3306, mysql_host='127.0.0.1'):
        assert query('select 3;') == '3'

    with settings(mysql_user='myuser', mysql_password='TH!sISan0therS3Cr3t', mysql_port='3306', mysql_host='127.0.0.1'):
        assert query('select 31;') == '31'


def test_run_query_without_supplying_the_password(mysql_server, mysql_user):

    from fabtools.mysql import query

    username, password = mysql_user

    try:
        require_file('.my.cnf', contents="[mysql]\npassword={0}".format(password))
        with settings(mysql_user=username):
            query('select 2;', use_sudo=False)
    finally:
        run('rm -f .my.cnf')
