import pytest

from fabtools.files import is_file


pytestmark = pytest.mark.network


@pytest.fixture(scope='module', autouse=True)
def skip_all():
        pytest.skip("Currently unmaintained")


def test_require_default_jdk_version():

    from fabtools.oracle_jdk import version, DEFAULT_VERSION
    from fabtools.require.oracle_jdk import installed

    installed()

    assert is_file('/opt/jdk/bin/java')
    assert version() == DEFAULT_VERSION


def test_require_jdk_version_6():

    from fabtools.oracle_jdk import version
    from fabtools.require.oracle_jdk import installed

    installed('6u45-b06')

    assert is_file('/opt/jdk/bin/java')
    assert version() == '6u45-b06'
