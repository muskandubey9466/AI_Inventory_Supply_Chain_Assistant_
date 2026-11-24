
import plotly.express as px


def category_stock_chart(df):

    data = (
        df.groupby("Category")["Quantity"]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        data,
        x="Category",
        y="Quantity",
        color="Category",
        title="Stock Quantity by Category",
        text="Quantity"
    )

    fig.update_layout(
        showlegend=False,
        xaxis_title="Product Category",
        yaxis_title="Available Quantity"
    )

    return fig


def stock_status_chart(df):

    data = (
        df["Stock Status"]
        .value_counts()
        .reset_index()
    )

    data.columns = ["Status", "Count"]

    fig = px.pie(
        data,
        names="Status",
        values="Count",
        title="Inventory Stock Status",
        hole=0.45
    )

    return fig


def supplier_stock_chart(df):

    data = (
        df.groupby("Supplier")["Stock Value"]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        data,
        x="Supplier",
        y="Stock Value",
        title="Inventory Value by Supplier",
        text_auto=".2s"
    )

    return fig
