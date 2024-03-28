import pytest


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
