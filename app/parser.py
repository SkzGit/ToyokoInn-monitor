from datetime import datetime, timedelta
import re
from unittest import result
DEBUG = False

from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/137.0 Safari/537.36"
)

def get_smoking_type(header_text):
    if "禁煙" in header_text:
        return "禁煙"
    if "喫煙" in header_text:
        return "喫煙"
    return "不明"

def check_room_status(url, stay, candidate):
    """
    戻り値

    {
        "available": bool,
        "remaining": int | None,
        "room_name": str,
        "smoking": str,
    }
    """

    results = []

    with sync_playwright() as p:
        
        browser = None

        try:

            browser = p.chromium.launch(
                headless=False,
            )

            page = browser.new_page(
                user_agent=USER_AGENT,
            )

            page.goto(
                url,
                wait_until="networkidle",
                timeout=60000,
            )

            checkin = datetime.strptime(
                stay["date"],
                "%Y-%m-%d",
            )

            checkout = checkin + timedelta(days=stay["nights"])

            checkin_day = str(checkin.day)
            checkout_day = str(checkout.day)

            #
            # 日付選択
            #

            page.locator(
                ".Popup_date__Is_J7 .FormInput_box__MpR5H"
            ).click()

            page.get_by_role(
                "button",
                name="選択を解除",
            ).click()

            page.wait_for_timeout(300)

            #
            # 目的の月が表示されるまで送る
            #

            target_month = f"{checkin.year}年{checkin.month}月"

            while True:

                months = page.locator("text=/\\d{4}年\\d{1,2}月/").all_inner_texts()

                # print("表示中の月:", months)

                if target_month in months:
                    break

                page.locator(".CalendarPager_button__Srb_0").last.click()

                page.wait_for_timeout(500)

            #
            # チェックイン
            #

            page.locator(
                f'[id="{checkin.strftime("%Y-%m")}"]'
            ).get_by_role(
                "button",
                name=checkin_day,
                exact=True,
            ).click()

            page.wait_for_timeout(300)

            #
            # チェックアウト月が表示されるまで送る
            #

            target_month = f"{checkout.year}年{checkout.month}月"

            while True:

                months = page.locator(
                    r"text=/\d{4}年\d{1,2}月/"
                ).all_inner_texts()

                if target_month in months:
                    break

                page.locator(
                    ".CalendarPager_button__Srb_0"
                ).last.click()

                page.wait_for_timeout(500)

            #
            # チェックアウト
            #

            page.locator(
                f'[id="{checkout.strftime("%Y-%m")}"]'
            ).get_by_role(
                "button",
                name=checkout_day,
                exact=True,
            ).click()

            page.wait_for_timeout(300)

            #
            # 人数
            #

            page.locator(
                ".Popup_amount__hj7sk "
                "> .FormInput_form-input__JiFIp "
                "> .FormInput_box__MpR5H"
            ).click()

            page.evaluate(
                """
                () => {
                    document
                        .querySelectorAll(".FormCount_form-count__UnWAv")[0]
                        .querySelectorAll("button")[1]
                        .click();
                }
                """
            )
            
            page.wait_for_timeout(300)

            # 人数ダイアログを閉じる
            page.locator(
                ".Popup_amount__hj7sk "
                "> .FormInput_form-input__JiFIp "
                "> .FormInput_box__MpR5H"
            ).click()

            page.wait_for_timeout(300)

            # デバッグ用
            # page.pause()

            #
            # 禁煙・喫煙
            #

            # print(f'禁煙・喫煙選択: {candidate["smoking"]}')

            # 入力欄を開く
            page.locator(
                ".BookingForm_form__zjBYX .FormInput_box__MpR5H"
            ).nth(2).click()

            page.wait_for_timeout(500)

            # ダイアログが表示されるまで待機
            page.locator(
                ".PopupSmokingType_popover-content__3aMN7"
            ).wait_for(state="visible")

            # 禁煙・喫煙を選択
            page.locator(
                ".PopupSmokingType_popover-content__3aMN7 label"
            ).filter(
                has_text=candidate["smoking"]
            ).click()

            page.wait_for_timeout(500)

            #
            # 検索
            #

            page.evaluate(
                """
                () => {
                    [...document.querySelectorAll("button")]
                        .find(b => b.textContent.includes("空室を検索"))
                        .click();
                }
                """
            )

            page.wait_for_url(
                "**/search/result/**",
                timeout=30000,
            )

            page.wait_for_load_state("networkidle")

            page.wait_for_timeout(3000)

            # デバッグ用
            # page.pause()

            # HTML保存→削除

            # print("現在のURL =", page.url)

            # 取得情報表示
            # print(page.locator("body").inner_text())

            #
            # 部屋カード一覧
            #

            parent_cards = page.locator(
                'div:has(> div[class*="SearchResultRoomPlanParentCard_card-wrapper"])'
            )

            count = parent_cards.count()

            # print(f"parent_cards = {count}")

            for i in range(count):

                parent = parent_cards.nth(i)

                #
                # 部屋情報
                #

                header = parent.locator(
                    'div[class*="SearchResultRoomPlanParentCard_card-wrapper"]'
                )

                title = header.locator("h2").inner_text().strip()

                if DEBUG:
                    print(title)

                header_text = header.inner_text()

                smoking = get_smoking_type(header_text)

                # 喫煙・禁煙の絞り込み
                requested_smoking = candidate["smoking"]

                if (
                    requested_smoking != "指定なし"
                    and smoking != requested_smoking
                ):
                    continue

                #
                # 部屋名判定
                #

                if candidate["roomSearch"] not in title:
                    continue

                #
                # 禁煙・喫煙判定　←削除
                #

                # 「指定なし」は判定しない

                # print("対象の部屋:", title)

                #
                # 空室情報
                #

                body = parent.locator(
                    'div[class*="SearchResultRoomPlanParentCard_child-list"]'
                )

                body_text = body.inner_text()

                price = None

                m = re.search(r"¥\s*([\d,]+)", body_text)

                if m:
                    price = m.group(1)                

                #
                # 空室なし
                #

                if "空室がありません" in body_text:
                    continue

                #
                # 残り○室
                #

                m = re.search(r"残り\s*(\d+)室", body_text)

                if m:

                    remain = int(m.group(1))

                    result = {
                        "available": True,
                        "remaining": remain,
                        "room_name": title,
                        "smoking": smoking,
                        "price": price,
                    }

                    results.append(result)

                    continue

            # print(result)

        finally:
            if browser:
                browser.close()
                
        return results