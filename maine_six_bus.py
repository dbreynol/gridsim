"""Synthetic six-bus DC-OPF with observed Maine nodal load profiles (2025–2026).

Install: uv add pypsa highspy pandas numpy scipy
Input: maine_selected_6_nodes_202501_202609.csv in the working directory.
"""
import numpy as np
import pandas as pd
import pypsa
from scipy.signal import lfilter

# 1. Historical loads; resolve the repeated November hour, then use UTC snapshots.
df = pd.read_csv("maine_selected_6_nodes_202501_202609.csv")
local = pd.to_datetime(df.Date) + pd.to_timedelta(df.Hour_Ending - 1, unit="h")
utc = (local.dt.tz_localize("America/New_York", ambiguous=df.Hour_Occurrence.eq(1).to_numpy())
       .dt.tz_convert("UTC").dt.tz_localize(None))
load = df.filter(like="_MW_Factor").copy()
load.columns = ["Spring", "Topsham", "Gulf", "Raymond", "Trenton", "Chester"]
load.index = pd.DatetimeIndex(utc)
load = load.dropna().sort_index()   # No imputation of missing nodal weights

# 2. Size installed capacity using 2025 only (avoid calibration on 2026 test data).
train = load.loc[load.index < pd.Timestamp("2026-01-01 05:00")]
N = train[["Chester", "Trenton", "Gulf"]].sum(axis=1).quantile(0.95)
S = train[["Spring", "Topsham", "Raymond"]].sum(axis=1).quantile(0.95)
up5 = lambda x: float(5 * np.ceil(x / 5))
gens = {  # name: (bus, installed MW, marginal $/MWh)
    "wind":    ("Chester", up5(.80*N), 0),
    "hydro":   ("Gulf",    up5(.65*N), 12),
    "thermal": ("Trenton", up5(1.15*N), 28),
    "ccgt":    ("Spring",  up5(1.00*S), 65),
    "peaker":  ("Topsham", up5(.60*S), 100),
    "backup":  ("Raymond", up5(.45*S), 180),
}

# 3. Build an intentionally synthetic, meshed 115-kV network.
n = pypsa.Network()
n.set_snapshots(load.index)
for bus in load:
    n.add("Bus", bus, v_nom=115)
    n.add("Load", f"load_{bus}", bus=bus, p_set=load[bus])
for name, (bus, mw, cost) in gens.items():
    n.add("Generator", name, bus=bus, p_nom=mw, marginal_cost=cost)

# Correlated synthetic wind availability, pending observed wind profiles.
noise = np.random.default_rng(7).normal(size=len(load))
wind_cf = np.clip(.43 + .22*lfilter([np.sqrt(1-.95**2)], [1, -.95], noise), .03, .95)
n.generators_t.p_max_pu["wind"] = wind_cf

# Lines: bus0, bus1, reactance in ohms, thermal rating in MVA.
lines = [
    ("Chester", "Trenton", 13, up5(.70*gens["wind"][1])),
    ("Chester", "Gulf",    18, up5(.55*gens["wind"][1])),
    ("Trenton", "Gulf",     9, up5(1.20*N)),
    ("Trenton", "Topsham", 15, up5(.33*S)), # northern/southern tie
    ("Gulf", "Spring",    18, up5(.26*S)), # second tie
    ("Spring", "Topsham",  9, up5(.60*S)),
    ("Spring", "Raymond", 12, up5(.13*S)), # local bottleneck
    ("Topsham", "Raymond",14, up5(.13*S)),
]
for a, b, x, rating in lines:
    n.add("Line", f"{a}-{b}", bus0=a, bus1=b, x=x, r=0, s_nom=rating)

# 4. Smoke test: one January week and one July week, then save network.
hours = n.snapshots[(n.snapshots.year == 2025) &
                    (n.snapshots.month.isin([1, 7])) & (n.snapshots.day <= 7)]
status, condition = n.optimize(snapshots=hours, solver_name="highs")
print("Optimization:", status, condition)
print("Generator MW:\n", n.generators[["bus", "p_nom", "marginal_cost"]])
print("Line ratings (MVA):\n", n.lines["s_nom"])
if status == "ok":
    spread = n.buses_t.marginal_price.loc[hours, "Topsham"] - n.buses_t.marginal_price.loc[hours, "Chester"]
    binding = n.lines_t.p0.loc[hours].abs().ge(n.lines.s_nom - 1e-3).any(axis=1)
    print(f"Mean Topsham–Chester LMP spread: ${spread.mean():.1f}/MWh")
    print(f"Hours with at least one binding line: {binding.mean():.1%}")
n.export_to_netcdf("maine_six_bus.nc")
