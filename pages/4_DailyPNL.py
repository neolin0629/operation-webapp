import streamlit as st
import pandas as pd

st.set_page_config(page_title="Daily PNL", layout="wide")

@st.cache_data
def load_data():
    product = pd.read_csv('data/product.csv', encoding='utf-8')
    account = pd.read_csv('data/account.csv', encoding='utf-8')
    account['date'] = pd.to_datetime(account['date'])
    return product, account

def main():
    st.title("Daily PNL")
    product, account = load_data()
    latest_date = account['date'].max()
    df = account[account['date'] == latest_date]
    df = df.merge(product, on='id', how='left')
 
    st.dataframe(df[['id', 'user', 'amount', 'return', 'netvalue', 'accumulated_netvalue', 'max_drawdown']])

    st.info(f'总资产：{df["amount"].sum()/100000000:,.2f}亿元')
            

if __name__ == "__main__":
    main()

