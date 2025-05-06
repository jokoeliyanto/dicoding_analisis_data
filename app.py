import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import squarify
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point

st.set_page_config(layout="wide")

st.title("Delivery Time Dashboard")
st.text("Dashboard for analyzing late delivery and its impact for customer review")
st.text("By: Joko Eliyanto")


df_late = pd.read_csv('df_late.csv')

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
    hole=0.3  
)


df_monthly_status = pd.read_csv('df_monthly_status.csv')

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


df_top10_city_status_long = pd.read_csv('df_top10_city_status_long.csv')
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

fig_city.update_layout(
    barmode='stack',
    yaxis={'categoryorder': 'total ascending'},
    legend_title='Delivery Status'
)

df_late_and_reviews = pd.read_csv('df_late_and_reviews.csv')

fig_scatter = px.scatter(
    df_late_and_reviews,
    x='late_orders',
    y='avg_review_score',
    title='Relationship Between Late Orders and Average Review Score',
    labels={'late_orders': 'Number of Late Orders', 'avg_review_score': 'Average Review Score'},
    color='avg_review_score',  
    color_continuous_scale='Blues',
    opacity=0.7
)


col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.plotly_chart(fig_city, use_container_width=True)

st.plotly_chart(fig_bar, use_container_width=True)

st.plotly_chart(fig_scatter, use_container_width=True)

rfm = pd.read_csv('rfm.csv')

segment_counts = rfm['Segment'].value_counts()
labels = segment_counts.index.tolist()
sizes = segment_counts.values.tolist()

colors = plt.cm.Set3(range(len(labels)))

st.subheader("Advance Analytics",  divider="gray")
st.markdown("#### RFM Analysis")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(12, 8))
    squarify.plot(
        sizes=sizes, 
        label=[f"{label}\n({count})" for label, count in zip(labels, sizes)],
        color=colors,
        alpha=0.8,
        ax=ax  
    )
    ax.axis('off')  
    st.pyplot(fig)  

with col2:
    segment_summary = rfm.groupby('Segment')[['Recency', 'Frequency', 'Monetary']].mean().reset_index()

    segment_summary['Customer Count'] = rfm.groupby('Segment').size().values

    segment_summary['Frequency'] = segment_summary['Frequency'].astype(int)
    segment_summary['Monetary'] = segment_summary['Monetary'].astype(int)

    styled_df = segment_summary.style.bar(
        subset=['Customer Count', 'Recency', 'Frequency', 'Monetary'],
        color='#5fba7d'
    ).format({'Recency': '{:.1f}', 'Frequency': '{:d}', 'Monetary': '{:d}'})

    st.dataframe(styled_df, use_container_width=True)

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


fig_bar_segment = px.bar(
    x=segment_counts.index,
    y=segment_counts.values,
    labels={'x': 'Segment', 'y': 'Number of Customers'},
    title='Number of Customers per Segment',
    color=segment_counts.index,
    color_discrete_sequence=px.colors.qualitative.Set2
)

fig_bar_segment.update_layout(
    xaxis_title='Segment',
    yaxis_title='Number of Customers',
    xaxis_tickangle=45
)

fig_scatter_segment = px.scatter(
    rfm,
    x='Frequency',
    y='Monetary',
    color='Segment',
    title='Frequency vs Monetary by Segment',
    labels={'Frequency': 'Frequency', 'Monetary': 'Monetary'},
    color_discrete_sequence=px.colors.qualitative.Set2
)

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig_bar_segment, use_container_width=True)

with col2:
    st.plotly_chart(fig_scatter_segment, use_container_width=True)

st.markdown("#### Geospatial Analysis")

@st.cache_data
def load_world():
    url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
    return gpd.read_file(url)

world = load_world()

df_state_grouped = pd.read_csv('df_state_grouped.csv')

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
        projection=dict(type='natural earth'),  
        showland=True,
        landcolor='lightgray'
    ),
    title='Customer Distribution by State',
    title_x=0.5
)


st.plotly_chart(fig, use_container_width=True)


st.markdown("#### Clustering")
grouped = pd.read_csv('grouped.csv')

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