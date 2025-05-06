import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import squarify
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point

# Atur tampilan jadi wide
st.set_page_config(layout="wide")

# Judul aplikasi
st.title("Delivery Time Dashboard")
st.text("Dashboard for analyzing late delivery and its impact for customer review")
st.text("By: Joko Eliyanto")


@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_and_joined_data.csv", parse_dates=["order_purchase_timestamp"])
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    return df

df = load_data()

# Sidebar filter tanggal
st.sidebar.header("Filter Tanggal")
min_date = df["order_purchase_timestamp"].min()
max_date = df["order_purchase_timestamp"].max()

start_date, end_date = st.sidebar.date_input(
    "Pilih rentang tanggal:",
    [min_date.date(), max_date.date()],
    min_value=min_date.date(),
    max_value=max_date.date()
)

# Filter data berdasarkan tanggal
filtered_df = df[
    (df["order_purchase_timestamp"].dt.date >= start_date) &
    (df["order_purchase_timestamp"].dt.date <= end_date)
]

#----- Pie Chart (Plotly) Distribusi Status Pengiriman -----
# st.subheader("Distribusi Status Pengiriman")

# Hitung distribusi pengiriman
df_late = filtered_df.groupby(['delivered_late']).agg({"order_id": "count"}).reset_index()
df_late = df_late.sort_values(by="order_id", ascending=True)
df_late['delivered_late'] = df_late['delivered_late'].map({
    False: 'On-time Delivery',
    True: 'Late Deliveries'
})

# Buat pie chart dengan Plotly
fig_pie = px.pie(
    df_late,
    values='order_id',
    names='delivered_late',
    color='delivered_late',
    color_discrete_map={
        'On-time Delivery': '#66b3ff',
        'Late Deliveries': '#ff9999'
    },
    title='Delivery Status Distribution',
    hole=0.3  # untuk tampilkan sebagai donut chart, hapus kalau mau pie biasa
)

# ----- Stacked Bar Chart Bulanan (Plotly) -----
# st.subheader("Status Pengiriman Bulanan")

# Pastikan kolom order_month bertipe period
filtered_df['order_month'] = filtered_df['order_purchase_timestamp'].dt.to_period('M').astype(str)

# Hitung jumlah pesanan per bulan berdasarkan status pengiriman
df_monthly_status = filtered_df.groupby(['order_month', 'delivered_late'])['order_id'].count().reset_index()

# Ganti label boolean jadi string
df_monthly_status['delivered_late'] = df_monthly_status['delivered_late'].map({
    False: 'On-time Delivery',
    True: 'Late Deliveries'
})

df_monthly_status.to_csv("df_monthly_status.csv", index=False)

# Buat stacked bar chart dengan Plotly
fig_bar = px.bar(
    df_monthly_status,
    x='order_month',
    y='order_id',
    color='delivered_late',
    title='Monthly Delivery Status: On-time vs Late Deliveries',
    labels={'order_id': 'Number of Orders', 'order_month': 'Month'},
    color_discrete_map={
        'On-time Delivery': '#66b3ff',
        'Late Deliveries': '#ff9999'
    }
)

fig_bar.update_layout(barmode='stack', xaxis_tickangle=-45)

# ----- Horizontal Stacked Bar Chart: Top 10 Cities by Delivery Status -----
# st.subheader("Top 10 Kota dengan Status Pengiriman Terbanyak")

# Hitung jumlah pengiriman per kota dan status
df_city_status = filtered_df.groupby(['customer_city', 'delivered_late'])['order_id'].count().unstack(fill_value=0)

# Ambil 10 kota teratas berdasarkan total pengiriman
top_10_cities = df_city_status.sum(axis=1).nlargest(10).index
df_top10_city_status = df_city_status.loc[top_10_cities]

# Ubah dari wide ke long format untuk plotly
df_top10_city_status_long = df_top10_city_status.reset_index().melt(
    id_vars='customer_city',
    value_vars=[False, True],
    var_name='delivered_late',
    value_name='order_count'
)

# Ganti nama status pengiriman
df_top10_city_status_long['delivered_late'] = df_top10_city_status_long['delivered_late'].map({
    False: 'On-time Delivery',
    True: 'Late Deliveries'
})

# Buat horizontal stacked bar chart
fig_city = px.bar(
    df_top10_city_status_long,
    x='order_count',
    y='customer_city',
    color='delivered_late',
    orientation='h',
    title='Top 10 Cities by Delivery Status: On-time vs Late Deliveries',
    labels={'order_count': 'Number of Orders', 'customer_city': 'City'},
    color_discrete_map={
        'On-time Delivery': '#66b3ff',
        'Late Deliveries': '#ff9999'
    }
)

# Urutkan kota berdasarkan total pengiriman (agar terbesar di atas)
fig_city.update_layout(
    barmode='stack',
    yaxis={'categoryorder': 'total ascending'},
    legend_title='Delivery Status'
)

# Menghitung jumlah pesanan terlambat per kota
df_late_deliveries = df[df['delivered_late'] == True]
late_orders_per_city = df_late_deliveries.groupby('customer_city')['order_id'].count()

# Menghitung rata-rata review score per kota
avg_review_per_city = df.groupby('customer_city')['calculated_review_score'].mean()

# Menggabungkan kedua informasi menjadi satu DataFrame
df_late_and_reviews = pd.DataFrame({
    'late_orders': late_orders_per_city,
    'avg_review_score': avg_review_per_city
}).dropna()  # Menghapus NaN jika ada kota yang tidak memiliki pesanan terlambat atau review

# Membuat scatter plot menggunakan Plotly
fig_scatter = px.scatter(
    df_late_and_reviews,
    x='late_orders',
    y='avg_review_score',
    title='Relationship Between Late Orders and Average Review Score',
    labels={'late_orders': 'Number of Late Orders', 'avg_review_score': 'Average Review Score'},
    color='avg_review_score',  # Memberikan warna berdasarkan rating review
    color_continuous_scale='Blues',
    opacity=0.7
)


# Layout dengan dua kolom: Pie chart di kolom kiri dan Bar chart di kolom kanan
col1, col2 = st.columns(2)

with col1:
    # Menampilkan pie chart di kolom pertama
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Menampilkan bar chart di kolom kedua
    st.plotly_chart(fig_city, use_container_width=True)

# Menampilkan scatter plot
st.plotly_chart(fig_bar, use_container_width=True)

# Menampilkan scatter plot
st.plotly_chart(fig_scatter, use_container_width=True)

# Pastikan kolom tanggal dalam format datetime
df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'])

# Tentukan tanggal referensi (misalnya, hari ini)
reference_date = datetime.today()

# 1. Recency: Menghitung selisih antara tanggal pengiriman terakhir dengan tanggal referensi
recency = df.groupby('customer_id')['order_delivered_customer_date'].max()
recency = (reference_date - recency).dt.days  # Hitung selisih dalam hari

# 2. Frequency: Menghitung jumlah pesanan per pelanggan
frequency = df.groupby('customer_id')['order_id'].count()

# 3. Monetary: Menghitung total pembayaran per pelanggan
monetary = df.groupby('customer_id')['payment_value_sum'].sum()

# Gabungkan ketiga metrik menjadi satu DataFrame
rfm = pd.DataFrame({
    'Recency': recency,
    'Frequency': frequency,
    'Monetary': monetary
})

# Mengisi nilai kosong dengan 0 sebelum melanjutkan ke proses penghitungan skor
rfm = rfm.fillna(0)

# Cek apakah kolom 'Frequency' memiliki cukup variasi
if len(rfm['Frequency'].unique()) > 1:
    # Skor berdasarkan kuantil untuk Frequency jika ada variasi
    rfm['F_rank'] = pd.qcut(rfm['Frequency'], 5, labels=False) + 1
else:
    # Jika tidak ada variasi, beri skor tetap (misalnya 3)
    rfm['F_rank'] = 3

# Skor untuk Recency dan Monetary tetap menggunakan qcut
rfm['R_rank'] = pd.qcut(rfm['Recency'], 5, labels=False) + 1
rfm['M_rank'] = pd.qcut(rfm['Monetary'], 5, labels=False) + 1

# Pastikan nilai pada kolom R_rank, F_rank, dan M_rank berupa integer
rfm['R_rank'] = rfm['R_rank'].astype(int)
rfm['F_rank'] = rfm['F_rank'].astype(int)
rfm['M_rank'] = rfm['M_rank'].astype(int)

# Gabungkan skor RFM menjadi satu kolom
rfm['RFM_Score'] = rfm['R_rank'].astype(str) + rfm['F_rank'].astype(str) + rfm['M_rank'].astype(str)

def assign_rfm_segment(score):
    if score == '555':
        return 'Best Customers'
    elif score == '111':
        return 'Lost'
    elif score[0] == '1':
        return 'New Customers'
    elif score[1] == '5':
        return 'Loyal Customers'
    elif score[1] == '1':
        return 'About to Sleep'
    elif score[2] == '5':
        return 'Big Spenders'
    elif score[2] == '1':
        return 'Low Value'
    elif score[0] in '45' and score[1] in '45':
        return 'Champions'
    elif score[0] in '34' and score[1] in '34':
        return 'Potential Loyalists'
    elif score[0] in '23' and score[1] in '12':
        return 'At Risk'
    else:
        return 'Other'

# Terapkan fungsi ke kolom RFM_Score
rfm['Segment'] = rfm['RFM_Score'].astype(str).apply(assign_rfm_segment)

# Hitung jumlah customer per segment
segment_counts = rfm['Segment'].value_counts()
labels = segment_counts.index.tolist()
sizes = segment_counts.values.tolist()

# Warna acak untuk setiap segmen
colors = plt.cm.Set3(range(len(labels)))

st.subheader("Advance Analytics",  divider="gray")
st.markdown("#### RFM Analysis")


# Layout Streamlit dengan dua kolom
col1, col2 = st.columns(2)

# Menampilkan treemap di kolom pertama
with col1:
    # Buat figure dan axis
    fig, ax = plt.subplots(figsize=(12, 8))
    squarify.plot(
        sizes=sizes, 
        label=[f"{label}\n({count})" for label, count in zip(labels, sizes)],
        color=colors,
        alpha=0.8,
        ax=ax  # Gunakan axis yang telah dibuat
    )
    # ax.set_title("Treemap Segmentasi Pelanggan Berdasarkan Jumlah", fontsize=16)
    ax.axis('off')  # Sembunyikan axis
    st.pyplot(fig)  # Kirimkan fig ke st.pyplot()

# Menampilkan DataFrame berdasarkan segmen di kolom kedua
with col2:
    # Grouping by segment and aggregating mean values of Recency, Frequency, and Monetary
    segment_summary = rfm.groupby('Segment')[['Recency', 'Frequency', 'Monetary']].mean().reset_index()

    # Adding customer count by using group size (since customer_id is the index)
    segment_summary['Customer Count'] = rfm.groupby('Segment').size().values

    # Convert to integer for clean display
    segment_summary['Frequency'] = segment_summary['Frequency'].astype(int)
    segment_summary['Monetary'] = segment_summary['Monetary'].astype(int)

    # Apply bar-style coloring to the metrics
    styled_df = segment_summary.style.bar(
        subset=['Customer Count', 'Recency', 'Frequency', 'Monetary'],
        color='#5fba7d'
    ).format({'Recency': '{:.1f}', 'Frequency': '{:d}', 'Monetary': '{:d}'})

    # Display the styled DataFrame in Streamlit
    st.dataframe(styled_df, use_container_width=True)

# Layout 3 columns in Streamlit
col1, col2, col3 = st.columns(3)

with col1:
    fig_rec = px.histogram(rfm.reset_index(), x='Recency', nbins=30, title='Distribution of Recency',
                           color_discrete_sequence=['skyblue'])
    st.plotly_chart(fig_rec, use_container_width=True)

with col2:
    fig_freq = px.histogram(rfm.reset_index(), x='Frequency', nbins=30, title='Distribution of Frequency',
                            color_discrete_sequence=['lightgreen'])
    st.plotly_chart(fig_freq, use_container_width=True)

with col3:
    fig_mon = px.histogram(rfm.reset_index(), x='Monetary', nbins=30, title='Distribution of Monetary',
                           color_discrete_sequence=['salmon'])
    st.plotly_chart(fig_mon, use_container_width=True)

# --- Plotly Visualizations ---
# 1. Bar chart for number of customers per segment (Plotly)
fig_bar_segment = px.bar(
    x=segment_counts.index,
    y=segment_counts.values,
    labels={'x': 'Segment', 'y': 'Number of Customers'},
    title='Number of Customers per Segment',
    color=segment_counts.index,
    color_discrete_sequence=px.colors.qualitative.Set2
)

# Update layout for better appearance
fig_bar_segment.update_layout(
    xaxis_title='Segment',
    yaxis_title='Number of Customers',
    xaxis_tickangle=45
)

# 2. Scatter plot for Frequency vs Monetary by Segment (Plotly)
fig_scatter_segment = px.scatter(
    rfm,
    x='Frequency',
    y='Monetary',
    color='Segment',
    title='Frequency vs Monetary by Segment',
    labels={'Frequency': 'Frequency', 'Monetary': 'Monetary'},
    color_discrete_sequence=px.colors.qualitative.Set2
)

# Use st.columns to display the plots side by side
col1, col2 = st.columns(2)

# Plot the bar chart in the first column
with col1:
    st.plotly_chart(fig_bar_segment, use_container_width=True)

# Plot the scatter plot in the second column
with col2:
    st.plotly_chart(fig_scatter_segment, use_container_width=True)

st.markdown("#### Geospatial Analysis")
# --- Load data negara dari GeoJSON online ---
@st.cache_data
def load_world():
    url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
    return gpd.read_file(url)

world = load_world()

# Agregasi per state
df_state_grouped = df.groupby('customer_state').agg({
    'customer_id': 'nunique',
    'geolocation_lat_cons': 'mean',
    'geolocation_lng_cons': 'mean'
}).reset_index()

df_state_grouped.rename(columns={'customer_id': 'customer_count'}, inplace=True)

# Plot
fig = px.scatter_geo(
    df_state_grouped,
    lat='geolocation_lat_cons',
    lon='geolocation_lng_cons',
    hover_name='customer_state',
    size='customer_count',
    projection='natural earth',
    color='customer_count',
    color_continuous_scale='Viridis'
)


fig.update_layout(
    geo=dict(
        projection=dict(type='natural earth'),  # atau 'equirectangular', 'mercator', dll.
        showland=True,
        landcolor='lightgray'
    ),
    title='Customer Distribution by State',
    title_x=0.5
)

# Tampilkan di Streamlit
st.plotly_chart(fig, use_container_width=True)


# Ensure all required columns are present
cols_needed = ['product_category_name_english', 'product_weight_g', 'product_length_cm', 
               'product_height_cm', 'product_width_cm', 'shipping_late', 'delivered_late']
df_clean = df[cols_needed].dropna()

# Calculate product volume
df_clean['product_volume_cm3'] = (
    df_clean['product_length_cm'] * 
    df_clean['product_height_cm'] * 
    df_clean['product_width_cm']
)

# Calculate medians
weight_median = df_clean['product_weight_g'].median()
volume_median = df_clean['product_volume_cm3'].median()

# Define product complexity group
def categorize_complexity(row):
    weight = row['product_weight_g']
    volume = row['product_volume_cm3']
    if weight <= weight_median and volume <= volume_median:
        return 'Light & Compact'
    elif weight <= weight_median and volume > volume_median:
        return 'Bulky but Light'
    elif weight > weight_median and volume <= volume_median:
        return 'Heavy & Compact'
    else:
        return 'Heavy & Bulky'

df_clean['complexity_group'] = df_clean.apply(categorize_complexity, axis=1)

# Aggregate delivery delay metrics by group
grouped = df_clean.groupby('complexity_group').agg(
    total_orders=('shipping_late', 'count'),
    shipping_late_rate=('shipping_late', 'mean'),
    delivered_late_rate=('delivered_late', 'mean')
).reset_index()

# Round percentage values
grouped['shipping_late_rate'] = (grouped['shipping_late_rate'] * 100).round(2)
grouped['delivered_late_rate'] = (grouped['delivered_late_rate'] * 100).round(2)

st.markdown("#### Clustering")

fig = px.bar(
    grouped.melt(id_vars='complexity_group', value_vars=['shipping_late_rate', 'delivered_late_rate']),
    x='complexity_group',
    y='value',
    color='variable',
    barmode='group',
    text='value',
    labels={'value': 'Late Delivery Rate (%)', 'variable': 'Delay Type'},
    title='Shipping & Delivery Delay by Product Complexity'
)
fig.update_layout(xaxis_title='Product Complexity', yaxis_title='Late Delivery Rate (%)')

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; font-size: 14px;'>
        &copy; 2024 <strong>Joko Eliyanto</strong>. All rights reserved.
        <br><br>
        <a href="https://wa.me/+6282183112655" target="_blank">
            <img src="https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white">
        </a>
        <a href="https://www.linkedin.com/in/joko-eliyanto-23a1b6143/" target="_blank">
            <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white">
        </a>
        <a href="https://github.com/jokoeliyanto" target="_blank">
            <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white">
        </a>
        <a href="mailto:jokoeliyanto@gmail.com" target="_blank">
            <img src="https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white">
        </a>
        <a href="https://medium.com/@jokoeliyanto" target="_blank">
            <img src="https://img.shields.io/badge/Medium-12100E?style=for-the-badge&logo=medium&logoColor=white">
        </a>
    </div>
    """,
    unsafe_allow_html=True
)