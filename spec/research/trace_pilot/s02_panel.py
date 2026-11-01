"""Bond-day aggregates from marketdb, written to the work folder, plus the sign proof and cleaning counts as statistics."""
from __future__ import annotations

import lib
import marketdb
import numpy as np
import pandas as pd
from scipy import stats as sps

MAX_SIZE = 250e6
DUP_MIN = 1e6


def load() -> pd.DataFrame:
    con = marketdb.connect()
    frame = con.sql("""SELECT cusip, company_symbol AS issuer, trd_exctn_dt AS date, trd_exctn_ts AS ts, rptd_pr AS price,
        TRY_CAST(yld_pt AS DOUBLE) AS yld, entrd_vol_qt AS qty, rpt_side_cd AS side, cntra_mp_id AS contra, trd_rpt_dt AS rpt
        FROM trace WHERE company_symbol IS NOT NULL AND company_symbol <> 'JPM'""").df()
    frame["date"] = pd.to_datetime(frame["date"])
    return frame


def duplicates(frame: pd.DataFrame) -> pd.Series:
    return frame.duplicated(["cusip", "ts", "price", "yld", "qty", "side", "contra", "rpt"], keep="first")


def clean_yields(frame: pd.DataFrame) -> pd.Series:
    """Yield kept where it is in range and within 200 bp of the bond's centred 11-day median."""
    usable = frame["yld"].where(frame["yld"].between(0.1, 40))
    daily = usable.groupby([frame["cusip"], frame["date"]]).median().rename("day_med").reset_index().sort_values(["cusip", "date"])
    daily["med11"] = daily.groupby("cusip")["day_med"].transform(lambda s: s.rolling(11, center=True, min_periods=3).median())
    merged = frame[["cusip", "date"]].merge(daily[["cusip", "date", "med11"]], on=["cusip", "date"], how="left")
    keep = (usable.to_numpy() - merged["med11"].to_numpy())
    good = np.abs(keep) <= 2.0
    return pd.Series(np.where(good, usable.to_numpy(), np.nan), index=frame.index)


def vw(frame: pd.DataFrame, value: str, key: list) -> pd.Series:
    data = frame.dropna(subset=[value])
    return (data[value] * data["qty"]).groupby([data[k] for k in key]).sum() / data["qty"].groupby([data[k] for k in key]).sum()


def sign_proof(frame: pd.DataFrame) -> dict:
    """On bond-days with both sides, reporter sale minus reporter buy, for price and yield, by contra type."""
    out = {}
    for contra in ["C", "A", "T", "D"]:
        data = frame[frame["contra"] == contra]
        px = vw(data, "price", ["cusip", "date", "side"]).unstack("side")
        yd = vw(data, "yld_clean", ["cusip", "date", "side"]).unstack("side")
        gap = (px["S"] - px["B"]).dropna()
        ygap = (yd["S"] - yd["B"]).dropna() * 100
        issuer = data.groupby("cusip")["issuer"].first()
        by_issuer = gap.groupby(gap.index.get_level_values("cusip").map(issuer)).mean()
        y_by_issuer = ygap.groupby(ygap.index.get_level_values("cusip").map(issuer)).mean()
        # Issuer means are the unit of evidence: t-test across issuers, not across bond-days.
        t_issuer = float(by_issuer.mean() / (by_issuer.std() / np.sqrt(len(by_issuer))))
        out[contra] = {"bond_days": int(len(gap)), "price_gap_mean": float(gap.mean()), "price_gap_median": float(gap.median()),
                       "share_price_gap_pos": float((gap > 0).mean()), "yield_gap_mean_bp": float(ygap.mean()),
                       "yield_gap_median_bp": float(ygap.median()), "share_yield_gap_neg": float((ygap < 0).mean()),
                       "issuers_price_gap_pos": int((by_issuer > 0).sum()), "issuers": int(len(by_issuer)),
                       "t_across_issuers": t_issuer, "by_issuer_price_gap": by_issuer.round(4).to_dict(),
                       "by_issuer_yield_gap_bp": y_by_issuer.round(2).to_dict()}
    # Size split for C: small tickets should show the widest gap, since retail pays more.
    data = frame[frame["contra"] == "C"]
    split = {}
    for name, low, high in [("under_100k", 0, 1e5), ("100k_1m", 1e5, 1e6), ("1m_plus", 1e6, 1e12)]:
        part = data[(data["qty"] >= low) & (data["qty"] < high)]
        px = vw(part, "price", ["cusip", "date", "side"]).unstack("side")
        gap = (px["S"] - px["B"]).dropna()
        split[name] = {"bond_days": int(len(gap)), "price_gap_mean": float(gap.mean()), "share_pos": float((gap > 0).mean())}
    out["C_by_size"] = split
    return out


def main() -> None:
    raw = load()
    stats = {"rows_raw": int(len(raw))}
    stats["rows_by_contra"] = raw["contra"].value_counts().to_dict()
    stats["par_bn_by_contra"] = (raw.groupby("contra")["qty"].sum() / 1e9).round(1).to_dict()
    stats["yield_null_share_by_issuer_C"] = raw[raw.contra == "C"].groupby("issuer")["yld"].apply(lambda s: float(s.isna().mean())).round(4).to_dict()
    stats["asof_share_C"] = float((pd.to_datetime(raw[raw.contra == "C"]["rpt"]) != raw[raw.contra == "C"]["date"]).mean())

    bad_price = ~raw["price"].between(1.000001, 300)
    stats["drop_price_rows"] = int(bad_price.sum())
    frame = raw[~bad_price].copy()
    dup = duplicates(frame)
    stats["dup_rows_by_contra"] = frame[dup]["contra"].value_counts().to_dict()
    stats["dup_par_bn_by_contra"] = (frame[dup].groupby("contra")["qty"].sum() / 1e9).round(2).to_dict()
    too_big = frame["qty"] > MAX_SIZE
    stats["drop_oversize_rows_by_contra"] = frame[too_big]["contra"].value_counts().to_dict()
    stats["drop_oversize_par_bn_by_contra"] = (frame[too_big].groupby("contra")["qty"].sum() / 1e9).round(1).to_dict()
    stats["oversize_C_side_counts"] = frame[too_big & (frame.contra == "C")]["side"].value_counts().to_dict()
    frame["dup"] = dup
    frame = frame[~too_big].copy()
    frame["yld_clean"] = clean_yields(frame)
    usable = frame["yld"].between(0.1, 40)
    stats["yield_outlier_share_C"] = float((frame["yld_clean"].isna() & usable)[frame.contra == "C"].sum() / usable[frame.contra == "C"].sum())
    stats["yield_out_of_range_share_C"] = float(((~usable) & frame["yld"].notna())[frame.contra == "C"].mean())

    # Sign proof uses the primary dedupe rule.
    primary = frame[~(frame["dup"] & (frame["qty"] >= DUP_MIN))]
    lib.save_part("cleaning", stats)
    lib.save_part("sign_proof", sign_proof(primary))

    def net(data: pd.DataFrame, name: str) -> pd.DataFrame:
        table = data.groupby(["cusip", "date", "side"])["qty"].sum().unstack("side").reindex(columns=["S", "B"]).fillna(0.0)
        return table.rename(columns={"S": f"{name}_buy", "B": f"{name}_sell"})

    parts = [net(primary[primary.contra == "C"], "c"),
             net(frame[(frame.contra == "C") & ~frame["dup"]], "c_dd"),
             net(frame[frame.contra == "C"], "c_nd"),
             net(primary[primary.contra == "A"], "a"),
             net(primary[primary.contra == "T"], "t")]
    daily = pd.concat(parts, axis=1).fillna(0.0)
    customer = primary[primary.contra == "C"]
    yields = vw(customer, "yld_clean", ["cusip", "date", "side"]).unstack("side").reindex(columns=["S", "B"])
    daily["y_buy"] = yields["S"]
    daily["y_sell"] = yields["B"]
    dealer = primary[(primary.contra == "D") & (primary.side == "S")]
    daily = daily.join(vw(dealer, "yld_clean", ["cusip", "date"]).rename("y_d"), how="outer")
    all_trades = primary.groupby(["cusip", "date"]).agg(n_all=("qty", "size"))
    daily = daily.join(all_trades, how="outer").reset_index()
    daily["issuer"] = daily["cusip"].map(raw.groupby("cusip")["issuer"].first())
    # Largest-print evidence for the par assumption: largest trade in each bond's life, to compare with SEC tranche size.
    largest = raw.groupby("cusip")["qty"].max().rename("max_qty")
    first_print = raw.groupby("cusip")["date"].min().rename("first_print")
    last_print = raw.groupby("cusip")["date"].max().rename("last_print")
    trading_days = pd.DatetimeIndex(sorted(raw["date"].unique()))
    pd.concat([largest, first_print, last_print], axis=1).to_parquet(lib.WORK / "bond_life.parquet")
    pd.Series(trading_days).to_frame("date").to_parquet(lib.WORK / "calendar.parquet")
    daily.to_parquet(lib.WORK / "daily.parquet", index=False)
    print(stats)


if __name__ == "__main__":
    main()
