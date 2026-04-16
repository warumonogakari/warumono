"""
hotel_search.py - ホテル空室検索スクリプト
使用方法:
  uv run python hotel/hotel_search.py <場所> <YYYY/M/D>  # 新規検索
  uv run python hotel/hotel_search.py                    # 前回と同じ条件で再検索
条件: 1泊・男性1名・20,000円以内・カプセルホテル不可
検索順: じゃらん → Booking.com → 楽天トラベル（結果が出たら打ち切り）
"""

import sys
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
from playwright.async_api import async_playwright

# 固定条件
BUDGET = 20000
CAPSULE_KEYWORDS = [
    # カプセル系（日本語・英語・表記ゆれ）
    "カプセル", "かぷせる", "capsule", "Capsule",
    # ネットカフェ・漫画喫茶系
    "安心お宿", "まんが喫茶", "漫画喫茶", "ネットカフェ", "CBOX", "コミックバスター",
    # ホステル・ゲストハウス・ドミトリー系
    "ドミトリー", "dormitory", "Dormitory",
    "ホステル", "Hostel", "hostel",
    "ゲストハウス", "Guesthouse", "guesthouse", "Guest House",
    # アダルト系
    "Adult Only", "adult only",
    # 旅籠（カプセル系が多い）
    "旅籠",
    # カプセルホテルブランド（名前に「カプセル」が含まれない）
    "ナインアワーズ", "nine hours", "Nine Hours",
]

# URLに含まれていたら除外するキーワード
CAPSULE_URL_KEYWORDS = [
    "capsule", "hostel", "dormitory", "nine-hours", "ninehours",
]

RESULTS_DIR = Path(__file__).parent / "results"
LAST_SEARCH_FILE = Path(__file__).parent / "last_search.json"


def is_capsule(name: str, url: str = "") -> bool:
    if any(kw in name for kw in CAPSULE_KEYWORDS):
        return True
    if url and any(kw in url.lower() for kw in CAPSULE_URL_KEYWORDS):
        return True
    return False


def save_last_search(location: str, date_str: str) -> None:
    """前回の検索条件を保存"""
    LAST_SEARCH_FILE.write_text(
        json.dumps({"location": location, "date": date_str}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def load_last_search() -> Optional[Tuple[str, str]]:
    """前回の検索条件を読み込む。なければ None を返す"""
    if not LAST_SEARCH_FILE.exists():
        return None
    try:
        data = json.loads(LAST_SEARCH_FILE.read_text(encoding="utf-8"))
        return data["location"], data["date"]
    except Exception:
        return None


def load_previous_hotel_names(location: str, date_str: str) -> set[str]:
    """同じ条件の直前の検索結果からホテル名セットを取得"""
    key = f"{location}_{date_str.replace('/', '')}"
    # results/ 内の該当ファイルを更新日時順に取得
    files = sorted(RESULTS_DIR.glob(f"*_{key}.md"), reverse=True)
    if not files:
        return set()
    # 最新の1件を読んでホテル名を抽出
    prev_file = files[0]
    names = set()
    for line in prev_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            names.add(line[4:].strip())
    return names


def save_results(location: str, date_str: str, site: str, hotels: list[dict], new_names: set[str]) -> Path:
    """結果をMarkdownファイルに保存"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = RESULTS_DIR / f"{timestamp}_{location}_{date_str.replace('/', '')}.md"
    checkout_dt = datetime.strptime(date_str, "%Y/%m/%d") + timedelta(days=1)
    checkout_str = checkout_dt.strftime("%Y/%m/%d")

    lines = [
        f"# ホテル検索結果",
        f"",
        f"## 検索条件",
        f"- 場所: {location}",
        f"- チェックイン: {date_str}",
        f"- チェックアウト: {checkout_str}",
        f"- 人数: 男性1名",
        f"- 予算: {BUDGET:,}円以内",
        f"- 検索サイト: {site}",
        f"- 検索日時: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}",
        f"",
        f"## 検索結果（{len(hotels)}件 / うち新規 {len(new_names)}件）",
        f"",
    ]
    for h in hotels:
        label = " 🆕NEW" if h["name"] in new_names else ""
        lines.append(f"### {h['name']}{label}")
        if h.get("price"):
            lines.append(f"- 料金: {h['price']}")
        lines.append(f"- URL: {h['url']}")
        lines.append("")

    filename.write_text("\n".join(lines), encoding="utf-8")
    return filename


async def search_jalan(page, location: str, checkin: str) -> list[dict]:
    """じゃらんで検索"""
    import re as _re
    print("  じゃらんを検索中...")
    dt = datetime.strptime(checkin, "%Y/%m/%d")

    # Step 1: トップページでキーワード検索を実行
    await page.goto("https://www.jalan.net/", timeout=30000)
    await page.wait_for_timeout(2000)

    kw_input = await page.query_selector("input[name='keyword']")
    if not kw_input:
        return []
    await kw_input.fill(location)
    try:
        async with page.expect_navigation(timeout=15000):
            await page.keyboard.press("Enter")
    except Exception:
        pass

    # Step 2: 結果が表示されるまで待機
    try:
        await page.wait_for_selector(".p-searchResultItem__facilityName", timeout=15000)
    except Exception:
        return []

    # Step 3: 日付フィルターを設定（dateUndecided を解除 → 日付フィールドを有効化）
    await page.evaluate(f"""
        var cb = document.querySelector('input[name="dateUndecided"]');
        if (cb && cb.checked) {{ cb.click(); }}
        var y = document.getElementById('dyn_y_txt');
        var m = document.getElementById('dyn_m_txt');
        var d = document.getElementById('dyn_d_txt');
        if (y) {{ y.disabled = false; y.value = '{dt.year}'; }}
        if (m) {{ m.disabled = false; m.value = '{dt.month:02d}'; }}
        if (d) {{ d.disabled = false; d.value = '{dt.day:02d}'; }}
        var mp = document.querySelector('input[name="maxPrice"]');
        if (mp) {{ mp.value = '{BUDGET}'; }}
    """)
    await page.wait_for_timeout(300)

    # Step 4: 再検索
    try:
        async with page.expect_navigation(timeout=15000):
            await page.evaluate("document.getElementById('research2').click()")
    except Exception:
        await page.wait_for_timeout(5000)

    try:
        await page.wait_for_selector(".p-searchResultItem__facilityName", timeout=15000)
    except Exception:
        return []

    # Step 5: ホテル情報を抽出
    hotels = []
    name_els = await page.query_selector_all(".p-searchResultItem__facilityName")
    price_els = await page.query_selector_all(".p-searchResultItem__lowestPriceValue")
    link_els = await page.query_selector_all(".jlnpc-yadoCassette__link")

    for i, name_el in enumerate(name_els):
        try:
            name = (await name_el.inner_text()).strip()
            if not name:
                continue

            # yado コードから URL を構築
            href = ""
            if i < len(link_els):
                js_href = await link_els[i].get_attribute("data-href") or ""
                m = _re.search(r"openYadoSyosai\('(\d+)'", js_href)
                if m:
                    href = f"https://www.jalan.net/yad{m.group(1)}/"

            if is_capsule(name, href):
                continue

            # 価格テキストを取得（例: "12,500円～/人"）
            price = ""
            if i < len(price_els):
                price = (await price_els[i].inner_text()).strip()
                # 予算超過をフィルタリング
                nums = _re.findall(r"[\d,]+", price)
                if nums:
                    try:
                        val = int(nums[0].replace(",", ""))
                        if val > BUDGET:
                            continue
                    except ValueError:
                        pass

            hotels.append({"name": name, "url": href, "price": price})
        except Exception:
            continue

    return hotels[:20]


async def search_booking(page, location: str, checkin: str) -> list[dict]:
    """Booking.comで検索"""
    print("  Booking.comを検索中...")
    dt = datetime.strptime(checkin, "%Y/%m/%d")
    checkout = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
    checkin_fmt = dt.strftime("%Y-%m-%d")

    url = (
        f"https://www.booking.com/searchresults.ja.html"
        f"?ss={location}&checkin={checkin_fmt}&checkout={checkout}"
        f"&group_adults=1&no_rooms=1&nflt=price%3DJPY-min-{BUDGET}-1"
    )
    await page.goto(url, timeout=30000)
    await page.wait_for_timeout(4000)

    hotels = []
    items = await page.query_selector_all('[data-testid="property-card"]')

    for item in items:
        try:
            name_el = await item.query_selector('[data-testid="title"]')
            if not name_el:
                continue
            name = (await name_el.inner_text()).strip()
            if not name:
                continue

            link_el = await item.query_selector('a[data-testid="title-link"]')
            href = ""
            if link_el:
                href = await link_el.get_attribute("href")
                if href and not href.startswith("http"):
                    href = "https://www.booking.com" + href

            if is_capsule(name, href):
                continue

            price_el = await item.query_selector('[data-testid="price-and-discounted-price"]')
            price = ""
            if price_el:
                price = (await price_el.inner_text()).strip()

            hotels.append({"name": name, "url": href, "price": price})
        except Exception:
            continue

    return hotels[:20]


async def search_rakuten(page, location: str, checkin: str) -> list[dict]:
    """楽天トラベルで検索"""
    print("  楽天トラベルを検索中...")
    dt = datetime.strptime(checkin, "%Y/%m/%d")
    checkout = (dt + timedelta(days=1))

    url = (
        f"https://search.travel.rakuten.co.jp/ds/hotellist/Japan-Tokyo-Tokyo"
        f"?f_nen1={dt.year}&f_tuki1={dt.month:02d}&f_hi1={dt.day:02d}"
        f"&f_nen2={checkout.year}&f_tuki2={checkout.month:02d}&f_hi2={checkout.day:02d}"
        f"&f_adult_su=1&f_max_charge={BUDGET}&keyword={location}"
    )
    await page.goto(url, timeout=30000)
    await page.wait_for_timeout(3000)

    hotels = []
    items = await page.query_selector_all(".hotel-list-item, [class*='hotelItem'], .hotelUnit")

    for item in items:
        try:
            name_el = await item.query_selector("h2 a, h3 a, [class*='hotelName'] a")
            if not name_el:
                continue
            name = (await name_el.inner_text()).strip()
            if not name:
                continue

            href = await name_el.get_attribute("href")
            if href and not href.startswith("http"):
                href = "https://travel.rakuten.co.jp" + href

            if is_capsule(name, href or ""):
                continue

            price_el = await item.query_selector("[class*='price'], [class*='charge']")
            price = ""
            if price_el:
                price = (await price_el.inner_text()).strip()

            hotels.append({"name": name, "url": href, "price": price})
        except Exception:
            continue

    return hotels[:20]


async def main():
    # 引数解析
    if len(sys.argv) == 1:
        # 引数なし → 前回の条件で再検索
        last = load_last_search()
        if last is None:
            print("エラー: 前回の検索条件が見つかりません。")
            print("使用方法: uv run python hotel/hotel_search.py <場所> <YYYY/M/D>")
            sys.exit(1)
        location, date_str = last
        print(f"（前回の条件で再検索: {location} / {date_str}）")
    elif len(sys.argv) == 3:
        location = sys.argv[1]
        date_str = sys.argv[2]
        # 日付バリデーション
        try:
            dt = datetime.strptime(date_str, "%Y/%m/%d")
            date_str = dt.strftime("%Y/%m/%d")
        except ValueError:
            print(f"エラー: 日付の形式が正しくありません。")
            print(f"  入力値: {date_str}")
            print(f"  正しい形式: YYYY/M/D（例: 2026/4/11）")
            sys.exit(1)
    else:
        print("エラー: 引数が不正です。")
        print("使用方法:")
        print("  uv run python hotel/hotel_search.py <場所> <YYYY/M/D>  # 新規検索")
        print("  uv run python hotel/hotel_search.py                    # 前回と同じ条件で再検索")
        sys.exit(1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 前回の検索結果を読み込む（比較用）
    prev_names = load_previous_hotel_names(location, date_str)

    print(f"\n=== ホテル検索 ===")
    print(f"場所: {location} / チェックイン: {date_str} / 予算: {BUDGET:,}円以内\n")

    searchers = [
        ("じゃらん", search_jalan),
        ("Booking.com", search_booking),
        ("楽天トラベル", search_rakuten),
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        })

        hotels = []
        used_site = ""

        for site_name, searcher in searchers:
            print(f"[{site_name}]")
            try:
                hotels = await searcher(page, location, date_str)
                if hotels:
                    used_site = site_name
                    print(f"  → {len(hotels)}件見つかりました（{site_name}）\n")
                    break
                else:
                    print(f"  → 結果なし。次のサイトへ。\n")
            except Exception as e:
                print(f"  → エラー: {e}。次のサイトへ。\n")

        await browser.close()

    if not hotels:
        print("すべてのサイトで条件に合うホテルが見つかりませんでした。")
        sys.exit(0)

    # 新規ホテルを特定
    current_names = {h["name"] for h in hotels}
    new_names = current_names - prev_names if prev_names else set()

    # 検索条件を保存（次回の引数なし実行のため）
    save_last_search(location, date_str)

    # 結果表示
    print("=" * 50)
    if prev_names:
        print(f"前回比較: {len(new_names)}件が新規")
        print()

    for i, h in enumerate(hotels, 1):
        is_new = h["name"] in new_names
        label = " [NEW]" if is_new else ""
        print(f"{i}.{label} {h['name']}")
        if h.get("price"):
            print(f"   料金: {h['price']}")
        print(f"   URL: {h['url']}")
        print()

    # ファイル保存
    saved_path = save_results(location, date_str, used_site, hotels, new_names)
    print(f"結果を保存しました: {saved_path}")


if __name__ == "__main__":
    asyncio.run(main())
