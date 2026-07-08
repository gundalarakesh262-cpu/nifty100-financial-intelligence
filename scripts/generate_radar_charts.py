import math
from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parent.parent
sqlite_path = base / 'output' / 'peer_percentiles.sqlite'
out_dir = base / 'reports' / 'radar_charts'
out_dir.mkdir(parents=True, exist_ok=True)

if not sqlite_path.exists():
    print('Missing', sqlite_path)
    raise SystemExit(1)

conn = sqlite3.connect(str(sqlite_path))
df = pd.read_sql('SELECT * FROM peer_percentiles', conn)
conn.close()

# metrics to plot: peer_score_* and peer_composite_score
metric_cols = [c for c in df.columns if c.startswith('peer_score_')]
if 'peer_composite_score' in df.columns:
    metric_cols.append('peer_composite_score')

# normalize columns to numeric
for c in metric_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(50)

peer_groups = df['peer_group_name'].fillna('ungrouped').unique()

def radar_plot(df_plot, labels, title, path):
    N = len(labels)
    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1]

    plt.figure(figsize=(6,6))
    ax = plt.subplot(111, polar=True)
    plt.xticks(angles[:-1], labels, color='grey', size=8)
    ax.set_rlabel_position(30)
    plt.yticks([20,40,60,80], ["20","40","60","80"], color="grey", size=7)
    plt.ylim(0,100)

    for _, row in df_plot.iterrows():
        values = row[labels].tolist()
        values = [float(v) for v in values]
        values += values[:1]
        ax.plot(angles, values, linewidth=1, linestyle='solid', label=row.get('company_name', row.get('company_id')))
        ax.fill(angles, values, alpha=0.1)

    plt.title(title, size=10, y=1.08)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize='small')
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

# For each peer group, plot top 5 companies by peer_composite_score
for grp in peer_groups:
    grp_name = grp if grp is not None else 'ungrouped'
    grp_df = df[df['peer_group_name'].fillna('ungrouped') == grp_name].copy()
    if grp_df.empty:
        continue
    # deduplicate by company_id to avoid repeated charts; keep highest composite score
    if 'company_id' in grp_df.columns:
        grp_df = grp_df.sort_values(by='peer_composite_score', ascending=False).drop_duplicates(subset=['company_id'], keep='first')
    grp_df = grp_df.sort_values(by='peer_composite_score', ascending=False).head(5)
    labels = metric_cols
    # ensure labels exist in dataframe
    labels = [l for l in labels if l in grp_df.columns]
    title = f"{grp_name} - Top {len(grp_df)}"
    safe = str(grp_name)[:40].replace('/', '_')
    out_path = out_dir / f"radar_{safe}.png"
    radar_plot(grp_df, labels, title, out_path)
    print('Wrote', out_path)

# standalone charts for ungrouped companies (limit 20 by composite score)
ungrouped = df[df['peer_group_name'].isna()].copy()
if not ungrouped.empty:
    ungrouped['peer_composite_score'] = pd.to_numeric(ungrouped['peer_composite_score'], errors='coerce').fillna(0)
    if 'company_id' in ungrouped.columns:
        ungrouped = ungrouped.sort_values(by='peer_composite_score', ascending=False).drop_duplicates(subset=['company_id'], keep='first')
    ungrouped = ungrouped.sort_values(by='peer_composite_score', ascending=False).head(20)
    for _, row in ungrouped.iterrows():
        comp_df = pd.DataFrame([row])
        company_id = row.get('company_id') or ''
        name = row.get('company_name') or company_id
        safe = f"{company_id}_{str(name)[:40]}".replace('/', '_').replace(' ', '_')
        out_path = out_dir / f"radar_ungrouped_{safe}.png"
        radar_plot(comp_df, metric_cols, str(name), out_path)
        print('Wrote', out_path)

print('Radar charts generated in', out_dir)
