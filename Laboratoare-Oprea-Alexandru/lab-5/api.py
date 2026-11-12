"""Lab 5 contract definitions. Business handlers and authentication are STUBS.
Generate with: python generate_openapi.py
No successful business operation is simulated by this server.
"""
from datetime import date, datetime, timezone
from typing import Annotated, Literal
from fastapi import FastAPI, Depends, Query, Path, Body, Request, Response, Security
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyCookie, APIKeyHeader
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator
from pydantic.alias_generators import to_camel
from starlette.exceptions import HTTPException

ID = Annotated[str, Field(pattern=r'^stk_[a-z0-9_]{1,48}$')]
Money = Annotated[str, Field(pattern=r'^(?:[1-9][0-9]*|0)\.[0-9]{2,4}$')]
Cursor = Annotated[str, Field(min_length=1,max_length=512,pattern=r'^[A-Za-z0-9_-]+$')]
class Model(BaseModel):
    model_config=ConfigDict(alias_generator=to_camel,populate_by_name=True,extra='forbid')
class ErrorDetail(Model):
    code: str
    message: str
class Error(Model):
    error: ErrorDetail
class Quote(Model):
    price: Money
    currency: Literal['USD']
    provider_time: AwareDatetime
    session_date: date
    status: Literal['delayed_feed','delayed','market_closed','awaiting_delayed_quote','final_price_pending']
    age_seconds: int=Field(ge=0)
    @model_validator(mode='after')
    def positive(self):
        from decimal import Decimal
        if Decimal(self.price)<=0: raise ValueError('price must be positive')
        return self
class Stock(Model):
    stock_id: ID
    symbol: str
    name: str
    exchange: Literal['XNAS']
    sector: str|None
    currency: Literal['USD']
    instrument_type: Literal['common','ordinary','equity_adr','equity_ads']
    active: bool
class StockSummary(Stock):
    quote: Quote|None
    change_percent: str|None=Field(pattern=r'^-?[0-9]+\.[0-9]{2}$')
class StockPage(Model):
    items: list[StockSummary]=Field(max_length=100)
    next_cursor: Cursor|None
    as_of: AwareDatetime
class Overview(Model):
    exchange: Literal['XNAS']
    session_date: date
    market_status: Literal['open','closed','opening_grace','closing_grace']
    active_stock_count: int=Field(ge=0)
    priced_stock_count: int=Field(ge=0)
    as_of: AwareDatetime
class PriceResponse(Model):
    stock_id: ID
    quote: Quote
    as_of: AwareDatetime
class HistoryPoint(Model):
    session_date: date
    close: Money
    provider_time: AwareDatetime
class HistoryPage(Model):
    stock_id: ID
    currency: Literal['USD']
    resolution: Literal['1d']
    basis: Literal['unadjusted']
    from_date: date
    to_date: date
    points: list[HistoryPoint]=Field(max_length=200)
    coverage: Literal['complete','partial']
    next_cursor: Cursor|None
    as_of: AwareDatetime
class WatchlistItem(Model):
    stock: Stock
    added_at: AwareDatetime
    quote: Quote|None
class WatchlistPage(Model):
    items: list[WatchlistItem]=Field(max_length=100)
    next_cursor: Cursor|None
    version: int=Field(ge=0)
class AddStock(Model):
    stock_id: ID
class Membership(Model):
    stock_id: ID
    added_at: AwareDatetime
    version: int=Field(ge=0)
class StockQuery(Model):
    exchange: Literal['XNAS']='XNAS'
    sector: Literal['technology','financials','healthcare','industrials','consumer_discretionary','consumer_staples','energy','materials','real_estate','utilities','communication_services','unknown']|None=None
    q: str|None=Field(default=None,min_length=1,max_length=80)
    sort: Literal['symbol','trending']='symbol'
    limit: int=Field(default=20,ge=1,le=100)
    cursor: Cursor|None=None
    @model_validator(mode='after')
    def query_text(self):
        if self.q is not None and not self.q.strip():raise ValueError('q must contain a non-space character')
        return self
class PageQuery(Model):
    limit: int=Field(default=20,ge=1,le=100)
    cursor: Cursor|None=None
class HistoryQuery(Model):
    from_date: date
    to_date: date
    limit: int=Field(default=100,ge=1,le=200)
    cursor: Cursor|None=None
    @model_validator(mode='after')
    def valid_dates(self):
        today=datetime.now(timezone.utc).date()
        try: earliest=today.replace(year=today.year-7)
        except ValueError: earliest=today.replace(year=today.year-7,day=28)
        if not earliest<=self.from_date<=self.to_date<=today:
            raise ValueError('range must be ordered, not future, and within the rolling seven-year window')
        return self

T='2026-11-12T15:00:00Z'
STOCK={'stockId':'stk_aapl','symbol':'AAPL','name':'Apple Inc.','exchange':'XNAS','sector':'technology','currency':'USD','instrumentType':'common','active':True}
QUOTE={'price':'230.50','currency':'USD','providerTime':'2026-11-12T14:44:00Z','sessionDate':'2026-11-12','status':'delayed','ageSeconds':960}
SUMMARY={**STOCK,'quote':QUOTE,'changePercent':'1.32'}
EXAMPLES={
'overview':{'exchange':'XNAS','sessionDate':'2026-11-12','marketStatus':'open','activeStockCount':3400,'pricedStockCount':3380,'asOf':T},
'filteredPage':{'items':[SUMMARY],'nextCursor':'c_page2_example','asOf':T},
'emptyList':{'items':[],'nextCursor':None,'asOf':T},
'stock':STOCK,
'price':{'stockId':'stk_aapl','quote':QUOTE,'asOf':T},
'history':{'stockId':'stk_aapl','currency':'USD','resolution':'1d','basis':'unadjusted','fromDate':'2026-11-10','toDate':'2026-11-11','points':[{'sessionDate':'2026-11-10','close':'226.80','providerTime':'2026-11-10T21:00:00Z'},{'sessionDate':'2026-11-11','close':'227.50','providerTime':'2026-11-11T21:00:00Z'}],'coverage':'complete','nextCursor':None,'asOf':T},
'emptyHistory':{'stockId':'stk_aapl','currency':'USD','resolution':'1d','basis':'unadjusted','fromDate':'2026-11-07','toDate':'2026-11-08','points':[],'coverage':'complete','nextCursor':None,'asOf':T},
'watchlist':{'items':[{'stock':STOCK,'addedAt':'2026-11-12T15:00:01Z','quote':QUOTE}],'nextCursor':None,'version':7},
'emptyWatchlist':{'items':[],'nextCursor':None,'version':0},
'add':{'stockId':'stk_aapl'},
'membership':{'stockId':'stk_aapl','addedAt':'2026-11-12T15:00:01Z','version':7},
'error':{'error':{'code':'invalid_input','message':'limit must be between 1 and 100'}}}

app=FastAPI(title='Personal Investment Dashboard API',version='1.0.0',description='Lab 5 source-generated contract. All business handlers and authentication adapters are explicitly unimplemented stubs (501). Examples are synthetic, not live market data.',servers=[{'url':'https://dashboard.example','description':'Illustrative same-origin deployment, not a live server'}])
@app.middleware('http')
async def private_http_cache(request, call_next):
    response=await call_next(request)
    if request.url.path.startswith('/v1/'):
        response.headers['Cache-Control']='private, no-store'
    return response
session=APIKeyCookie(name='dashboard_session',scheme_name='SessionCookie',auto_error=False,description='Opaque Secure, HttpOnly, SameSite session resolved by the external authentication boundary. Never use a caller-supplied owner ID.')
csrf=APIKeyHeader(name='X-CSRF-Token',scheme_name='CsrfToken',auto_error=False,description='Session-bound CSRF token; required together with SessionCookie on mutations.')
class ApiFailure(Exception):
    def __init__(self,status,code,message,headers=None): self.status,self.code,self.message,self.headers=status,code,message,headers
@app.exception_handler(ApiFailure)
async def api_failure(request,exc):
    return JSONResponse(status_code=exc.status,content={'error':{'code':exc.code,'message':exc.message}},headers=exc.headers)
@app.exception_handler(RequestValidationError)
async def validation_failure(request,exc):
    return JSONResponse(status_code=400,content={'error':{'code':'invalid_input','message':'Invalid path, query, or JSON body; follow the documented schema.'}})
@app.exception_handler(Exception)
async def unexpected_failure(request,exc):
    return JSONResponse(status_code=500,content={'error':{'code':'internal_error','message':'An unexpected server error occurred.'}})
@app.exception_handler(HTTPException)
async def http_failure(request,exc):
    return JSONResponse(status_code=exc.status_code,content={'error':{'code':'http_error','message':str(exc.detail)}},headers=exc.headers)

def current_identity(token:Annotated[str|None,Security(session)]):
    if not token:raise ApiFailure(401,'authentication_required','A valid session is required.')
    # Must validate token expiry/revocation and resolve trusted issuer+subject.
    # Accepting any nonempty cookie as identity would be unsafe.
    raise ApiFailure(501,'not_implemented','External session verification adapter is not implemented.')
def mutation_identity(principal:Annotated[str,Depends(current_identity)],token:Annotated[str|None,Security(csrf)]):
    if not token:raise ApiFailure(403,'csrf_required','A valid session-bound CSRF token is required.')
    raise ApiFailure(501,'not_implemented','CSRF verification and mutation handlers are not implemented.')
def stub():raise ApiFailure(501,'not_implemented','Contract stub: no business data was read or changed.')
def failures(*extra):
    specs={400:('invalid_input','Invalid input.'),401:('authentication_required','A valid session is required.'),429:('rate_limited','Wait before retrying.'),500:('internal_error','An unexpected server error occurred.'),501:('not_implemented','Contract stub: operation is not implemented.'),503:('unavailable','Required data or dependency is unavailable.'),403:('csrf_invalid','CSRF validation failed.'),404:('not_found','No visible resource exists.'),409:('stock_inactive','An inactive Stock cannot be used for this operation.')}
    result={}
    for code in (400,401,429,500,501,503,*extra):
        c,m=specs[code]
        result[code]={'model':Error,'description':m,'content':{'application/json':{'examples':{c:{'value':{'error':{'code':c,'message':m}}}}}}}
        if code in (429,503):result[code]['headers']={'Retry-After':{'description':'Minimum wait in whole seconds. Use backoff if absent.','schema':{'type':'integer','minimum':1},'example':2}}
    return result

def success_examples(**names):return {'application/json':{'examples':{label:{'value':EXAMPLES[name]} for label,name in names.items()}}}
READ=[Depends(current_identity)]
WRITE=[Depends(mutation_identity)]
@app.get('/v1/market/overview',operation_id='getMarketOverview',tags=['Market'],response_model=Overview,dependencies=READ,responses={**failures(),200:{'content':success_examples(overview='overview')}})
def overview():
    """Counts of supported active/priced Stocks and known session state. Unknown calendar or incomplete reference coverage returns 503. STUB."""
    stub()
@app.get('/v1/stocks',operation_id='listStocks',tags=['Stocks'],response_model=StockPage,dependencies=READ,responses={**failures(),200:{'content':success_examples(filteredPage='filteredPage',emptyList='emptyList')}})
def stocks(query:Annotated[StockQuery,Query()]):
    """Active Stocks only. Combine exchange, sector and case-insensitive name/symbol q before pagination. Default symbol ascending then stockId; trending orders absolute percentage change descending then stockId. Cursor binds normalised filters, sort and limit. Unknown/expired/mismatched cursor is 400. STUB."""
    stub()
@app.get('/v1/stocks/{stockId}',operation_id='getStock',tags=['Stocks'],response_model=Stock,dependencies=READ,responses={**failures(404),200:{'content':success_examples(stock='stock')}})
def stock(stock_id:Annotated[ID,Path(alias='stockId')]):
    """Stable identity lookup; retained inactive instruments remain identifiable. Unknown ID returns 404. STUB."""
    stub()
@app.get('/v1/stocks/{stockId}/price',operation_id='getStockPrice',tags=['Stocks'],response_model=PriceResponse,dependencies=READ,responses={**failures(404,409),200:{'content':success_examples(price='price')}})
def price(stock_id:Annotated[ID,Path(alias='stockId')]):
    """Return only a policy-valid quotation/close. Preserve source time; normal-session age >20 minutes, missing data or unknown calendar returns 503. Unknown instrument: 404; inactive: 409. STUB."""
    stub()
@app.get('/v1/stocks/{stockId}/history',operation_id='getStockHistory',tags=['Stocks'],response_model=HistoryPage,dependencies=READ,responses={**failures(404),200:{'content':success_examples(history='history',emptyHistory='emptyHistory')}})
def history(stock_id:Annotated[ID,Path(alias='stockId')],query:Annotated[HistoryQuery,Query()]):
    """Inclusive UTC date range within seven years. Daily unadjusted closes only, date ascending. Known empty coverage is 200; unknown coverage/source failure is 503. Cursor binds Stock, dates and limit. STUB."""
    stub()
@app.get('/v1/watchlist',operation_id='getMyWatchlist',tags=['Watchlist'],response_model=WatchlistPage,dependencies=READ,responses={**failures(),200:{'content':success_examples(watchlist='watchlist',emptyWatchlist='emptyWatchlist')}})
def watchlist(query:Annotated[PageQuery,Query()]):
    """Only the authenticated identity's membership; addedAt descending then stockId. Query authoritative membership on every page. A cursor bound to another owner/version or expired is 400; never serve a stale private snapshot. Missing price stays null without removing membership. STUB."""
    stub()
@app.post('/v1/watchlist/items',operation_id='addToMyWatchlist',tags=['Watchlist'],response_model=Membership,status_code=201,dependencies=WRITE,responses={**failures(403,404,409),201:{'description':'New membership durably committed.','content':success_examples(created='membership'),'headers':{'Location':{'schema':{'type':'string'},'example':'/v1/watchlist/items/stk_aapl'}}},200:{'model':Membership,'description':'Already present; confirmed no-op with existing addedAt/version.','content':success_examples(existing='membership')}})
def add(body:Annotated[AddStock,Body(openapi_examples={'add':{'value':EXAMPLES['add']}})]):
    """Owner comes only from authentication. Reject owner/version/addedAt fields. Active supported Stock required. Confirm only after authoritative commit; duplicates create no extra membership. STUB."""
    stub()
@app.delete('/v1/watchlist/items/{stockId}',operation_id='removeFromMyWatchlist',tags=['Watchlist'],status_code=204,response_class=Response,dependencies=WRITE,responses={**failures(403)})
def remove(stock_id:Annotated[ID,Path(alias='stockId')]):
    """Delete only the caller's membership, including inactive Stocks. Already absent returns 204 with no body. No existence leak about other owners. Lost commit confirmation is 503 with code change_unconfirmed. STUB."""
    stub()

def contract():
    schema=get_openapi(title=app.title,version=app.version,description=app.description,routes=app.routes,servers=app.servers)
    for path,operations in schema['paths'].items():
        for method,op in operations.items():
            if method not in ('get','post','delete'):continue
            # Runtime validation handler returns 400 instead of FastAPI's default 422.
            op['responses'].pop('422',None)
            # Cookie AND CSRF for mutations, not two alternative credentials.
            op['security']=[{'SessionCookie':[],**({'CsrfToken':[]} if method in ('post','delete') else {})}]
    # Preserve explicit JSON nulls in examples (the framework schema encoder omits them).
    response_examples={
        'getMarketOverview':{'overview':'overview'},
        'listStocks':{'filteredPage':'filteredPage','emptyList':'emptyList'},
        'getStock':{'stock':'stock'},'getStockPrice':{'price':'price'},
        'getStockHistory':{'history':'history','emptyHistory':'emptyHistory'},
        'getMyWatchlist':{'watchlist':'watchlist','emptyWatchlist':'emptyWatchlist'}}
    for operations in schema['paths'].values():
        for op in operations.values():
            names=response_examples.get(op.get('operationId'))
            if names:op['responses']['200']['content']['application/json']['examples']={k:{'value':EXAMPLES[v]} for k,v in names.items()}
    return schema
app.openapi=contract
