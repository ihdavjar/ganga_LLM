import pytest
try:
    import unittest.mock as mock
except ImportError:
    import mock

from GangaCore.Utility.Config import getConfig, makeConfig
makeConfig('defaults_DiracProxy', '')
getConfig('defaults_DiracProxy').addOption('group', 'gridpp_user', '')
getConfig('defaults_DiracProxy').setSessionValue('group', 'gridpp_user')
from GangaDirac.Lib.Credentials.DiracProxy import DiracProxy, DiracProxyInfo


class FakeShell(object):
    """
    A mock version of Shell which allows to customise the return values

    Examples:
        >>> s = FakeShell()
        >>> assert s.cmd1.call_count == 0
        >>> assert s.cmd1('foo') == (0, '', '')
        >>> assert s.cmd1.call_count == 1
        >>> assert s.cmd1('something -vo') == (0, 'gridpp_user', '')
        >>> assert s.cmd1.call_count == 2
    """
    vo = 'gridpp_user'
    timeleft = '1:2:3'

    def __init__(self):
        self.env = {}
        self.cmd1 = mock.Mock(wraps=self._cmd1)
        self.system = mock.Mock(wraps=self._system)
        self.check_call = mock.Mock(wraps=self._check_call)

    def _cmd1(self, cmd):
        val = ''

        if '-vo' in cmd:
            val = self.vo
        elif '-timeleft' in cmd:
            val = self.timeleft

        return 0, val, '',

    def _system(self, cmd):
        return 0

    def _check_call(self, cmd):
        pass


def resolver(dummy_class, input_):
    values = {}
    values['DIRAC group'] = 'gridpp_user'
    values['timeleft'] = dummy_class.shell.timeleft
    return values[input_]


@pytest.yield_fixture(scope='function')
def fake_shell(mocker):
    #from GangaCore.testlib.GangaUnitTest import load_config_files, clear_config
    # load_config_files()
    s = mocker.patch('GangaDirac.Lib.Credentials.DiracProxy.DiracProxyInfo.shell', FakeShell())
    mocker.patch('GangaDirac.Lib.Credentials.DiracProxy.DiracProxyInfo.field', resolver)
    mocker.patch('GangaDirac.Lib.Credentials.DiracProxy.DiracProxyInfo.identity', return_value='some_user')
    mocker.patch('GangaCore.GPIDev.Adapters.ICredentialInfo.os.path.exists', return_value=True)
    mocker.patch('GangaCore.GPIDev.Credentials.CredentialStore.CredentialStore.enable_caching', False)
    yield s
    # clear_config()


def test_plain_construct(fake_shell):
    DiracProxyInfo(DiracProxy())


def test_construct(fake_shell):
    req = DiracProxy(group='gridpp_user')
    DiracProxyInfo(req)


def test_default_location(fake_shell):
    v = DiracProxyInfo(DiracProxy())
    assert v.location == v.default_location()


def test_location(fake_shell):
    req = DiracProxy(group='gridpp_user')
    v = DiracProxyInfo(req)
    assert v.location == v.default_location()


def test_create(fake_shell):
    req = DiracProxy(group='gridpp_user')
    v = DiracProxyInfo(req)
    v.create()

    assert v.shell.check_call.call_count == 1
    cmd = v.shell.check_call.call_args[0][0]
    assert 'dirac-proxy-init' in cmd
    assert '-group gridpp_user' in cmd
    assert '-out "{0}"'.format(v.location) in cmd


def test_is_valid(fake_shell):
    req = DiracProxy(group='gridpp_user')
    v = DiracProxyInfo(req)

    assert v.is_valid()

    fake_shell.timeleft = '0:0:0'

    assert not v.is_valid()
