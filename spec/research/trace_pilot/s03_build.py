"""Weekly bond panel: spreads, M1, M2, M3 and forward targets, written to the work folder. T0 descriptives go to results.json."""
from __future__ import annotations

import json

import lib
import numpy as np
import pandas as pd
from posmon.indicators import taarss
from posmon.ledger import RemovalRule, build_ledger

FLOW_SETS = {"C": ("c",), "C_A": ("c", "a"), "C_A_T": ("c", "a", "t"), "C_dedupe_all": ("c_dd",), "C_dedupe_none": ("c_nd",)}
TENORS = {"DGS1MO": 1 / 12, "DGS3MO": 0.25, "DGS6MO": 0.5, "DGS1": 1, "DGS2": 2, "DGS3": 3, "DGS5": 5, "DGS7": 7, "DGS10": 10,
          "DGS20": 20, "DGS30": 30}


def curve() -> pd.DataFrame:
    out = {}
    for name in TENORS:
        table = pd.read_csv(lib.HERE / "raw" / "fred" / f"{name}.csv", parse_dates=["observation_date"], index_col="observation_date")
        out[name] = pd.to_numeric(table[name], errors="coerce")
    return pd.DataFrame(out).ffill(limit=3)


def add_spreads(daily: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    frame = daily.merge(reference[["cusip", "maturity_ts", "is_floater"]], on="cusip", how="left")
    frame["rem"] = (frame["maturity_ts"] - frame["date"]).dt.days / 365.25
    cmt = curve()
    tenors = np.array(list(TENORS.values()))
    rates = cmt.reindex(sorted(frame["date"].unique())).ffill()
    interp = np.full(len(frame), np.nan)
    for date, index in frame.groupby("date").indices.items():
        row = rates.loc[date].to_numpy()
        if np.isnan(row).any():
            continue
        interp[index] = np.interp(frame["rem"].to_numpy()[index], tenors, row)
    frame["cmt"] = interp
    for col, name in [("y_buy", "s_buy"), ("y_sell", "s_sell"), ("y_d", "s_d")]:
        frame[name] = (frame[col] - frame["cmt"]) * 100
    two_sided = (frame["s_buy"] + frame["s_sell"]) / 2
    frame["s_mid"] = two_sided.where(two_sided.notna(), frame["s_d"])
    frame["level_source"] = np.where(two_sided.notna(), "customer_two_sided", np.where(frame["s_d"].notna(), "dealer", "none"))
    return frame


def scale_table(frame: pd.DataFrame, reference: pd.DataFrame, calendar: pd.DatetimeIndex) -> dict:
    """Amount issued by date where the SEC gives one, otherwise the trailing volume fallback from plan.md."""
    gross = frame.pivot_table(index="date", columns="cusip", values="gross", aggfunc="sum").reindex(calendar).fillna(0.0)
    trailing = gross.rolling(130, min_periods=40).mean() * 5
    dev = gross.loc[:lib.DEV_END].mean() * 5
    ratios = []
    amounts = {}
    for row in reference.itertuples():
        values = json.loads(row.issue_amounts) if isinstance(row.issue_amounts, str) else []
        dates = pd.to_datetime(json.loads(row.issue_dates)) if isinstance(row.issue_dates, str) else []
        if len(values):
            series = pd.Series(values, index=dates).sort_index().cumsum()
            amounts[row.cusip] = series
            if dev.get(row.cusip, 0) > 0:
                ratios.append(series.iloc[-1] / dev[row.cusip])
    ratio = float(np.median(ratios)) if ratios else np.nan
    scale = trailing * ratio
    for cusip, series in amounts.items():
        if cusip in scale:
            scale[cusip] = series.reindex(calendar, method="ffill").fillna(series.iloc[0]).to_numpy()
    return {"scale": scale, "ratio": ratio, "has_sec": set(amounts)}


def mask_windows(net: pd.Series, dates: pd.DatetimeIndex, birth, reopen: list, calendar: pd.DatetimeIndex) -> pd.Series:
    out = net.copy()
    for start in ([birth] if birth is not None else []) + list(reopen):
        position = calendar.searchsorted(start)
        window = calendar[position:position + 5]
        out[out.index.isin(window)] = 0.0
    return out


def ledger_path(net: np.ndarray, entry: np.ndarray, level: np.ndarray) -> dict:
    """Incremental pro rata ledger. Same rule as posmon.build_ledger, with a check against it in main()."""
    n = len(net)
    entries, opens = np.zeros(n), np.zeros(n)
    count = 0
    share, depth, open_par, unmatched = np.full(n, np.nan), np.full(n, np.nan), np.zeros(n), np.zeros(n)
    miss = 0.0
    current = np.nan
    for i in range(n):
        value = net[i]
        if value > 0 and entry[i] == entry[i]:
            entries[count], opens[count] = entry[i], value
            count += 1
        elif value < 0:
            total = opens[:count].sum()
            taken = min(-value, total)
            miss += -value - taken
            if taken > 0:
                opens[:count] *= 1 - taken / total
        current = level[i] if level[i] == level[i] else current
        total = opens[:count].sum()
        open_par[i], unmatched[i] = total, miss
        if total > 0 and current == current:
            under = entries[:count] < current
            par = opens[:count][under].sum()
            share[i] = par / total
            depth[i] = (opens[:count][under] * (current - entries[:count][under])).sum() / par if par > 0 else 0.0
    return {"share": share, "depth": depth, "open": open_par, "unmatched": unmatched}


def main() -> None:
    daily = pd.read_parquet(lib.WORK / "daily.parquet")
    life = pd.read_parquet(lib.WORK / "bond_life.parquet")
    calendar = pd.DatetimeIndex(pd.read_parquet(lib.WORK / "calendar.parquet")["date"])
    reference = pd.read_csv(lib.HERE / "bond_reference.csv")
    reference["maturity_ts"] = pd.to_datetime(reference["maturity"], errors="coerce")
    reference["is_floater"] = reference["is_floater"].map({True: True, "True": True}).notna()
    frame = add_spreads(daily, reference)
    for col in ["c_buy", "c_sell", "c_dd_buy", "c_dd_sell", "c_nd_buy", "c_nd_sell", "a_buy", "a_sell", "t_buy", "t_sell"]:
        frame[col] = frame[col].fillna(0.0)
    frame["gross"] = frame["c_buy"] + frame["c_sell"]
    scales = scale_table(frame, reference, calendar)

    panel_start = calendar[5]
    birth = {c: (d if d > panel_start else None) for c, d in life["first_print"].items()}
    reopen = {}
    for row in reference.itertuples():
        dates = json.loads(row.issue_dates) if isinstance(row.issue_dates, str) else []
        reopen[row.cusip] = [pd.Timestamp(d) for d in dates if pd.Timestamp(d) >= calendar[0]]

    def weekly_for(flow_key: str, spread_col: str = "s_mid", mask: bool = True) -> pd.DataFrame:
        rows = []
        tag = FLOW_SETS[flow_key]
        for cusip, group in frame.groupby("cusip"):
            info = reference[reference.cusip == cusip]
            if info.empty or info["is_floater"].iloc[0] or pd.isna(info["maturity_ts"].iloc[0]):
                continue
            issuer = group["issuer"].iloc[0]
            if issuer not in lib.SPREAD_ISSUERS or cusip not in scales["scale"]:
                continue
            first, last = life.loc[cusip, "first_print"], life.loc[cusip, "last_print"]
            days = calendar[(calendar >= first) & (calendar <= last)]
            if len(days) < 30:
                continue
            g = group.set_index("date").reindex(days)
            net = sum(g[f"{t}_buy"].fillna(0.0) - g[f"{t}_sell"].fillna(0.0) for t in tag)
            if mask:
                net = mask_windows(net, days, birth.get(cusip), reopen.get(cusip, []), days)
            scale = scales["scale"][cusip].reindex(days)
            maturity = info["maturity_ts"].iloc[0]
            cum = net.cumsum()
            level = g[spread_col]
            week = days + pd.to_timedelta(4 - days.weekday, unit="D")
            table = pd.DataFrame({"level": level, "week": week, "day": np.arange(len(days))}, index=days)
            valid = table.dropna(subset=["level"])
            picks = valid.groupby("week").tail(1)
            week_last = pd.Series(days, index=week).groupby(level=0).max()
            ages = {w: days.get_loc(week_last[w]) - int(d) for w, d in zip(picks["week"], picks["day"])}
            picks = picks[[ages[w] <= 2 for w in picks["week"]]]
            if picks.empty:
                continue
            idx = picks["day"].to_numpy()  # position of the level day
            cum_values, scale_values = cum.to_numpy(), scale.to_numpy()
            prev = idx - 1  # last flow day allowed in a signal, one trading day before the level
            def window(n: int) -> np.ndarray:
                out = np.full(len(idx), np.nan)
                ok = prev - n >= 0
                out[ok] = (cum_values[prev[ok]] - cum_values[prev[ok] - n]) / scale_values[prev[ok]]
                return out
            rem = (maturity - picks.index).days / 365.25
            part = pd.DataFrame({"cusip": cusip, "issuer": issuer, "week": picks["week"].to_numpy(), "date": picks.index, "spread": picks["level"].to_numpy(),
                                 "rem": rem, "m1_4": window(20), "m1_13": window(65), "scale": scale_values[idx],
                                 "cum_at_level": cum_values[idx], "has_sec": cusip in scales["has_sec"]})
            # Later flow in scale units, for T3 and T4. Starts after the level day.
            part["cum_scaled"] = cum_values[idx] / scale_values[idx]
            part["cum_level"] = cum_values[idx]
            # M2: one value per calendar month, entered at the first level strictly after month-end.
            month_ends = pd.Series(days, index=days.to_period("M")).groupby(level=0).max()
            m2 = pd.Series(np.nan, index=part.index)
            for period, day_set in pd.Series(days, index=days.to_period("M")).groupby(level=0):
                flows = (net.loc[day_set.values]).to_numpy()
                traded = g.loc[day_set.values, "n_all"].notna().sum()
                base = scale.loc[day_set.values[-1]]
                if traded < 10 or not base > 0:
                    continue
                # Plan: enters at the first Friday after month-end, and the level must come after the month's last flow.
                month_end = pd.Timestamp(day_set.values[-1])
                friday = month_end + pd.Timedelta(days=(4 - month_end.weekday()) % 7 or 7)
                later = np.nonzero((part["week"].to_numpy() == np.datetime64(friday)) & (part["date"].to_numpy() > np.datetime64(month_end)))[0]
                if len(later) == 0:
                    continue
                m2.iloc[later[0]] = taarss(np.cumsum(flows) / base * 100)
            part["m2"] = m2.to_numpy()
            # M3 entry at the day's customer buy spread, and current spread at the prior flow day.
            buy = g["s_buy"].to_numpy()
            path = ledger_path(np.nan_to_num(net.to_numpy()), buy, g["s_mid"].to_numpy())
            part["pain_share"] = path["share"][prev]
            part["pain_depth"] = path["depth"][prev]
            part["ledger_open"] = path["open"][prev]
            part["ledger_unmatched"] = path["unmatched"][prev]
            rows.append(part)
        out = pd.concat(rows, ignore_index=True)
        out = out[out["rem"] >= 1].copy()
        out["bucket"] = pd.cut(out["rem"], lib.BUCKET_EDGES, labels=lib.BUCKET_NAMES, right=False).astype(str)
        return out.sort_values(["cusip", "week"]).reset_index(drop=True)

    outputs = {}
    outputs["C"] = weekly_for("C")
    for key in ["C_A", "C_A_T", "C_dedupe_all", "C_dedupe_none"]:
        outputs[key] = weekly_for(key)
    outputs["C_no_mask"] = weekly_for("C", mask=False)
    outputs["C_dealer_level"] = weekly_for("C", spread_col="s_d")
    for key, value in outputs.items():
        value.to_parquet(lib.WORK / f"weekly_{key}.parquet", index=False)

    # Ledger check: incremental path against posmon.build_ledger on 12 bonds, all days.
    rng = np.random.default_rng(lib.SEED)
    checked = []
    for cusip in rng.choice(outputs["C"]["cusip"].unique(), size=12, replace=False):
        days = calendar[(calendar >= life.loc[cusip, "first_print"]) & (calendar <= life.loc[cusip, "last_print"])]
        g = frame[frame.cusip == cusip].set_index("date").reindex(days)
        net = (g["c_buy"].fillna(0.0) - g["c_sell"].fillna(0.0)).to_numpy()
        buy = g["s_buy"].to_numpy()
        changes = np.where((net > 0) & np.isnan(buy), 0.0, net)
        reference_ledger = build_ledger(changes, np.nan_to_num(buy), RemovalRule.PRO_RATA, dates=list(days))
        path = ledger_path(net, buy, g["s_mid"].to_numpy())
        checked.append(abs(reference_ledger.open_total - path["open"][-1]) / max(reference_ledger.gross_total, 1.0))
    lib.save_part("ledger_check", {"bonds": 12, "max_relative_gap": float(max(checked))})

    # Reference and spread-level coverage.
    coverage = {
        "bonds_with_customer_trades": int(len(reference)),
        "with_maturity": int(reference["maturity"].notna().sum()),
        "floaters": int(reference["is_floater"].sum()),
        "with_sec_amount": int(reference["amount_outstanding_usd"].notna().sum()),
        "with_sec_amount_by_issuer": reference.dropna(subset=["amount_outstanding_usd"]).groupby("issuer").size().to_dict(),
        "bonds_by_issuer": reference.groupby("issuer").size().to_dict(),
        "sec_rule_counts": reference["rule"].value_counts().to_dict() if "rule" in reference else {},
        "fallback_ratio_amount_to_weekly_volume": scales["ratio"],
        "level_source_share": frame[frame["issuer"].isin(lib.SPREAD_ISSUERS)]["level_source"].value_counts(normalize=True).round(4).to_dict(),
        "panel_rows": int(len(outputs["C"])), "panel_bonds": int(outputs["C"]["cusip"].nunique()),
        "panel_weeks": int(outputs["C"]["week"].nunique()), "panel_issuers": int(outputs["C"]["issuer"].nunique()),
        "panel_rows_with_sec": int(outputs["C"]["has_sec"].sum()),
        "median_weeks_per_bond": float(outputs["C"].groupby("cusip").size().median()),
        "median_spread_bp": outputs["C"].groupby("issuer")["spread"].median().round(1).to_dict(),
    }
    lib.save_part("coverage", coverage)
    print(coverage)
    print("ledger check", max(checked))


if __name__ == "__main__":
    main()
