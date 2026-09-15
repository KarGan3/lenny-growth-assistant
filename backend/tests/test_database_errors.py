from sqlalchemy.exc import OperationalError


def test_database_outage_returns_actionable_error_without_raw_database_detail(client, monkeypatch):
    from app.db import get_db
    from app.main import app
    def broken_db():
        raise OperationalError('secret SQL', {}, Exception('private connection detail'))
        yield
    app.dependency_overrides[get_db] = broken_db
    try:
        result=client.get('/sessions')
        assert result.status_code == 503
        assert result.json()['error'] == 'database_unavailable'
        assert 'private connection' not in result.text
        assert 'secret SQL' not in result.text
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_validation_error_does_not_echo_input(client):
    response=client.post('/sessions',json={'title':'x'*256,'user_metadata':{'private':'do not echo'}})
    assert response.status_code==422
    assert response.json()['error']=='validation_error'
    assert 'do not echo' not in response.text
