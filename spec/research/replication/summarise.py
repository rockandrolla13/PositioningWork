"""Collect every sub-result into results.json, with the verdicts and the numbers that justify them."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    i4, ten, opi = load("i4_results.json"), load("i4_tenyear.json"), load("i4_opi_bands.json")
    i4_total = i4["grid_rates_total"] + i4["uncond_variants"] + i4["shape_variants"] + i4["rolling_variants"] + i4["pinned_grid_size"] + ten["variants"] + opi["variants"]
    i7, vol21 = load("i7_results.json"), load("i7_vol21.json")
    rows = pd.DataFrame(i7["rows"])
    base = rows[(rows.variant == "total")].set_index(["kind", "window"])
    i6, band, ger, reb = load("i6_results.json"), load("i6_bands.json"), load("i6_germany.json"), load("i6_rebuild.json")
    p2 = pd.DataFrame(load("p2_results.json")["rows"])
    i10, i8, p1 = load("i10_results.json"), load("i8_results.json"), load("p1_results.json")
    expanding = [r for r in band["half_width_longer"] if r["scale"] == "expanding_sd"][0]
    p2_best = p2.sort_values("inside_band", ascending=False).iloc[0].to_dict()
    best_share = p2[p2.formula.str.startswith("share")].sort_values("inside_band", ascending=False).iloc[0].to_dict()
    table8 = pd.DataFrame(i8["table"])
    table8 = table8[table8.date == "2023-10-30"].set_index("form")
    out = {
        "P1": {"verdict": "Specified", "evidence": {"numeric_tokens_in_note": p1["numeric_tokens"], "reason": "The one page holds only its date, the 30-day window and list numbers. It prints no output."}},
        "P2": {"verdict": "Specified", "evidence": {"reason": "The deck's line is the legacy survival share, so no source output exists for the corrected formula.", "best_share_formula_inside_band": best_share["inside_band"], "best_share_formula_last": best_share["last"]}},
        "P3_extra": {"verdict": "Verified", "evidence": {"deck_line_recipe": {k: p2_best[k] for k in ("basis", "window", "formula", "inside_band", "corr_point", "last")}, "printed_readout": 1.00, "variants": len(p2)}},
        "I4": {"verdict": "Partial", "evidence": {"variants_total": i4_total, "chart_range": i4["chart_range_ex1"], "tuesday_dgs10_range": i4["tuesday_dgs10_range_2009_06"], "base_rate": i4["base_rate_pinned"], "uncond_best": i4["uncond_k1_best"],
                                                   "uncond_by_sampling": i4["best_uncond_by_dow"], "rate_matches_within_1pt": i4["grid_rates_within_1pt"], "rate_matches_within_2pt_and_range": i4["grid_rates_within_2pt_and_range_ok"],
                                                   "best_in_pinned_sample": i4["pinned_best"], "best_cond_rmse": min(i4["best_cond_rmse_full_sample"], i4["best_cond_rmse_rolling"], opi["best_shape"][0]["rm_cond"])}},
        "I6": {"verdict": "Partial", "evidence": {"centre_ex3": band["centre"][0], "half_width_ex3": expanding, "ex4_unfitted": {"k_fit": ger["expanding_k_fit"], "printed_k": ger["printed_k"], "corr": ger["corr_half_width"], "centre_h63_corr": [r for r in ger["centre"] if r["h"] == 63][0]["corr"]},
                                                   "band_rebuild": reb["band_match"][0], "stats_best": band["stats_best"][0], "stats_variants": band["stats_variants"], "printed": reb["printed"], "december_rebuilt": [reb["december_first"], reb["december_last"]], "december_printed": reb["printed_december"],
                                                   "cftc_proxy_best_abs_corr": max(abs(r["corr"]) for r in i6["proxy_rows"]), "cftc_proxy_variants": len(i6["proxy_rows"]), "strike_level_data_on_machine": False}},
        "I7": {"verdict": {"continuation_time_series": "Partial", "continuation_cross_section": "Partial", "reversal": "Partial", "coffee": "Specified"},
               "evidence": {"date_map": i7["date_map"], "chart_stats": i7["chart_stats"], "base_1W": base.xs("1W", level="window")[["corr_w", "corr_m", "corr_q", "sharpe_1999", "vol_1999", "turn_week_pct", "printed_turn"]].to_dict("index"), "halves": i7["halves"], "ts_vol21": vol21["rows"], "variants": len(rows) + len(vol21["rows"])}},
        "I8": {"verdict": "Partial", "evidence": {"printed": i8["printed"], "mean_response": table8.loc["mean_response"].to_dict(), "sum_response": table8.loc["sum_response"].to_dict(), "variants": i8["variants"], "tick_data_2023_on_machine": False}},
        "I9": {"verdict": "Not reproducible", "evidence": {"reason": "CitiFX flows are private, CPAIN is undefined, and the weights are hidden."}},
        "I10": {"verdict": "Partial", "evidence": {"exhibit2_cells": i10["exhibit2_cells"], "live": i10["exhibit2_live"], "live_inside_band": i10["exhibit2_live_inside_band"], "live_no_partner": i10["exhibit2_live_no_partner"], "carry_range": [min(r["carry"] for r in i10["carry_variants"]), max(r["carry"] for r in i10["carry_variants"])], "carry_printed": 5.4, "momentum": i10["momentum"], "momentum_printed": -4.6, "ust_line_corr_all": i10["exhibit2_corr_all"]["public_mean"], "ust_line_corr_live": i10["exhibit2_corr_live"]["public_mean"]}},
        "I11": {"verdict": "Specified", "evidence": {"reason": "Stan, NumPyro, JAX and PyMC are not installed, so the sampler did not run."}},
    }
    (HERE / "results.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: v["verdict"] for k, v in out.items()}, indent=1))
    print("I4 total variants", i4_total)


if __name__ == "__main__":
    main()
