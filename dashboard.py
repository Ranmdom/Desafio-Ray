import os
import pandas as pd
import streamlit as st
import altair as alt
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv

# --- Carrega dados com cache ---
@st.cache_data(ttl=3600)
def load_data(db_url: str) -> pd.DataFrame:
    engine = create_engine(db_url)
    query = '''
    SELECT
      videoid      AS "videoId",
      title        AS "title",
      publishedat  AS "publishedAt",
      viewcount    AS "viewCount",
      likecount    AS "likeCount",
      commentcount AS "commentCount"
    FROM f1_highlights
    ORDER BY viewcount DESC;
    '''
    df = pd.read_sql(query, engine)
    # Conversão de tipos
    df["publishedAt"] = pd.to_datetime(df["publishedAt"])
    df["date"] = df["publishedAt"].dt.date
    df["month"] = df["publishedAt"].dt.to_period("M").dt.to_timestamp()
    df["likeRate"] = df["likeCount"] / df["viewCount"]
    return df

# --- Função principal ---
def main():
    load_dotenv()
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        st.error("Variável SUPABASE_DB_URL não encontrada")
        st.stop()

    st.set_page_config(
        page_title="F1 Highlights 2024",
        layout="wide"
    )

    # Carrega dados
    df = load_data(db_url)

    # Sidebar de filtros
    with st.sidebar:
        st.header("Filtros")
        # Intervalo de datas
        start_date, end_date = st.date_input(
            "Período de publicação", 
            value=(df["date"].min(), df["date"].max())
        )
    # Aplica filtro de datas
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    # Título do dashboard
    st.title("🏎️ F1 Highlights 2024")

    # 1. Visão Rápida
    st.header("🔍 Visão Rápida")
    total_videos = len(df)
    total_views = df['viewCount'].sum()
    avg_likes = df['likeCount'].mean() or 0
    avg_comments = df['commentCount'].mean() or 0
    avg_like_rate = df['likeRate'].mean() * 100

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Vídeos", f"{total_videos:,}")
    c2.metric("Views", f"{total_views:,}")
    c3.metric("Likes méd.", f"{avg_likes:,.0f}")
    c4.metric("Comentários méd.", f"{avg_comments:,.0f}")
    c5.metric("Taxa de likes (%)", f"{avg_like_rate:.1f}%")
    st.markdown("---")

    # 2. Top 5 Corridas
    st.header("🏆 Top 5 Highlights por Views")
    top5 = df.nlargest(5, "viewCount")
    fig_top = px.bar(
        top5, x="viewCount", y="title", orientation="h",
        labels={"viewCount": "Views", "title": "Título"},
        title="📈 Vídeos Mais Assistidos"
    )
    fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top, use_container_width=True)
    st.markdown("---")

    # 3. Evolução Mensal de Views
    st.header("📆 Evolução Mensal de Views")
    monthly_views = (
        df.groupby(df["month"].dt.to_period("M").dt.to_timestamp())["viewCount"]
          .sum().reset_index())
    chart_month = (
        alt.Chart(monthly_views)
        .mark_line(point=True)
        .encode(
            x=alt.X("month:T", title="Mês"),
            y=alt.Y("viewCount:Q", title="Total de Views"),
            tooltip=[alt.Tooltip("month:T"), alt.Tooltip("viewCount:Q")]
        )
        .properties(height=300)
    )
    st.altair_chart(chart_month, use_container_width=True)
    st.markdown("---")

    # 4. Engajamento vs Views
    st.header("🤝 Engajamento vs Views")
    fig_scatter = px.scatter(
        df, x="viewCount", y="likeRate",
        hover_data=["title", "viewCount", "likeRate"],
        labels={"viewCount": "Views", "likeRate": "Taxa de Likes"},
        title="🎯 Engajamento vs Audiência"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.markdown("---")

    # 5. Crescimento de Engajamento Mensal
    st.header("🚀 Crescimento Mensal de Engajamento")
    monthly_eng = (
        df.groupby(df["month"].dt.to_period("M").dt.to_timestamp())["likeRate"]
          .mean().reset_index())
    chart_eng = (
        alt.Chart(monthly_eng)
        .mark_area(opacity=0.3)
        .encode(
            x=alt.X("month:T", title="Mês"),
            y=alt.Y("likeRate:Q", title="Tx. Média de Likes"),
            tooltip=[alt.Tooltip("month:T"), alt.Tooltip("likeRate:Q", format=".2%")]
        )
        .properties(height=300)
    )
    st.altair_chart(chart_eng, use_container_width=True)

if __name__ == "__main__":
    main()
