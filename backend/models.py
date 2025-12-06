"""
Modelos Pydantic para a API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# ==================== AUTH MODELS ====================

class Token(BaseModel):
    """Token de acesso JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class TokenData(BaseModel):
    """Dados contidos no token"""
    username: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[List[str]] = None


class UserBase(BaseModel):
    """Base do usuário"""
    username: str = Field(..., min_length=3, max_length=50)
    role: str = Field(default="viewer")


class UserCreate(UserBase):
    """Criar usuário"""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Atualizar usuário"""
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Resposta do usuário (sem senha)"""
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserInDB(UserBase):
    """Usuário no banco"""
    id: int
    hashed_password: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class LoginRequest(BaseModel):
    """Request de login"""
    username: str
    password: str


# ==================== BOT MODELS ====================

class BotStatus(BaseModel):
    """Status de um bot"""
    name: str
    status: str  # running, stopped, error
    pnl_today: float
    pnl_total: float
    trades_today: int
    win_rate: float
    open_positions: int
    capital_allocated: float
    last_trade: Optional[datetime] = None


class Position(BaseModel):
    """Posição aberta"""
    id: int
    bot_name: str
    symbol: str
    side: str
    entry_price: float
    current_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    opened_at: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class Trade(BaseModel):
    """Trade executado"""
    id: int
    bot_name: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    opened_at: datetime
    closed_at: datetime
    duration_minutes: int


class DailyStats(BaseModel):
    """Estatísticas diárias"""
    date: str
    pnl: float
    trades: int
    wins: int
    losses: int
    win_rate: float
    best_trade: float
    worst_trade: float
    volume: float


# ==================== CONFIG MODELS ====================

class BotConfig(BaseModel):
    """Configuração de um bot"""
    name: str
    enabled: bool
    amount_per_trade: float
    take_profit: float
    stop_loss: float
    max_positions: int
    symbols: List[str]


class GlobalConfig(BaseModel):
    """Configurações globais"""
    monthly_target: float
    risk_per_trade: float
    max_daily_loss: float
    trading_hours_start: int
    trading_hours_end: int
    poupanca_enabled: bool
    poupanca_percentage: float


class ConfigUpdate(BaseModel):
    """Atualização de configuração"""
    bot_name: Optional[str] = None
    config: Dict[str, Any]


# ==================== DASHBOARD MODELS ====================

class DashboardSummary(BaseModel):
    """Resumo do dashboard"""
    total_balance: float
    available_balance: float
    in_positions: float
    pnl_today: float
    pnl_week: float
    pnl_month: float
    total_trades: int
    active_bots: int
    open_positions: int
    win_rate: float


class Alert(BaseModel):
    """Alerta do sistema"""
    id: int
    type: str  # info, warning, error
    message: str
    created_at: datetime
    read: bool = False


# ==================== ACTION MODELS ====================

class ManualTradeRequest(BaseModel):
    """Request para trade manual"""
    symbol: str
    side: str  # buy, sell
    amount: float
    price: Optional[float] = None  # None = market order


class ClosePositionRequest(BaseModel):
    """Request para fechar posição"""
    position_id: int
    reason: Optional[str] = None


class BotActionRequest(BaseModel):
    """Request para ação no bot"""
    action: str  # start, stop, restart
    bot_name: Optional[str] = None  # None = todos os bots


# ==================== RESPONSE MODELS ====================

class APIResponse(BaseModel):
    """Resposta padrão da API"""
    success: bool
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    """Resposta paginada"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int


# Atualizar referências circulares
Token.model_rebuild()
