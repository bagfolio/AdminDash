from flask import render_template, request, jsonify, redirect, url_for, flash
from app import db
from models import (
    APIEndpoint, APILog, Company, FinancialStatement, StockPrice,
    Formula, FormulaResult, ScheduledTask
)
from fmp_api import fetch_endpoint_data, get_available_endpoints
from formula_engine import evaluate_formula, parse_formula
from scheduler import schedule_task, remove_task
import json
import logging
from sqlalchemy import inspect, text
from datetime import datetime

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register all routes with the Flask app"""
    
    @app.route('/')
    def index():
        """Main dashboard page"""
        # Get counts for different data types
        company_count = Company.query.count()
        statement_count = FinancialStatement.query.count()
        price_count = StockPrice.query.count()
        formula_count = Formula.query.count()
        
        # Get latest API logs
        recent_logs = APILog.query.order_by(APILog.timestamp.desc()).limit(5).all()
        
        # Get data freshness
        latest_price = StockPrice.query.order_by(StockPrice.date.desc()).first()
        latest_statement = FinancialStatement.query.order_by(FinancialStatement.last_updated.desc()).first()
        
        return render_template('dashboard.html', 
                              company_count=company_count,
                              statement_count=statement_count,
                              price_count=price_count,
                              formula_count=formula_count,
                              recent_logs=recent_logs,
                              latest_price=latest_price,
                              latest_statement=latest_statement)
    
    @app.route('/database')
    def database():
        """Database browsing and management page"""
        # Get all table names
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Default to viewing the first table if one exists
        selected_table = request.args.get('table', tables[0] if tables else None)
        
        # Get table columns and sample data if a table is selected
        columns = []
        sample_data = []
        if selected_table:
            columns = inspector.get_columns(selected_table)
            
            # Get sample data (first 10 rows)
            try:
                result = db.session.execute(text(f'SELECT * FROM "{selected_table}" LIMIT 10'))
                sample_data = [dict(row) for row in result]
            except Exception as e:
                logger.error(f"Error fetching sample data: {e}")
                flash(f"Error fetching sample data: {e}", "danger")
        
        return render_template('database.html', 
                              tables=tables,
                              selected_table=selected_table,
                              columns=columns,
                              sample_data=sample_data)
    
    @app.route('/api/table_data', methods=['GET'])
    def table_data():
        """API to get paginated table data"""
        table_name = request.args.get('table')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        offset = (page - 1) * limit
        
        if not table_name:
            return jsonify({"error": "Table name is required"}), 400
            
        try:
            # Get total count
            count_result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            total = count_result.scalar()
            
            # Get data for current page
            result = db.session.execute(text(f'SELECT * FROM "{table_name}" LIMIT :limit OFFSET :offset'),
                                      {'limit': limit, 'offset': offset})
            
            # Convert to list of dicts
            data = [dict(row) for row in result]
            
            return jsonify({
                "data": data,
                "total": total,
                "page": page,
                "limit": limit
            })
            
        except Exception as e:
            logger.error(f"Error fetching table data: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/execute_query', methods=['POST'])
    def execute_query():
        """Execute a raw SQL query"""
        query = request.json.get('query')
        if not query:
            return jsonify({"error": "Query is required"}), 400
            
        try:
            # Execute the query
            result = db.session.execute(text(query))
            
            # Check if this is a SELECT query
            if result.returns_rows:
                # Convert to list of dicts
                data = [dict(row) for row in result]
                return jsonify({
                    "success": True,
                    "data": data,
                    "rowCount": len(data)
                })
            else:
                # For non-SELECT queries
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": "Query executed successfully",
                    "rowCount": result.rowcount
                })
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error executing query: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/formulas')
    def formulas():
        """Custom formula management page"""
        # Get all formulas
        all_formulas = Formula.query.all()
        
        # Get sample variables for formula creation
        variables = {
            "financial_statement": [
                "revenue", "netIncome", "totalAssets", "totalLiabilities", 
                "operatingIncome", "ebitda", "eps", "grossProfit"
            ],
            "stock_price": [
                "open", "high", "low", "close", "volume"
            ],
            "custom": [
                "pe_ratio", "price_to_book", "debt_to_equity"
            ]
        }
        
        return render_template('formulas.html',
                             formulas=all_formulas,
                             variables=variables)
    
    @app.route('/api/formulas', methods=['POST'])
    def create_formula():
        """Create a new custom formula"""
        data = request.json
        name = data.get('name')
        description = data.get('description')
        formula_text = data.get('formula_text')
        variables = data.get('variables')
        
        if not name or not formula_text or not variables:
            return jsonify({"error": "Name, formula text, and variables are required"}), 400
            
        try:
            # Validate formula syntax
            parse_result = parse_formula(formula_text, variables)
            if not parse_result['valid']:
                return jsonify({"error": f"Invalid formula: {parse_result['error']}"}), 400
                
            # Create new formula
            formula = Formula(
                name=name,
                description=description,
                formula_text=formula_text,
                variables=variables
            )
            
            db.session.add(formula)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Formula created successfully",
                "id": formula.id
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating formula: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/formulas/<int:formula_id>', methods=['DELETE'])
    def delete_formula(formula_id):
        """Delete a formula"""
        formula = Formula.query.get_or_404(formula_id)
        
        try:
            db.session.delete(formula)
            db.session.commit()
            return jsonify({"success": True, "message": "Formula deleted successfully"})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting formula: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/formulas/<int:formula_id>/calculate', methods=['POST'])
    def calculate_formula(formula_id):
        """Calculate formula results for specified symbols and date range"""
        formula = Formula.query.get_or_404(formula_id)
        data = request.json
        symbols = data.get('symbols', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not symbols or not start_date:
            return jsonify({"error": "Symbols and start date are required"}), 400
            
        try:
            results = []
            for symbol in symbols:
                # Evaluate formula for the symbol and date range
                formula_results = evaluate_formula(formula, symbol, start_date, end_date)
                results.extend(formula_results)
                
            return jsonify({
                "success": True,
                "message": f"Formula calculated for {len(results)} data points",
                "results": results
            })
            
        except Exception as e:
            logger.error(f"Error calculating formula: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/scheduler')
    def scheduler_page():
        """Scheduler management page"""
        # Get all scheduled tasks
        tasks = ScheduledTask.query.all()
        
        # Get all available endpoints
        endpoints = APIEndpoint.query.all()
        
        return render_template('scheduler.html',
                             tasks=tasks,
                             endpoints=endpoints)
    
    @app.route('/api/scheduler/tasks', methods=['POST'])
    def create_task():
        """Create a new scheduled task"""
        data = request.json
        name = data.get('name')
        endpoint_id = data.get('endpoint_id')
        parameters = data.get('parameters')
        frequency = data.get('frequency')
        
        if not name or not endpoint_id or not frequency:
            return jsonify({"error": "Name, endpoint ID, and frequency are required"}), 400
            
        try:
            # Get the endpoint
            endpoint = APIEndpoint.query.get_or_404(endpoint_id)
            
            # Create task
            task = ScheduledTask(
                name=name,
                endpoint_id=endpoint_id,
                parameters=parameters,
                frequency=frequency
            )
            
            db.session.add(task)
            db.session.commit()
            
            # Schedule the task
            schedule_task(task)
            
            return jsonify({
                "success": True,
                "message": "Task scheduled successfully",
                "id": task.id
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating scheduled task: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/scheduler/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        """Delete a scheduled task"""
        task = ScheduledTask.query.get_or_404(task_id)
        
        try:
            # Remove the task from the scheduler
            remove_task(task)
            
            # Delete from database
            db.session.delete(task)
            db.session.commit()
            
            return jsonify({"success": True, "message": "Task deleted successfully"})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting task: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/fetch', methods=['POST'])
    def fetch_data():
        """Manually fetch data from FMP API"""
        data = request.json
        endpoint_id = data.get('endpoint_id')
        parameters = data.get('parameters', {})
        
        if not endpoint_id:
            return jsonify({"error": "Endpoint ID is required"}), 400
            
        try:
            # Get the endpoint
            endpoint = APIEndpoint.query.get_or_404(endpoint_id)
            
            # Fetch data
            result = fetch_endpoint_data(endpoint, parameters)
            
            if result['success']:
                return jsonify({
                    "success": True,
                    "message": f"Successfully fetched data for {endpoint.name}",
                    "rows_affected": result.get('rows_affected', 0)
                })
            else:
                return jsonify({
                    "success": False,
                    "error": result.get('error', 'Unknown error')
                }), 400
                
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/settings')
    def settings():
        """Settings and API endpoint management page"""
        # Get all API endpoints
        endpoints = APIEndpoint.query.all()
        
        # Get API logs statistics
        total_calls = APILog.query.count()
        successful_calls = APILog.query.filter_by(success=True).count()
        failed_calls = APILog.query.filter_by(success=False).count()
        
        # Get average response time
        avg_time_result = db.session.query(db.func.avg(APILog.execution_time)).scalar()
        avg_time = round(avg_time_result, 2) if avg_time_result else 0
        
        return render_template('settings.html',
                             endpoints=endpoints,
                             total_calls=total_calls,
                             successful_calls=successful_calls,
                             failed_calls=failed_calls,
                             avg_time=avg_time)
    
    @app.route('/api/endpoints', methods=['POST'])
    def create_endpoint():
        """Create a new API endpoint"""
        data = request.json
        name = data.get('name')
        endpoint_path = data.get('endpoint_path')
        description = data.get('description')
        parameters = data.get('parameters')
        response_model = data.get('response_model')
        
        if not name or not endpoint_path:
            return jsonify({"error": "Name and endpoint path are required"}), 400
            
        try:
            endpoint = APIEndpoint(
                name=name,
                endpoint_path=endpoint_path,
                description=description,
                parameters=parameters,
                response_model=response_model
            )
            
            db.session.add(endpoint)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Endpoint created successfully",
                "id": endpoint.id
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating endpoint: {e}")
            return jsonify({"error": str(e)}), 500
            
    @app.route('/api/endpoints/sync', methods=['POST'])
    def sync_endpoints():
        """Sync available endpoints from FMP API"""
        try:
            endpoints = get_available_endpoints()
            
            # Create or update endpoints
            counter = 0
            for ep in endpoints:
                existing = APIEndpoint.query.filter_by(endpoint_path=ep['endpoint_path']).first()
                if existing:
                    # Update existing
                    existing.name = ep['name']
                    existing.description = ep['description']
                    existing.parameters = ep['parameters']
                    existing.response_model = ep['response_model']
                else:
                    # Create new
                    new_endpoint = APIEndpoint(**ep)
                    db.session.add(new_endpoint)
                    counter += 1
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": f"Successfully synced endpoints. Added {counter} new endpoints."
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error syncing endpoints: {e}")
            return jsonify({"error": str(e)}), 500

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_message="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('base.html', error_message="Server error occurred"), 500
