import pandas as pd
import streamlit as st
import altair as alt


def plot_chart(group_by, category_column):
    df = pd.DataFrame(group_by).fillna(0).reset_index()
    chart = alt.Chart(df).mark_bar().encode(x='date', y='sum(amount)', color=category_column)
    st.altair_chart(chart, use_container_width=True)


class Spending():
    def __init__(self, data, category_group_column='parentName', category_type_column='categoryType', excluded_types=['NO_CATEGORY'], included_types=None):
        by_day = data['transactions'].copy()
        by_day['amount'] = by_day['amount'] * -1
        by_day['date'] = pd.to_datetime(by_day['date'])
        if included_types:
            by_day = by_day.loc[by_day[category_type_column].isin(included_types)]
        else:
            by_day = by_day.loc[not by_day[category_type_column].isin(excluded_types)]
        by_month = by_day.groupby([pd.Grouper(key='date', freq='1M'), category_group_column]).sum()
        by_year = by_day.groupby([pd.Grouper(key='date', freq='1Y'), category_group_column]).sum()
        st.header('Spending by month')
        plot_chart(by_month, category_group_column)
        st.header('Spending by year')
        plot_chart(by_year, category_group_column)
