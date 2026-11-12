"""Executable validation of the generated contract and stub boundary."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, RefResolver, FormatChecker
from openapi_spec_validator import validate_spec
from api import app, current_identity, mutation_identity, EXAMPLES

spec=app.openapi()
validate_spec(spec)
assert json.loads(Path(__file__).with_name('openapi.json').read_text())==spec
ops=[(p,m,o) for p,item in spec['paths'].items() for m,o in item.items() if m in ('get','post','delete')]
assert len(ops)==8
examples=0
for path,method,op in ops:
    assert '400' in op['responses'] and '422' not in op['responses']
    assert op['security']==[{'SessionCookie':[],**({'CsrfToken':[]} if method!='get' else {})}]
    for response in op['responses'].values():
        for content in response.get('content',{}).values():
            schema=content.get('schema')
            for example in content.get('examples',{}).values():
                if schema:
                    Draft202012Validator(schema,resolver=RefResolver.from_schema(spec),format_checker=FormatChecker()).validate(example['value'])
                    examples+=1
    if 'requestBody' in op:
        content=op['requestBody']['content']['application/json']
        for ex in content.get('examples',{}).values():
            Draft202012Validator(content['schema'],resolver=RefResolver.from_schema(spec)).validate(ex['value'])
            examples+=1
assert 'content' not in spec['paths']['/v1/watchlist/items/{stockId}']['delete']['responses']['204']
client=TestClient(app)
assert client.get('/v1/stocks').status_code==401
assert client.get('/v1/stocks',cookies={'dashboard_session':'not-a-real-session'}).status_code==501
# Overrides model an already verified external identity only in isolated tests.
app.dependency_overrides[current_identity]=lambda:'issuer|subject-fixture'
app.dependency_overrides[mutation_identity]=lambda:'issuer|subject-fixture'
checks=[('/v1/stocks?limit=0',400),('/v1/stocks?limit=101',400),('/v1/stocks?sort=invalid',400),('/v1/stocks?ownerId=other',400),('/v1/stocks?q=%20',400),('/v1/stocks?exchange=XNYS',400),('/v1/stocks?cursor=',400),('/v1/stocks/BAD!',400),('/v1/stocks/stk_aapl/history?fromDate=2026-11-11&toDate=2026-11-10',400),('/v1/stocks/stk_aapl/history?fromDate=1900-01-01&toDate=2026-11-10',400),('/v1/stocks/stk_aapl/history?fromDate=2026-11-10&toDate=2099-01-01',400),('/v1/stocks/stk_aapl/history?fromDate=2026-11-10&toDate=2026-11-11&limit=201',400),('/v1/stocks?sector=technology&sort=trending&limit=20',501),('/v1/stocks/stk_aapl/history?fromDate=2026-11-10&toDate=2026-11-11',501)]
for url,status in checks:
    response=client.get(url)
    assert response.status_code==status,(url,response.text)
    assert set(response.json())=={'error'}
for body in ({},{'stockId':'stk_aapl','ownerId':'other'},{'stockId':'bad'},{'stockId':'stk_aapl','version':999}):
    assert client.post('/v1/watchlist/items',json=body).status_code==400
assert client.post('/v1/watchlist/items',content='{',headers={'Content-Type':'application/json'}).status_code==400
assert client.post('/v1/watchlist/items',json=EXAMPLES['add']).status_code==501
assert client.delete('/v1/watchlist/items/stk_aapl').status_code==501
app.dependency_overrides.pop(mutation_identity)
assert client.post('/v1/watchlist/items',json=EXAMPLES['add']).status_code==403
app.dependency_overrides.clear()
print(f'PASS: OpenAPI 3.1 validation; {len(ops)} operations; {examples} examples; authentication/CSRF stub boundaries; 14 query/path and 5 invalid-body checks; 204 without body; deterministic generation.')
