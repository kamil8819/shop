import os
import json
import urllib.request
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(title="3D Print Telegram Shop")

SHOP_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN = "8744417186:AAFdvQ0GT_Tosi_0r7Dp64vJdihLj5pEDj0"
OWNER_CHAT_ID = "496029586"

# Статика (изображения, стили, скрипты)
app.mount("/images", StaticFiles(directory=os.path.join(SHOP_DIR, "images")), name="images")

@app.get("/")
async def serve_shop():
    return FileResponse(os.path.join(SHOP_DIR, "index.html"))

@app.get("/products.json")
async def get_products():
    return FileResponse(os.path.join(SHOP_DIR, "products.json"))

def notify_owner_telegram(order_data: dict):
    """Отправляет уведомление о новом заказе владельцу в Telegram"""
    try:
        cust = order_data.get("customer", {})
        deliv = order_data.get("delivery", {})
        items = order_data.get("items", [])
        total = order_data.get("totalSum", 0)

        items_text = "\n".join([
            f"  • <b>{it.get('title')}</b> ({it.get('option', 'Стандарт')}) — {it.get('qty', 1)} шт. x {it.get('sum', 0):,} ₽"
            for it in items
        ])

        msg = (
            f"🛍 <b>НОВЫЙ ЗАКАЗ ИЗ МАГАЗИНА 3D-ПЕЧАТИ!</b>\n\n"
            f"👤 <b>Клиент:</b> {cust.get('name', 'Не указано')}\n"
            f"📞 <b>Связь:</b> {cust.get('contact', 'Не указано')}\n"
            f"🚚 <b>Доставка Ozon:</b> {deliv.get('address', 'Не указан')}\n\n"
            f"📦 <b>Состав заказа:</b>\n{items_text}\n\n"
            f"💰 <b>ИТОГО К ОПЛАТЕ:</b> <b>{total:,} ₽</b>\n"
            f"⏰ <i>{order_data.get('date', '')}</i>"
        )

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": OWNER_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }

        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"), 
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[SHOP] Заказ отправлен владельцу ({resp.status})")
            return True
    except Exception as e:
        print(f"[SHOP ERROR] Ошибка отправки заказа в Telegram: {e}")
        return False

@app.post("/api/order")
async def create_order(request: Request):
    try:
        data = await request.json()
        print(f"[SHOP] Получен новый заказ: {data}")
        notify_owner_telegram(data)
        return {"status": "ok", "message": "Заказ успешно принят!"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

if __name__ == "__main__":
    import uvicorn
    print("[SHOP] Запуск сервера магазина на http://127.0.0.1:8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
