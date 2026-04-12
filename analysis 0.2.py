"""
SalesPulse Pro — End-to-End Sales Analytics Dashboard
Dataset : Superstore Sales (Kaggle)
Author  : Your Name
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ── Color palette ──────────────────────────────────────────────────────────
BG       = '#0F1117'
CARD     = '#1A1D27'
ACCENT   = '#4F7EF7'
TEAL     = '#2DD4BF'
AMBER    = '#F59E0B'
ROSE     = '#FB7185'
PURPLE   = '#A78BFA'
GREEN    = '#34D399'
PALETTE  = [ACCENT, TEAL, AMBER, ROSE, PURPLE, GREEN, '#F472B6', '#60A5FA']

plt.rcParams.update({
    'figure.facecolor': BG,  'axes.facecolor': CARD,
    'axes.edgecolor':  '#2E3347', 'axes.labelcolor': '#C8CDD8',
    'xtick.color':     '#7A8099', 'ytick.color':     '#7A8099',
    'text.color':      '#E8EAF0', 'grid.color':      '#2E3347',
    'grid.linewidth':  0.6,       'font.family':      'DejaVu Sans',
    'axes.spines.top': False,     'axes.spines.right':False,
})

# ══════════════════════════════════════════════════════════════════════════
# 1. LOAD DATA
# ══════════════════════════════════════════════════════════════════════════
print("=" * 62)
print("  SalesPulse Pro — Loading Data")
print("=" * 62)

df = pd.read_csv("data 0.2/superstore.csv", encoding='latin-1')
print(f"  Raw shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

# ══════════════════════════════════════════════════════════════════════════
# 2. DATA CLEANING
# ══════════════════════════════════════════════════════════════════════════
print("\n  Cleaning...")

# ── 2a. Column names: strip spaces, lowercase, replace spaces with _
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

# ── 2b. Parse dates
df['order_date']  = pd.to_datetime(df['order_date'],  dayfirst=False)
df['ship_date']   = pd.to_datetime(df['ship_date'],   dayfirst=False)

# ── 2c. Drop duplicates
before = len(df)
df.drop_duplicates(subset='order_id', keep='first', inplace=True)
print(f"  Duplicates removed : {before - len(df)}")

# ── 2d. Handle missing values
print(f"  Missing values     : {df.isnull().sum().sum()}")
df.dropna(subset=['sales', 'profit'], inplace=True)

# ── 2e. Fix data types
df['sales']    = pd.to_numeric(df['sales'],    errors='coerce')
df['profit']   = pd.to_numeric(df['profit'],   errors='coerce')
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df['discount'] = pd.to_numeric(df['discount'], errors='coerce')

# ── 2f. Remove negative / zero sales (bad records)
df = df[df['sales'] > 0].copy()

# ══════════════════════════════════════════════════════════════════════════
# 3. FEATURE ENGINEERING  (calculated columns)
# ══════════════════════════════════════════════════════════════════════════
print("\n  Engineering features...")

df['profit_margin']  = (df['profit'] / df['sales'] * 100).round(2)
df['revenue_per_qty']= (df['sales']  / df['quantity']).round(2)
df['order_year']     = df['order_date'].dt.year
df['order_month']    = df['order_date'].dt.month
df['order_month_name']= df['order_date'].dt.strftime('%b')
df['order_quarter']  = df['order_date'].dt.quarter.map(
                        {1:'Q1',2:'Q2',3:'Q3',4:'Q4'})
df['ship_days']      = (df['ship_date'] - df['order_date']).dt.days
df['is_profitable']  = (df['profit'] > 0).astype(int)
df['discount_band']  = pd.cut(df['discount'],
                        bins=[-0.01, 0, 0.2, 0.4, 1.0],
                        labels=['No Discount','Low','Medium','High'])

print(f"  Final dataset      : {df.shape[0]:,} rows × {df.shape[1]} cols")

# ══════════════════════════════════════════════════════════════════════════
# 4. KPI CALCULATIONS
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 62)
print("  KEY PERFORMANCE INDICATORS")
print("=" * 62)

total_sales     = df['sales'].sum()
total_profit    = df['profit'].sum()
total_orders    = df['order_id'].nunique()
total_customers = df['customer_id'].nunique()
avg_margin      = df['profit_margin'].mean()
avg_ship_days   = df['ship_days'].mean()
total_qty       = df['quantity'].sum()

kpis = {
    'Total Sales'       : f"${total_sales:,.0f}",
    'Total Profit'      : f"${total_profit:,.0f}",
    'Total Orders'      : f"{total_orders:,}",
    'Unique Customers'  : f"{total_customers:,}",
    'Avg Profit Margin' : f"{avg_margin:.1f}%",
    'Avg Ship Days'     : f"{avg_ship_days:.1f}",
    'Units Sold'        : f"{total_qty:,}",
}
for k, v in kpis.items():
    print(f"  {k:<22} {v}")

# ══════════════════════════════════════════════════════════════════════════
# 5. ANALYSIS TABLES  (exported for Power BI + SQL)
# ══════════════════════════════════════════════════════════════════════════

# Monthly sales trend
monthly = (df.groupby(['order_year','order_month','order_month_name'])
             .agg(sales=('sales','sum'), profit=('profit','sum'),
                  orders=('order_id','nunique'))
             .reset_index()
             .sort_values(['order_year','order_month']))
monthly['profit_margin'] = (monthly['profit'] / monthly['sales'] * 100).round(2)
monthly['period'] = monthly['order_month_name'] + ' ' + monthly['order_year'].astype(str)

# Category + sub-category
cat_perf = (df.groupby(['category','sub-category'])
              .agg(sales=('sales','sum'), profit=('profit','sum'),
                   orders=('order_id','nunique'), qty=('quantity','sum'))
              .reset_index())
cat_perf['profit_margin'] = (cat_perf['profit'] / cat_perf['sales'] * 100).round(2)
cat_perf.sort_values('sales', ascending=False, inplace=True)

# Region performance
region = (df.groupby('region')
            .agg(sales=('sales','sum'), profit=('profit','sum'),
                 customers=('customer_id','nunique'),
                 orders=('order_id','nunique'))
            .reset_index())
region['profit_margin'] = (region['profit'] / region['sales'] * 100).round(2)
region.sort_values('sales', ascending=False, inplace=True)

# Top 10 products
top_products = (df.groupby('product_name')
                  .agg(sales=('sales','sum'), profit=('profit','sum'),
                       orders=('order_id','nunique'))
                  .reset_index()
                  .sort_values('sales', ascending=False)
                  .head(10))
top_products['product_short'] = top_products['product_name'].str[:30] + '...'

# Segment analysis
segment = (df.groupby('segment')
             .agg(sales=('sales','sum'), profit=('profit','sum'),
                  customers=('customer_id','nunique'))
             .reset_index())
segment['profit_margin'] = (segment['profit'] / segment['sales'] * 100).round(2)

# Discount impact
disc_impact = (df.groupby('discount_band')
                 .agg(sales=('sales','sum'), profit=('profit','sum'),
                      orders=('order_id','nunique'))
                 .reset_index())
disc_impact['profit_margin'] = (disc_impact['profit'] / disc_impact['sales'] * 100).round(2)

# State-level (top 10)
state_perf = (df.groupby('state')
                .agg(sales=('sales','sum'), profit=('profit','sum'))
                .reset_index()
                .sort_values('sales', ascending=False)
                .head(10))

# ══════════════════════════════════════════════════════════════════════════
# 6. DASHBOARD  (6-panel)
# ══════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════
# 6. DASHBOARD  (FINAL FIXED VERSION)
# ══════════════════════════════════════════════════════════════════════════
print("\n  Building dashboard...")

# ✅ STEP 1: Create figure FIRST
fig = plt.figure(figsize=(26, 20))
fig.patch.set_facecolor(BG)

# ✅ STEP 2: Grid layout
gs = gridspec.GridSpec(
    3, 3, figure=fig,
    left=0.06, right=0.97, top=0.93, bottom=0.05,
    hspace=0.50, wspace=0.38,
    height_ratios=[0.55, 1.6, 1.6],
)

# ── Title ─────────────────────────────────────────
fig.text(0.5, 0.965,
         "Sales Insights Dashboard",
         ha='center', fontsize=18, color='#E8EAF0', fontweight='bold')

# ── KPI Banner ────────────────────────────────────
ax_kpi = fig.add_subplot(gs[0, :])
ax_kpi.set_facecolor(BG)
ax_kpi.axis('off')

kpi_list = [
    ("TOTAL SALES",      f"${total_sales/1e6:.2f}M",    ACCENT),
    ("TOTAL PROFIT",     f"${total_profit/1e3:.0f}K",   TEAL),
    ("TOTAL ORDERS",     f"{total_orders:,}",            AMBER),
    ("CUSTOMERS",        f"{total_customers:,}",         ROSE),
    ("AVG MARGIN",       f"{avg_margin:.1f}%",           PURPLE),
    ("AVG SHIP DAYS",    f"{avg_ship_days:.1f}",         GREEN),
]

for i, (lbl, val, col) in enumerate(kpi_list):
    x = 0.083 + i * 0.167
    ax_kpi.add_patch(plt.Rectangle(
        (x-0.075, 0.04), 0.150, 0.90,
        transform=ax_kpi.transAxes,
        facecolor=CARD, edgecolor=col, linewidth=2, clip_on=False))
    ax_kpi.text(x, 0.74, lbl, transform=ax_kpi.transAxes,
                ha='center', fontsize=8.5, color='#7A8099', fontweight='bold')
    ax_kpi.text(x, 0.28, val, transform=ax_kpi.transAxes,
                ha='center', fontsize=19, color=col, fontweight='bold')

# ── 1. Monthly Sales & Profit ─────────────────────
ax1 = fig.add_subplot(gs[1, :2])
ax1.set_facecolor(CARD)

xi = range(len(monthly))
ax1.plot(xi, monthly['sales'], color=ACCENT, linewidth=2.5, label='Sales')

ax1.set_title("Monthly Sales Trend", fontsize=13, fontweight='bold')
ax1.grid(axis='y', linestyle='--', alpha=0.3)

# ── 2. Top Categories ─────────────────────────────
ax3 = fig.add_subplot(gs[1, 2])
ax3.set_facecolor(CARD)

top_sub = cat_perf.head(8)
ax3.barh(top_sub['sub-category'], top_sub['sales']/1000)

ax3.set_title("Top Sub-Categories by Sales", fontsize=13, fontweight='bold')

# ── 3. Region Performance ─────────────────────────
ax4 = fig.add_subplot(gs[2, 0])
ax4.set_facecolor(CARD)

bars = ax4.bar(region['region'], region['sales']/1000)

for bar, margin in zip(bars, region['profit_margin']):
    ax4.text(bar.get_x()+bar.get_width()/2,
             bar.get_height(),
             f"{margin:.1f}%", ha='center', fontsize=9)

ax4.set_title("Region Sales & Profit Margin", fontsize=13, fontweight='bold')

# ── 4. Segment Distribution ───────────────────────
ax5 = fig.add_subplot(gs[2, 1])
ax5.set_facecolor(BG)

ax5.pie(segment['sales'],
        autopct='%1.1f%%',
        startangle=120)

ax5.set_title("Sales by Segment", fontsize=13, fontweight='bold')

# ── 5. Discount Impact (FINAL FIX 🔥) ─────────────
ax6 = fig.add_subplot(gs[2, 2])
ax6.set_facecolor(CARD)

valid_disc = disc_impact.dropna(subset=['discount_band'])

ax6.bar(valid_disc['discount_band'].astype(str),
        valid_disc['profit_margin'],
        color=['green', 'orange', 'red', 'darkred'],
        width=0.55)

# Zero reference line
ax6.axhline(0, linestyle='--', linewidth=1)

# ✅ Correct % formatting
import matplotlib.ticker as mtick
ax6.yaxis.set_major_formatter(mtick.PercentFormatter(100))

# Prevent clipping
ax6.set_ylim(min(valid_disc['profit_margin']) - 10,
             max(valid_disc['profit_margin']) + 10)

# Labels (no overlap)
for bar, val in zip(ax6.patches, valid_disc['profit_margin']):
    offset = 2 if val >= 0 else -5
    ax6.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + offset,
             f"{val:.1f}%",
             ha='center', fontsize=9)

ax6.set_title("Profit Margin by Discount Band", fontsize=13, fontweight='bold')

# ── FINAL RENDER ──────────────────────────────────
plt.tight_layout()
#plt.show()
# ══════════════════════════════════════════════════════════════════════════
# 7. EXPORT CSVs for Power BI
# ══════════════════════════════════════════════════════════════════════════
monthly.to_csv("outputs/monthly_sales.csv", index=False)
cat_perf.to_csv("outputs/category_performance.csv", index=False)
region.to_csv("outputs/region_performance.csv", index=False)
top_products.to_csv("outputs/top_products.csv", index=False)
segment.to_csv("outputs/segment_analysis.csv", index=False)
disc_impact.to_csv("outputs/discount_impact.csv", index=False)
state_perf.to_csv("outputs/state_performance.csv", index=False)
df.to_csv("outputs/master_sales.csv", index=False)

print("\n  Exports saved to outputs/")
for f in ['monthly_sales','category_performance','region_performance',
          'top_products','segment_analysis','discount_impact',
          'state_performance','master_sales']:
    print(f"  ✓ {f}.csv")

print("\n" + "=" * 62)
print("  Analysis Complete!")
print("=" * 62)
