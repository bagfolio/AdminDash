import os
import requests
import time
import logging
import json
from datetime import datetime
from app import db, app
from models import APILog, Company, FinancialStatement, StockPrice

logger = logging.getLogger(__name__)

def make_api_request(endpoint, params=None):
    """
    Make a request to the FMP API with proper logging
    
    Args:
        endpoint (str): API endpoint path
        params (dict): Optional parameters
        
    Returns:
        dict: API response or error information
    """
    api_key = app.config["FMP_API_KEY"]
    base_url = app.config["FMP_API_BASE_URL"]
    url = f"{base_url}/{endpoint}"
    
    # Add API key to params
    if params is None:
        params = {}
    params['apikey'] = api_key
    
    # Create log entry
    log_entry = APILog(
        endpoint=endpoint,
        params=params,
        timestamp=datetime.utcnow()
    )
    
    start_time = time.time()
    try:
        response = requests.get(url, params=params, timeout=30)
        execution_time = time.time() - start_time
        
        # Update log with response info
        log_entry.status_code = response.status_code
        log_entry.execution_time = execution_time
        log_entry.response_size = len(response.content)
        
        if response.status_code == 200:
            log_entry.success = True
            db.session.add(log_entry)
            db.session.commit()
            return {
                'success': True,
                'data': response.json()
            }
        else:
            log_entry.success = False
            log_entry.error_message = f"API returned {response.status_code}: {response.text}"
            db.session.add(log_entry)
            db.session.commit()
            return {
                'success': False,
                'error': f"API returned {response.status_code}: {response.text}",
                'status_code': response.status_code
            }
    except Exception as e:
        execution_time = time.time() - start_time
        log_entry.success = False
        log_entry.error_message = str(e)
        log_entry.execution_time = execution_time
        db.session.add(log_entry)
        db.session.commit()
        logger.error(f"API request failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def fetch_endpoint_data(endpoint, parameters=None):
    """
    Fetch data from a specific FMP endpoint and store in database
    
    Args:
        endpoint (APIEndpoint): The endpoint model
        parameters (dict): Optional parameters for the API call
        
    Returns:
        dict: Result information
    """
    if parameters is None:
        parameters = {}
    
    # Make API request
    result = make_api_request(endpoint.endpoint_path, parameters)
    
    if not result['success']:
        return result
    
    # Determine which model to use based on endpoint
    data = result['data']
    rows_affected = 0
    
    # Process and store data based on endpoint type
    if endpoint.response_model == 'Company':
        rows_affected = store_company_data(data)
    elif endpoint.response_model == 'FinancialStatement':
        statement_type = parameters.get('statement_type', 'income')
        period = parameters.get('period', 'annual')
        rows_affected = store_financial_statements(data, statement_type, period)
    elif endpoint.response_model == 'StockPrice':
        rows_affected = store_stock_prices(data)
    else:
        # Generic storage as JSON in appropriate table
        logger.warning(f"No specific handler for response model: {endpoint.response_model}")
    
    return {
        'success': True,
        'rows_affected': rows_affected
    }


def store_company_data(companies_data):
    """Store company profile data in the database"""
    count = 0
    for company_data in companies_data:
        symbol = company_data.get('symbol')
        if not symbol:
            continue
            
        # Check if company already exists
        company = Company.query.get(symbol)
        if company:
            # Update existing company
            company.name = company_data.get('companyName', company.name)
            company.exchange = company_data.get('exchange')
            company.industry = company_data.get('industry')
            company.sector = company_data.get('sector')
            company.cik = company_data.get('cik')
            company.market_cap = company_data.get('mktCap')
            company.data = company_data
            company.last_updated = datetime.utcnow()
        else:
            # Create new company
            company = Company(
                symbol=symbol,
                name=company_data.get('companyName', 'Unknown'),
                exchange=company_data.get('exchange'),
                industry=company_data.get('industry'),
                sector=company_data.get('sector'),
                cik=company_data.get('cik'),
                market_cap=company_data.get('mktCap'),
                data=company_data,
                last_updated=datetime.utcnow()
            )
            db.session.add(company)
        
        count += 1
    
    db.session.commit()
    return count


def store_financial_statements(statements_data, statement_type, period):
    """Store financial statement data in the database"""
    count = 0
    for statement in statements_data:
        symbol = statement.get('symbol')
        if not symbol:
            continue
            
        # Parse fiscal date
        date_str = statement.get('date')
        if not date_str:
            continue
            
        try:
            fiscal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {date_str}")
            continue
        
        # Look for existing statement
        existing = FinancialStatement.query.filter_by(
            symbol=symbol,
            statement_type=statement_type,
            period=period,
            fiscal_date=fiscal_date
        ).first()
        
        if existing:
            # Update existing statement
            existing.data = statement
            existing.last_updated = datetime.utcnow()
        else:
            # Create new statement
            new_statement = FinancialStatement(
                symbol=symbol,
                statement_type=statement_type,
                period=period,
                fiscal_date=fiscal_date,
                data=statement,
                last_updated=datetime.utcnow()
            )
            db.session.add(new_statement)
        
        count += 1
    
    db.session.commit()
    return count


def store_stock_prices(prices_data):
    """Store historical stock price data in the database"""
    count = 0
    
    # Determine if this is for a single symbol or multiple
    if isinstance(prices_data, dict):
        # Single symbol format
        for symbol, prices in prices_data.items():
            count += store_symbol_prices(symbol, prices)
    elif isinstance(prices_data, list):
        # Direct list of prices (single symbol)
        symbol = prices_data[0].get('symbol') if prices_data else None
        if symbol:
            count += store_symbol_prices(symbol, prices_data)
    
    return count


def store_symbol_prices(symbol, prices):
    """Store prices for a specific symbol"""
    count = 0
    for price in prices:
        date_str = price.get('date')
        if not date_str:
            continue
            
        try:
            price_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {date_str}")
            continue
        
        # Check for existing price
        existing = StockPrice.query.filter_by(
            symbol=symbol,
            date=price_date
        ).first()
        
        if existing:
            # Update existing price
            existing.open = price.get('open')
            existing.high = price.get('high')
            existing.low = price.get('low')
            existing.close = price.get('close')
            existing.adjusted_close = price.get('adjClose')
            existing.volume = price.get('volume')
        else:
            # Create new price entry
            new_price = StockPrice(
                symbol=symbol,
                date=price_date,
                open=price.get('open'),
                high=price.get('high'),
                low=price.get('low'),
                close=price.get('close'),
                adjusted_close=price.get('adjClose'),
                volume=price.get('volume')
            )
            db.session.add(new_price)
        
        count += 1
    
    db.session.commit()
    return count


def get_available_endpoints():
    """
    Get a list of available FMP API endpoints for configuration
    This is a predefined list since FMP doesn't provide an endpoint discovery API
    
    Returns:
        list: Available endpoints with their configurations
    """
    endpoints = [
        {
            'name': 'Company Profile',
            'endpoint_path': 'profile/{symbol}',
            'description': 'Get company profile information',
            'parameters': {
                'symbol': {'type': 'string', 'required': True}
            },
            'response_model': 'Company'
        },
        {
            'name': 'Income Statement',
            'endpoint_path': 'income-statement/{symbol}',
            'description': 'Get company income statements',
            'parameters': {
                'symbol': {'type': 'string', 'required': True},
                'period': {'type': 'string', 'required': False, 'default': 'annual', 'options': ['annual', 'quarter']},
                'limit': {'type': 'integer', 'required': False, 'default': 10}
            },
            'response_model': 'FinancialStatement'
        },
        {
            'name': 'Balance Sheet',
            'endpoint_path': 'balance-sheet-statement/{symbol}',
            'description': 'Get company balance sheets',
            'parameters': {
                'symbol': {'type': 'string', 'required': True},
                'period': {'type': 'string', 'required': False, 'default': 'annual', 'options': ['annual', 'quarter']},
                'limit': {'type': 'integer', 'required': False, 'default': 10}
            },
            'response_model': 'FinancialStatement'
        },
        {
            'name': 'Cash Flow Statement',
            'endpoint_path': 'cash-flow-statement/{symbol}',
            'description': 'Get company cash flow statements',
            'parameters': {
                'symbol': {'type': 'string', 'required': True},
                'period': {'type': 'string', 'required': False, 'default': 'annual', 'options': ['annual', 'quarter']},
                'limit': {'type': 'integer', 'required': False, 'default': 10}
            },
            'response_model': 'FinancialStatement'
        },
        {
            'name': 'Historical Stock Prices',
            'endpoint_path': 'historical-price-full/{symbol}',
            'description': 'Get historical stock prices',
            'parameters': {
                'symbol': {'type': 'string', 'required': True},
                'from': {'type': 'string', 'required': False, 'format': 'YYYY-MM-DD'},
                'to': {'type': 'string', 'required': False, 'format': 'YYYY-MM-DD'},
                'timeseries': {'type': 'integer', 'required': False, 'description': 'Number of data points'}
            },
            'response_model': 'StockPrice'
        },
        {
            'name': 'Company Financial Ratios',
            'endpoint_path': 'ratios/{symbol}',
            'description': 'Get company financial ratios',
            'parameters': {
                'symbol': {'type': 'string', 'required': True},
                'period': {'type': 'string', 'required': False, 'default': 'annual', 'options': ['annual', 'quarter']},
                'limit': {'type': 'integer', 'required': False, 'default': 10}
            },
            'response_model': 'FinancialStatement'
        },
        {
            'name': 'Company Key Metrics',
            'endpoint_path': 'key-metrics/{symbol}',
            'description': 'Get company key metrics',
            'parameters': {
                'symbol': {'type': 'string', 'required': True},
                'period': {'type': 'string', 'required': False, 'default': 'annual', 'options': ['annual', 'quarter']},
                'limit': {'type': 'integer', 'required': False, 'default': 10}
            },
            'response_model': 'FinancialStatement'
        },
        {
            'name': 'Stock Market Index',
            'endpoint_path': 'quote/{index}',
            'description': 'Get stock market index data',
            'parameters': {
                'index': {'type': 'string', 'required': True, 'description': 'Index symbol like ^DJI, ^GSPC'}
            },
            'response_model': 'StockPrice'
        }
    ]
    
    return endpoints
