from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv


# =========================================================
# ENV
# =========================================================

load_dotenv()


KOREAEXIM_EXCHANGE_API_KEY = os.getenv(
    "KOREAEXIM_EXCHANGE_API_KEY",
    "",
).strip()


KOREAEXIM_INTEREST_API_KEY = os.getenv(
    "KOREAEXIM_INTEREST_API_KEY",
    "",
).strip()


# =========================================================
# CONFIG
# =========================================================

EXCHANGE_URL = (
    "https://oapi.koreaexim.go.kr/"
    "site/program/financial/exchangeJSON"
)


INTEREST_URL = (
    "https://oapi.koreaexim.go.kr/"
    "site/program/financial/interestJSON"
)


# =========================================================
# ERROR
# =========================================================

class MarketDataError(RuntimeError):
    pass


# =========================================================
# HELPERS
# =========================================================

def _num(value: Any) -> float:

    return float(
        str(value)
        .replace(",", "")
        .strip()
    )


def _date_candidates(
    start: datetime,
    days: int = 14,
):

    for i in range(days):

        yield (
            start
            - timedelta(days=i)
        )


def _get_json(
    url: str,
    *,
    params=None,
    headers=None,
    timeout: int = 15,
):

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


def _field(
    row: Dict[str, Any],
    *names: str,
) -> Any:
    """
    수출입은행 응답이 소문자/대문자 어느 쪽으로 와도
    읽을 수 있도록 처리.
    """

    for name in names:

        if name in row:
            return row[name]

    return None


# =========================================================
# EXCHANGE API
# AP01
# =========================================================

def _exim_rates_for_date(
    dt: datetime,
    api_key: str,
) -> Optional[Dict[str, float]]:

    data = _get_json(
        EXCHANGE_URL,
        params={
            "authkey": api_key,
            "searchdate": dt.strftime("%Y%m%d"),
            "data": "AP01",
        },
    )

    if not isinstance(data, list):
        return None

    if not data:
        return None


    result: Dict[str, float] = {}


    for row in data:

        unit = str(
            _field(
                row,
                "cur_unit",
                "CUR_UNIT",
            )
            or ""
        ).strip()


        rate = _field(
            row,
            "deal_bas_r",
            "DEAL_BAS_R",
        )


        if rate in (
            None,
            "",
        ):
            continue


        # -----------------------------------------
        # USD
        # -----------------------------------------

        if unit == "USD":

            result["USD/KRW"] = (
                _num(rate)
            )


        # -----------------------------------------
        # JPY
        #
        # 한국수출입은행 JPY(100)는
        # 100엔 기준이므로 1엔 기준으로 변환
        # -----------------------------------------

        elif unit.startswith("JPY"):

            jpy_rate = (
                _num(rate)
            )

            if "100" in unit:

                jpy_rate /= 100.0

            result[
                "JPY/KRW"
            ] = jpy_rate


        # -----------------------------------------
        # EUR
        # -----------------------------------------

        elif unit == "EUR":

            result["EUR/KRW"] = (
                _num(rate)
            )


    required = {
        "USD/KRW",
        "JPY/KRW",
        "EUR/KRW",
    }


    if not required.issubset(
        result
    ):
        return None


    return result


# =========================================================
# FIND TWO RECENT FX DAYS
# =========================================================

def _latest_two_exchange_days(
    start: datetime,
    api_key: str,
):

    found = []


    for dt in _date_candidates(
        start,
        days=14,
    ):

        rates = (
            _exim_rates_for_date(
                dt,
                api_key,
            )
        )


        if rates:

            found.append(
                (
                    dt,
                    rates,
                )
            )


        if len(found) == 2:

            return found


    raise MarketDataError(
        "최근 수출입은행 환율 데이터 "
        "2개 영업일을 찾지 못했습니다."
    )


# =========================================================
# FETCH FX
# =========================================================

def fetch_fx(
    start: datetime,
    api_key: str,
) -> Dict[str, Dict[str, Any]]:

    (
        (
            latest_dt,
            latest,
        ),
        (
            prev_dt,
            prev,
        ),
    ) = _latest_two_exchange_days(
        start,
        api_key,
    )


    result: Dict[
        str,
        Dict[str, Any],
    ] = {}


    for name in (
        "USD/KRW",
        "JPY/KRW",
        "EUR/KRW",
    ):

        current_value = (
            latest[name]
        )

        previous_value = (
            prev[name]
        )


        if previous_value:

            change_pct = (
                (
                    current_value
                    - previous_value
                )
                / previous_value
                * 100
            )

        else:

            change_pct = 0.0


        result[name] = {

            "value":
                current_value,

            "change_pct":
                change_pct,

            "source_date":
                latest_dt.strftime(
                    "%Y-%m-%d"
                ),

            "previous_date":
                prev_dt.strftime(
                    "%Y-%m-%d"
                ),
        }


    return result


# =========================================================
# INTEREST API
# AP02 — LOAN RATE
# =========================================================

def _exim_loan_rates_for_date(
    dt: datetime,
    api_key: str,
) -> Optional[list[Dict[str, Any]]]:

    data = _get_json(
        INTEREST_URL,
        params={
            "authkey": api_key,
            "searchdate": dt.strftime(
                "%Y%m%d"
            ),
            "data": "AP02",
        },
    )


    if not isinstance(
        data,
        list,
    ):
        return None


    if not data:
        return None


    result: list[
        Dict[str, Any]
    ] = []


    for row in data:

        name = str(
            _field(
                row,
                "sfln_intrc_nm",
                "SFLN_INTRC_NM",
            )
            or ""
        ).strip()


        rate_raw = _field(
            row,
            "int_r",
            "INT_R",
        )


        if (
            not name
            or rate_raw in (
                None,
                "",
            )
        ):
            continue


        try:

            rate = _num(
                rate_raw
            )

        except (
            TypeError,
            ValueError,
        ):
            continue


        result.append(
            {
                "name":
                    name,

                "value":
                    rate,
            }
        )


    return (
        result
        or None
    )


# =========================================================
# FETCH LATEST LOAN RATE
# =========================================================

def fetch_latest_loan_rates(
    start: datetime,
    api_key: str,
) -> Dict[str, Any]:

    for dt in _date_candidates(
        start,
        days=14,
    ):

        rates = (
            _exim_loan_rates_for_date(
                dt,
                api_key,
            )
        )


        if rates:

            return {

                "source_date":
                    dt.strftime(
                        "%Y-%m-%d"
                    ),

                "items":
                    rates,
            }


    raise MarketDataError(
        "최근 수출입은행 대출금리 "
        "데이터를 찾지 못했습니다."
    )


# =========================================================
# FETCH ALL
# =========================================================

def fetch_all(
    start: Optional[
        datetime
    ] = None,
) -> Dict[str, Any]:

    # -----------------------------------------
    # Check keys
    # -----------------------------------------

    if not KOREAEXIM_EXCHANGE_API_KEY:

        raise MarketDataError(
            "KOREAEXIM_EXCHANGE_API_KEY가 없습니다. "
            ".env 파일을 확인해주세요."
        )


    if not KOREAEXIM_INTEREST_API_KEY:

        raise MarketDataError(
            "KOREAEXIM_INTEREST_API_KEY가 없습니다. "
            ".env 파일을 확인해주세요."
        )


    # -----------------------------------------
    # Time
    # -----------------------------------------

    start = (
        start
        or datetime.now(
            ZoneInfo(
                "Asia/Seoul"
            )
        )
    )


    # -----------------------------------------
    # FX
    # -----------------------------------------

    fx = fetch_fx(
        start,
        KOREAEXIM_EXCHANGE_API_KEY,
    )


    # -----------------------------------------
    # LOAN RATE
    # -----------------------------------------

    loan_rates = (
        fetch_latest_loan_rates(
            start,
            KOREAEXIM_INTEREST_API_KEY,
        )
    )


    # -----------------------------------------
    # Result
    # -----------------------------------------

    return {

        "as_of":
            start.strftime(
                "%Y.%m.%d %H:%M KST"
            ),

        "items":
            fx,

        "loan_rates":
            loan_rates,

        "sources": {

            "FX":
                "한국수출입은행",

            "LOAN":
                "한국수출입은행",
        },
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    data = fetch_all()

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
    )