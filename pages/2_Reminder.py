import streamlit as st
import pandas as pd
import os

def load_data():
    product = pd.read_csv('data/product.csv', encoding='utf-8')
    account = pd.read_csv('data/account.csv', encoding='utf-8')
    account['date'] = pd.to_datetime(account['date'])
    return product, account

def check_warnings(product, account):
    warnings = {
        'warning_line': [],
        'max_drawdown': [],
        'dividend': []
    }
    
    latest_date = account['date'].max()
    latest_data = account[account['date'] == latest_date]
    
    for _, row in latest_data.iterrows():
        prod_info = product[product['id'] == row['id']].iloc[0]
        
        # 1. 检查净值是否接近预警线
        if row['netvalue'] - prod_info['warning_line'] < 0.01:
            warnings['warning_line'].append({
                '用户': prod_info['user'],
                'ID': row['id'],
                '当前净值': f"{row['netvalue']:.4f}",
                '预警线': f"{prod_info['warning_line']:.4f}"
            })
        
        # 2. 检查最大回撤是否超过3%
        if row['max_drawdown'] < -0.03:
            warnings['max_drawdown'].append({
                '用户': prod_info['user'],
                'ID': row['id'],
                '最大回撤': f"{row['max_drawdown']:.2%}"
            })
        
        # 3. 检查是否有产品可以分红
        if prod_info['dividend_nv'] > 0 and row['netvalue'] >= prod_info['dividend_nv']:
            warnings['dividend'].append({
                '用户': prod_info['user'],
                'ID': row['id'],
                '当前净值': f"{row['netvalue']:.4f}",
                '分红线': f"{prod_info['dividend_nv']:.4f}"
            })
    
    return warnings

def main():
    st.title("产品提醒")
    
    product, account = load_data()
    warnings = check_warnings(product, account)
    
    if any(warnings.values()):
        st.warning("以下产品需要注意：")
        
        if warnings['warning_line']:
            st.subheader("1. 净值接近预警线的产品")
            st.table(pd.DataFrame(warnings['warning_line']))
        
        if warnings['max_drawdown']:
            st.subheader("2. 最大回撤超过3%的产品")
            st.table(pd.DataFrame(warnings['max_drawdown']))
        
        if warnings['dividend']:
            st.subheader("3. 可以进行分红的产品")
            st.table(pd.DataFrame(warnings['dividend']))
    else:
        st.success("目前没有需要特别注意的产品。")

if __name__ == "__main__":
    main()

