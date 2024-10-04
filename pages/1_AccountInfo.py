import pandas as pd
import streamlit as st

st.set_page_config(page_title="Account Information", layout="wide")

def main():
    st.title("Account Information")
    product = pd.read_csv('./data/product.csv', dtype={'monitor_center_account': str})
    st.dataframe(product)

if __name__ == "__main__":
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.warning("😕 Please input Password in Home page")
    else:
        main()