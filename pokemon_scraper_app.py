import os
import requests
from bs4 import BeautifulSoup
import streamlit as st
from pathlib import Path
from io import BytesIO
import zipfile
import re
from datetime import datetime, timedelta, timezone

# 日本時間の取得関数
def get_japan_time_str():
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    return now.strftime('%Y-%m-%d_%H-%M-%S')

# 商品名の抽出とファイル名整形
def get_product_name(soup):
    title = soup.find("title")
    if title:
        name = title.text.split('|')[0].strip()
        name = re.sub(r'[\\/*?:"<>|]', "", name)
        return name
    return "商品名不明"

# 画像URLとフォルダ名の取得
def scrape_images_and_name(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    product_name = get_product_name(soup)
    date_str = get_japan_time_str()
    folder_name = f"{product_name}_{date_str}"

    photo_list_div = soup.find('div', class_='photoList')
    image_urls = []

    if photo_list_div:
        item_divs = photo_list_div.find_all('div', class_='item')
        for item in item_divs:
            first_img = item.find('img')
            if first_img:
                img_url = first_img.get("src")
                if img_url and not img_url.startswith("http"):
                    img_url = requests.compat.urljoin(url, img_url)
                if img_url and 'data:image' not in img_url:
                    image_urls.append(img_url)

    return folder_name, image_urls

# ZIPファイルの作成
def create_zip(images, folder_name):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for idx, img_url in enumerate(images):
            try:
                img_data = requests.get(img_url).content
                file_path = f"{folder_name}/image_{idx + 1}.jpg"
                zip_file.writestr(file_path, img_data)
            except Exception as e:
                print(f"画像取得エラー: {e}")
                continue
    zip_buffer.seek(0)
    return zip_buffer

# -------------------------------
# Streamlit アプリ本体
# -------------------------------

correct_password = "1212"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("画像ダウンロードツール🔒")
    password_input = st.text_input("暗証番号を入力してください:", type="password")

    if password_input == correct_password:
        st.session_state.authenticated = True
        st.success("認証に成功しました。ツールを起動します。")
        st.rerun()  # ← ここを修正済み
    elif password_input:
        st.error("暗証番号が間違っています。")
else:
    st.title("ポケモンセンター画像スクレイピングアプリ")

    url = st.text_input("商品ページのURLを入力してください:")

    if st.button("画像を取得"):
        if url:
            with st.spinner("画像を取得中..."):
                folder_name, image_urls = scrape_images_and_name(url)
                if image_urls:
                    st.success(f"{folder_name} から {len(image_urls)} 枚の画像を取得しました。")
                    for img_url in image_urls:
                        st.image(img_url, width=200)
                    
                    zip_file = create_zip(image_urls, folder_name)
                    st.download_button(
                        label="画像をまとめてダウンロード（ZIP）",
                        data=zip_file,
                        file_name=f"{folder_name}.zip",
                        mime="application/zip"
                    )
                else:
                    st.warning("画像が見つかりませんでした。")
        else:
            st.error("URLを入力してください。")
