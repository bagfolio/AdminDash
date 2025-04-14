import logging
import json
from sqlalchemy import inspect, text
from app import db

logger = logging.getLogger(__name__)


def get_table_schema(table_name):
    """
    Get schema information for a database table
    
    Args:
        table_name (str): Name of the table
        
    Returns:
        dict: Schema information
    """
    try:
        inspector = inspect(db.engine)
        columns = inspector.get_columns(table_name)
        pk = inspector.get_pk_constraint(table_name)
        fks = inspector.get_foreign_keys(table_name)
        
        return {
            'table_name': table_name,
            'columns': columns,
            'primary_key': pk,
            'foreign_keys': fks
        }
    except Exception as e:
        logger.error(f"Error getting schema for table {table_name}: {e}")
        return None


def execute_raw_query(query, params=None, fetch=True):
    """
    Execute a raw SQL query with proper error handling
    
    Args:
        query (str): SQL query to execute
        params (dict): Query parameters
        fetch (bool): Whether to fetch results
        
    Returns:
        dict: Query results or execution info
    """
    if params is None:
        params = {}
        
    try:
        result = db.session.execute(text(query), params)
        
        if fetch and result.returns_rows:
            data = [dict(row) for row in result]
            return {
                'success': True,
                'data': data,
                'row_count': len(data)
            }
        else:
            db.session.commit()
            return {
                'success': True,
                'message': 'Query executed successfully',
                'row_count': result.rowcount
            }
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error executing query: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def format_currency(value):
    """Format a value as currency"""
    if value is None:
        return 'N/A'
    
    try:
        # Format as currency with commas
        return f"${value:,.2f}"
    except (ValueError, TypeError):
        return 'N/A'


def format_number(value, decimal_places=2):
    """Format a numeric value with commas and specified decimal places"""
    if value is None:
        return 'N/A'
    
    try:
        # Format with commas and decimal places
        format_str = f"{{:,.{decimal_places}f}}"
        return format_str.format(value)
    except (ValueError, TypeError):
        return 'N/A'


def format_percent(value):
    """Format a value as a percentage"""
    if value is None:
        return 'N/A'
    
    try:
        # Format as percentage
        return f"{value:.2f}%"
    except (ValueError, TypeError):
        return 'N/A'


def get_database_tables():
    """Get a list of all tables in the database"""
    try:
        inspector = inspect(db.engine)
        return inspector.get_table_names()
    except Exception as e:
        logger.error(f"Error getting database tables: {e}")
        return []


def get_table_row_count(table_name):
    """Get the number of rows in a table"""
    try:
        result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        return result.scalar()
    except Exception as e:
        logger.error(f"Error getting row count for table {table_name}: {e}")
        return 0
