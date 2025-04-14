import logging
import re
import numpy as np
import pandas as pd
from datetime import datetime
from app import db
from models import (
    Formula, FormulaResult, FinancialStatement, StockPrice, Company
)

logger = logging.getLogger(__name__)


def parse_formula(formula_text, variables):
    """
    Parse and validate a formula string
    
    Args:
        formula_text (str): The formula text to parse
        variables (dict): Variables available for the formula
        
    Returns:
        dict: Validation result
    """
    # Basic validation
    if not formula_text or not variables:
        return {'valid': False, 'error': 'Formula or variables cannot be empty'}
    
    # Check for invalid characters
    if re.search(r'[^a-zA-Z0-9_\s\+\-\*\/\(\)\.\,\>\<\=\!]', formula_text):
        return {'valid': False, 'error': 'Formula contains invalid characters'}
    
    # Replace variable names with placeholders for evaluation
    test_formula = formula_text
    for var_name in variables:
        test_formula = test_formula.replace(var_name, '1')
    
    # Try to evaluate the formula with test values
    try:
        # Use eval in a safe way - we've already sanitized the input
        # and are only using it to check syntax
        eval(test_formula)
        return {'valid': True}
    except Exception as e:
        return {'valid': False, 'error': f"Syntax error: {str(e)}"}


def get_variable_data(symbol, variable, start_date, end_date=None):
    """
    Get data for a specific variable from the database
    
    Args:
        symbol (str): Stock symbol
        variable (str): Variable name
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): Optional end date
        
    Returns:
        pandas.Series: Time series data for the variable
    """
    try:
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        
        # Identify variable source
        if variable in ['open', 'high', 'low', 'close', 'adjusted_close', 'volume']:
            # Stock price data
            query = StockPrice.query.filter_by(symbol=symbol)
            query = query.filter(StockPrice.date >= start)
            if end:
                query = query.filter(StockPrice.date <= end)
            
            prices = query.order_by(StockPrice.date).all()
            
            # Convert to dataframe
            if prices:
                df = pd.DataFrame([{
                    'date': p.date,
                    'value': getattr(p, variable)
                } for p in prices])
                df.set_index('date', inplace=True)
                return df['value']
            else:
                return pd.Series()
                
        elif variable in ['pe_ratio', 'price_to_book', 'debt_to_equity']:
            # Custom calculated ratios
            if variable == 'pe_ratio':
                # Get latest income statement and stock price
                income = (
                    FinancialStatement.query
                    .filter_by(symbol=symbol, statement_type='income', period='annual')
                    .order_by(FinancialStatement.fiscal_date.desc())
                    .first()
                )
                
                latest_price = (
                    StockPrice.query
                    .filter_by(symbol=symbol)
                    .order_by(StockPrice.date.desc())
                    .first()
                )
                
                if income and latest_price:
                    net_income = income.data.get('netIncome')
                    eps = income.data.get('eps')
                    price = latest_price.close
                    
                    if eps and eps != 0:
                        return pd.Series([price / eps], index=[latest_price.date])
                
                return pd.Series()
                
            elif variable == 'price_to_book':
                # Implementation for price to book ratio
                pass
                
            elif variable == 'debt_to_equity':
                # Implementation for debt to equity ratio
                pass
        
        else:
            # Financial statement data
            # Determine statement type based on variable name
            statement_type = 'income'  # Default
            common_metrics = {
                'income': ['revenue', 'grossProfit', 'operatingIncome', 'netIncome', 'eps'],
                'balance': ['totalAssets', 'totalLiabilities', 'totalEquity', 'cashAndCashEquivalents'],
                'cash_flow': ['operatingCashFlow', 'capitalExpenditure', 'freeCashFlow']
            }
            
            for s_type, metrics in common_metrics.items():
                if variable in metrics:
                    statement_type = s_type
                    break
            
            # Query for financial statements
            statements = (
                FinancialStatement.query
                .filter_by(symbol=symbol, statement_type=statement_type)
                .filter(FinancialStatement.fiscal_date >= start)
            )
            
            if end:
                statements = statements.filter(FinancialStatement.fiscal_date <= end)
                
            statements = statements.order_by(FinancialStatement.fiscal_date).all()
            
            # Convert to dataframe
            if statements:
                df = pd.DataFrame([{
                    'date': s.fiscal_date,
                    'value': s.data.get(variable)
                } for s in statements])
                df.set_index('date', inplace=True)
                return df['value']
            else:
                return pd.Series()
        
    except Exception as e:
        logger.error(f"Error getting variable data: {e}")
        return pd.Series()


def evaluate_formula(formula, symbol, start_date, end_date=None):
    """
    Evaluate a formula for a specific symbol and date range
    
    Args:
        formula (Formula): Formula model
        symbol (str): Stock symbol
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): Optional end date
        
    Returns:
        list: Formula results
    """
    try:
        # Get data for each variable
        variables_data = {}
        for var_name in formula.variables:
            variables_data[var_name] = get_variable_data(symbol, var_name, start_date, end_date)
        
        if not variables_data or all(len(data) == 0 for data in variables_data.values()):
            logger.warning(f"No data found for formula variables: {formula.name}, symbol: {symbol}")
            return []
        
        # Combine all data on a common date index
        all_data = pd.DataFrame(variables_data)
        
        # For each date, evaluate the formula
        results = []
        formula_text = formula.formula_text
        
        for date, row in all_data.iterrows():
            if row.isnull().any():
                continue  # Skip dates with missing values
                
            try:
                # Create evaluation namespace
                eval_vars = {}
                for var_name in formula.variables:
                    eval_vars[var_name] = row[var_name]
                
                # Evaluate the formula
                result_value = eval(formula_text, {"__builtins__": {}}, eval_vars)
                
                # Create or update result in database
                date_str = date.strftime('%Y-%m-%d')
                existing = FormulaResult.query.filter_by(
                    formula_id=formula.id,
                    symbol=symbol,
                    date=date
                ).first()
                
                if existing:
                    existing.value = result_value
                    existing.inputs = {k: float(v) for k, v in eval_vars.items()}
                    existing.calculation_time = datetime.utcnow()
                    existing.error = None
                else:
                    result = FormulaResult(
                        formula_id=formula.id,
                        symbol=symbol,
                        date=date,
                        value=result_value,
                        inputs={k: float(v) for k, v in eval_vars.items()},
                        calculation_time=datetime.utcnow()
                    )
                    db.session.add(result)
                
                results.append({
                    'date': date_str,
                    'value': result_value,
                    'inputs': {k: float(v) for k, v in eval_vars.items()}
                })
                
            except Exception as e:
                logger.error(f"Error evaluating formula for date {date}: {e}")
                # Record the error
                error_result = FormulaResult(
                    formula_id=formula.id,
                    symbol=symbol,
                    date=date,
                    value=None,
                    inputs={k: float(v) if not pd.isna(v) else None for k, v in row.items()},
                    calculation_time=datetime.utcnow(),
                    error=str(e)
                )
                db.session.add(error_result)
        
        db.session.commit()
        return results
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error evaluating formula: {e}")
        return []
