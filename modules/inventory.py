
import pandas as pd
import re


def normalize_column_name(name):
    """Normalize column names for easier matching."""
    return re.sub(
        r"[^a-z0-9]",
        "",
        str(name).lower().strip()
    )


def find_column(df, possible_names):

    columns = {
        normalize_column_name(col): col
        for col in df.columns
    }

    for name in possible_names:

        key = normalize_column_name(name)

        if key in columns:
            return columns[key]

    return None


def load_inventory(uploaded_file):

    if uploaded_file.name.lower().endswith(".csv"):

        df = pd.read_csv(uploaded_file)

    elif uploaded_file.name.lower().endswith(".xlsx"):

        df = pd.read_excel(uploaded_file)

    else:

        raise ValueError("Please upload a CSV or Excel file.")

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    return df


def get_inventory_columns(df):

    return {
        "product": find_column(
            df,
            ["Product Name", "Product", "Item", "SKU Name"]
        ),

        "quantity": find_column(
            df,
            ["Quantity", "Stock", "Current Stock", "Available Quantity"]
        ),

        "category": find_column(
            df,
            ["Category", "Product Category"]
        ),

        "supplier": find_column(
            df,
            ["Supplier", "Vendor", "Supplier Name"]
        ),

        "reorder": find_column(
            df,
            ["Reorder Level", "Minimum Stock", "Min Stock"]
        ),

        "price": find_column(
            df,
            ["Unit Price", "Price", "Cost Per Unit"]
        ),

        "value": find_column(
            df,
            ["Stock Value", "Inventory Value", "Total Value"]
        )
    }


def get_low_stock_products(df):

    columns = get_inventory_columns(df)

    quantity_col = columns["quantity"]
    reorder_col = columns["reorder"]

    if not quantity_col or not reorder_col:
        return pd.DataFrame()

    result = df.copy()

    result[quantity_col] = pd.to_numeric(
        result[quantity_col],
        errors="coerce"
    )

    result[reorder_col] = pd.to_numeric(
        result[reorder_col],
        errors="coerce"
    )

    return result[
        result[quantity_col] <= result[reorder_col]
    ]


def get_reorder_recommendations(df):

    columns = get_inventory_columns(df)

    quantity_col = columns["quantity"]
    reorder_col = columns["reorder"]

    if not quantity_col or not reorder_col:
        return pd.DataFrame()

    result = get_low_stock_products(df).copy()

    if result.empty:
        return result

    result["Suggested Reorder Quantity"] = (
        pd.to_numeric(result[reorder_col], errors="coerce")
        -
        pd.to_numeric(result[quantity_col], errors="coerce")
    ).clip(lower=0)

    return result


def get_inventory_summary(df):

    columns = get_inventory_columns(df)

    quantity_col = columns["quantity"]
    value_col = columns["value"]

    quantity = 0

    if quantity_col:

        quantity = pd.to_numeric(
            df[quantity_col],
            errors="coerce"
        ).fillna(0).sum()

    value = 0

    if value_col:

        value = pd.to_numeric(
            df[value_col],
            errors="coerce"
        ).fillna(0).sum()

    return {
        "total_products": len(df),
        "total_quantity": quantity,
        "inventory_value": value,
        "low_stock_items": len(
            get_low_stock_products(df)
        )
    }
