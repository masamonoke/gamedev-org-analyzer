from threading import Lock

import yfinance as yf
from pandas.core.frame import DataFrame

from common.config import logging


# https://en.wikipedia.org/wiki/Piotroski_F-score
class FundamentalAnalysis:
    def __init__(self, company_ticker: str) -> None:
        ticker = yf.Ticker(company_ticker)
        balance_sheet = ticker.get_balance_sheet()
        if type(balance_sheet) == DataFrame:
            self.balance_sheet: DataFrame = balance_sheet
        self.income_statement = ticker.get_income_stmt()
        self.cfs = ticker.get_cash_flow()
        self.years = self.balance_sheet.columns

    def piotroski_f_score(self) -> float:
        score = self._profitability() + self._leverage() + self._operating_efficiency()
        return score

    def _profitability(self) -> float:
        net_income = self.income_statement[self.years[0]]["NetIncome"]
        net_income_prev = self.income_statement[self.years[1]]["NetIncome"]
        income_score = 1 if net_income > 0 else 0
        income__prev_score = 1 if net_income_prev > 0 else 0

        op_cashflow = self.cfs[self.years[0]]["OperatingCashFlow"]
        op_cashflow_score = 1 if op_cashflow > 0 else 0

        avg_assets = (self.balance_sheet[self.years[0]]["TotalAssets"] + self.balance_sheet[self.years[1]][
            "TotalAssets"]) / 2
        avg_assets_prev = (self.balance_sheet[self.years[1]]["TotalAssets"] + self.balance_sheet[self.years[2]][
            "TotalAssets"]) / 2

        roa = net_income / avg_assets
        roa_prev = net_income_prev / avg_assets_prev
        roa_score = 1 if roa > roa_prev else 0

        total_assets = self.balance_sheet[self.years[0]]["TotalAssets"]
        accurals = op_cashflow / total_assets - roa
        accurals_score = 1 if accurals > 0 else 0

        score = income_score + income__prev_score + op_cashflow_score + roa_score + accurals_score

        return float(score)

    def _leverage(self) -> float:
        try:
            long_term_debt = self.balance_sheet[self.years[0]]["LongTermDebt"]
            total_assets = self.balance_sheet[self.years[0]]["TotalAssets"]
            debt_ratio = long_term_debt / total_assets
            debt_ratio_score = 1 if debt_ratio > 0 else 0
        except KeyError:
            # there can be no debt
            debt_ratio_score = 1

        current_assets = self.balance_sheet[self.years[0]]["CurrentAssets"]
        current_liabilities = self.balance_sheet[self.years[0]]["CurrentLiabilities"]
        current_ratio = current_assets / current_liabilities
        current_ratio_score = 1 if current_ratio > 1 else 0

        leverage_score = debt_ratio_score + current_ratio_score
        return float(leverage_score)

    def _operating_efficiency(self) -> float:
        gross_profit = self.income_statement[self.years[0]]["GrossProfit"]
        gross_profit_prev = self.income_statement[self.years[1]]["GrossProfit"]

        revenue = self.income_statement[self.years[0]]["TotalRevenue"]
        revenue_prev = self.income_statement[self.years[1]]["TotalRevenue"]

        gross_margin = gross_profit / revenue
        gross_margin_prev = gross_profit_prev / revenue_prev
        gross_margin_score = 1 if gross_margin > gross_margin_prev else 0

        avg_assets = (self.balance_sheet[self.years[0]]["TotalAssets"] + self.balance_sheet[self.years[1]][
            "TotalAssets"]) / 2
        avg_assets_prev = (self.balance_sheet[self.years[1]]["TotalAssets"] + self.balance_sheet[self.years[2]][
            "TotalAssets"]) / 2

        asset_turnover = revenue / avg_assets
        asset_turnover_prev = revenue_prev / avg_assets_prev
        asset_turnover_score = 1 if asset_turnover > asset_turnover_prev else 0

        operating_efficiency_score = gross_margin_score + asset_turnover_score

        return float(operating_efficiency_score)


def f_score(company_ticker: str, lock: Lock) -> float:
    logging.info(f"Evaluating f-score for {company_ticker}")
    fund = FundamentalAnalysis(company_ticker)
    score = fund.piotroski_f_score()
    logging.info(f"F-score for {company_ticker} is {score}")
    return score
