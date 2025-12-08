import pytest
from src.ai.dynamic_fair_factor import DynamicFairFactor


def test_get_dynamic_take_profit_by_name_defaults():
    df = DynamicFairFactor()
    # Bot_Meme_Scalper, 0 minutes -> 1.2
    tp0 = df.get_dynamic_take_profit_by_name('Bot_Meme_Scalper', 0)
    assert pytest.approx(tp0, 0.001) == 1.2
    # 15 minutes -> 0.8
    tp15 = df.get_dynamic_take_profit_by_name('Bot_Meme_Scalper', 15)
    assert pytest.approx(tp15, 0.001) == 0.8
    # 50 minutes -> 0.5
    tp50 = df.get_dynamic_take_profit_by_name('Bot_Meme_Scalper', 50)
    assert pytest.approx(tp50, 0.001) == 0.5


def test_get_dynamic_rsi_by_name_defaults():
    df = DynamicFairFactor()
    rsi0 = df.get_dynamic_rsi_by_name('Bot_Estavel_Holder', 0)
    assert isinstance(rsi0, dict)
    assert rsi0['compra'] == 35
    assert rsi0['venda'] == 70

    rsi60 = df.get_dynamic_rsi_by_name('Bot_Estavel_Holder', 60)
    assert rsi60['compra'] == 40
    assert rsi60['venda'] == 68
