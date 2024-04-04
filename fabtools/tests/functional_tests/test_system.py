import pytest


class TestDistrib:

    def test_distrib_id(self):
        from fabtools.system import distrib_id
        assert distrib_id().lower() == pytest.box_os_id

    def test_distrib_release(self):
        from fabtools.system import distrib_release
        assert distrib_release().lower().split('.')[0] == pytest.box_os_rel


class TestRequireLocale:

    def test_en_locale(self):
        from fabtools.require.system import locale
        locale('en_US')

    def test_fr_locale(self):
        from fabtools.require.system import locale
        from fabtools.system import distrib_family, distrib_release
        from distutils.version import StrictVersion as V
        if distrib_family() == 'redhat' and V(distrib_release() + '.0') >= V('8.0'):
            from fabtools.require.rpm import packages as require_packages
            require_packages(['langpacks-fr', 'glibc-langpack-fr'])
        locale('fr_FR')

    def test_non_existing_locale(self):
        from fabtools.require.system import locale, UnsupportedLocales
        with pytest.raises(UnsupportedLocales) as excinfo:
            locale('ZZZZ')
        assert excinfo.value.locales == ['ZZZZ']
