import pytest
import requests
import tornado.httpclient

import salt.utils.http
from tests.support.mock import MagicMock, patch


class _FakeFetchResponse:
    """Simple object mimicking the bits of tornado's HTTPResponse we rely on."""

    def __init__(self, code=200, body=b"payload", headers=None):
        self.code = code
        self.body = body
        self.headers = headers or {"Content-Type": "text/plain; charset=utf-8"}


@pytest.fixture
def syncwrapper_stub(monkeypatch):
    """Patch ``salt.utils.http.SyncWrapper`` with a controllable test double."""

    class SyncWrapperStub:
        fetch_return = _FakeFetchResponse()
        fetch_side_effect = None
        enter_calls = 0
        close_calls = 0
        fetch_calls = 0

        def __init__(self, *args, **kwargs):
            # Mirror SyncWrapper signature but we only need to track usage.
            pass

        def __enter__(self):
            SyncWrapperStub.enter_calls += 1
            return self

        def __exit__(self, exc_type, exc, tb):
            self.close()
            # Propagate exceptions so http.query can handle them
            return False

        def close(self):
            SyncWrapperStub.close_calls += 1

        def fetch(self, *args, **kwargs):
            SyncWrapperStub.fetch_calls += 1
            if SyncWrapperStub.fetch_side_effect is not None:
                raise SyncWrapperStub.fetch_side_effect
            return SyncWrapperStub.fetch_return

        @classmethod
        def reset_counters(cls, *, clear_fetch=True):
            cls.enter_calls = 0
            cls.close_calls = 0
            cls.fetch_calls = 0
            if clear_fetch:
                cls.fetch_side_effect = None
                cls.fetch_return = _FakeFetchResponse()

    monkeypatch.setattr(salt.utils.http, "SyncWrapper", SyncWrapperStub)
    SyncWrapperStub.reset_counters()
    return SyncWrapperStub


def test_requests_session_verify_ssl_false(ssl_webserver, integration_files_dir):
    """
    test salt.utils.http.session when using verify_ssl
    """
    for verify in [True, False, None]:
        kwargs = {"verify_ssl": verify}
        if verify is None:
            kwargs.pop("verify_ssl")

        if verify is True or verify is None:
            with pytest.raises(requests.exceptions.SSLError) as excinfo:
                session = salt.utils.http.session(**kwargs)
                ret = session.get(ssl_webserver.url("this.txt"))
        else:
            session = salt.utils.http.session(**kwargs)
            ret = session.get(ssl_webserver.url("this.txt"))
            assert ret.status_code == 200


def test_session_ca_bundle_verify_false():
    """
    test salt.utils.http.session when using
    both ca_bunlde and verify_ssl false
    """
    ret = salt.utils.http.session(ca_bundle="/tmp/test_bundle", verify_ssl=False)
    assert ret is False


def test_session_headers():
    """
    test salt.utils.http.session when setting
    headers
    """
    ret = salt.utils.http.session(headers={"Content-Type": "application/json"})
    assert ret.headers["Content-Type"] == "application/json"


def test_session_ca_bundle():
    """
    test salt.utils.https.session when setting ca_bundle
    """
    fpath = "/tmp/test_bundle"
    patch_os = patch("os.path.exists", MagicMock(return_value=True))
    with patch_os:
        ret = salt.utils.http.session(ca_bundle=fpath)
    assert ret.verify == fpath


def test_query_tornado_httperror_no_response():
    """
    Tests that http.query handles a Tornado HTTPError where exc.response is None.
    This happens on connection-level failures such as a connect timeout (HTTP 599)
    where no HTTP response is ever received from the server.
    """
    import tornado.httpclient

    http_error = tornado.httpclient.HTTPError(599, "Timeout while connecting")
    assert http_error.response is None

    mock_client = MagicMock()
    mock_client.fetch.side_effect = http_error
    # http.query() uses SyncWrapper as a context manager; ensure
    # __enter__() returns the mock_client itself.
    mock_client.__enter__.return_value = mock_client


def test_query_tornado_closes_syncwrapper_on_success(syncwrapper_stub):
    syncwrapper_stub.reset_counters()
    syncwrapper_stub.fetch_return = _FakeFetchResponse(body=b"test-body")

    ret = salt.utils.http.query("http://example.com", backend="tornado", status=True)

    assert syncwrapper_stub.enter_calls == 1
    assert syncwrapper_stub.close_calls == 1
    assert syncwrapper_stub.fetch_calls == 1
    assert ret["body"] == "test-body"
    assert ret["status"] == 200


def test_query_tornado_closes_syncwrapper_on_http_error(syncwrapper_stub):
    syncwrapper_stub.reset_counters()
    response = MagicMock(body=b"", headers={"Content-Type": "text/plain"})
    syncwrapper_stub.fetch_side_effect = tornado.httpclient.HTTPError(
        599, "Unit test failure", response=response
    )

    ret = salt.utils.http.query(
        "http://example.com",
        backend="tornado",
        status=True,
        raise_error=True,
    )

    assert syncwrapper_stub.enter_calls == 1
    assert syncwrapper_stub.close_calls == 1
    assert syncwrapper_stub.fetch_calls == 1
    assert ret["status"] == 599
    assert "Unit test failure" in ret["error"]
