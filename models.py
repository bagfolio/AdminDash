import datetime
from app import db
from sqlalchemy.dialects.postgresql import JSONB


class APIEndpoint(db.Model):
    """Represents an available FMP API endpoint that can be fetched"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    endpoint_path = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    parameters = db.Column(JSONB, nullable=True)  # JSON schema for required parameters
    response_model = db.Column(db.String(100), nullable=True)  # Links to the model that stores this data
    
    def __repr__(self):
        return f"<APIEndpoint {self.name}>"


class APILog(db.Model):
    """Logs all API calls to FMP"""
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255), nullable=False)
    params = db.Column(JSONB, nullable=True)
    status_code = db.Column(db.Integer, nullable=True)
    response_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    execution_time = db.Column(db.Float, nullable=True)  # Time in seconds
    success = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f"<APILog {self.endpoint} {self.timestamp}>"


class Company(db.Model):
    """Store company profile information"""
    symbol = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    exchange = db.Column(db.String(50), nullable=True)
    industry = db.Column(db.String(255), nullable=True)
    sector = db.Column(db.String(255), nullable=True)
    cik = db.Column(db.String(20), nullable=True)
    market_cap = db.Column(db.BigInteger, nullable=True)
    data = db.Column(JSONB, nullable=True)  # Additional data
    last_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    financial_statements = db.relationship('FinancialStatement', backref='company', lazy=True)
    
    def __repr__(self):
        return f"<Company {self.symbol}>"


class FinancialStatement(db.Model):
    """Store financial statement data"""
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), db.ForeignKey('company.symbol'), nullable=False)
    statement_type = db.Column(db.String(20), nullable=False)  # income, balance, cash_flow
    period = db.Column(db.String(10), nullable=False)  # annual, quarter
    fiscal_date = db.Column(db.Date, nullable=False)
    data = db.Column(JSONB, nullable=False)  # Full statement data
    last_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<FinancialStatement {self.symbol} {self.statement_type} {self.fiscal_date}>"


class StockPrice(db.Model):
    """Store historical stock price data"""
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), db.ForeignKey('company.symbol'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open = db.Column(db.Float, nullable=True)
    high = db.Column(db.Float, nullable=True)
    low = db.Column(db.Float, nullable=True)
    close = db.Column(db.Float, nullable=True)
    adjusted_close = db.Column(db.Float, nullable=True)
    volume = db.Column(db.BigInteger, nullable=True)
    
    __table_args__ = (db.UniqueConstraint('symbol', 'date', name='unique_stock_price'),)
    
    def __repr__(self):
        return f"<StockPrice {self.symbol} {self.date}>"


class Formula(db.Model):
    """Custom formulas defined by users"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    formula_text = db.Column(db.Text, nullable=False)  # The actual formula expression
    variables = db.Column(JSONB, nullable=False)  # Variables used in the formula
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationship to results
    results = db.relationship('FormulaResult', backref='formula', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Formula {self.name}>"


class FormulaResult(db.Model):
    """Stores the results of formula calculations"""
    id = db.Column(db.Integer, primary_key=True)
    formula_id = db.Column(db.Integer, db.ForeignKey('formula.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=True)
    inputs = db.Column(JSONB, nullable=True)  # Input values used for calculation
    calculation_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    error = db.Column(db.Text, nullable=True)  # Any error during calculation
    
    __table_args__ = (db.UniqueConstraint('formula_id', 'symbol', 'date', name='unique_formula_result'),)
    
    def __repr__(self):
        return f"<FormulaResult {self.formula_id} {self.symbol} {self.date}>"


class ScheduledTask(db.Model):
    """Scheduled tasks for data fetching"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    endpoint_id = db.Column(db.Integer, db.ForeignKey('api_endpoint.id'), nullable=False)
    parameters = db.Column(JSONB, nullable=True)  # Parameters for the API call
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly
    active = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime, nullable=True)
    next_run = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationship to endpoint
    endpoint = db.relationship('APIEndpoint', backref='scheduled_tasks')
    
    def __repr__(self):
        return f"<ScheduledTask {self.name} {self.frequency}>"
