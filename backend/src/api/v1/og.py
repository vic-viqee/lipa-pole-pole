from fastapi import APIRouter, Depends, HTTPException, Request

from src.core.deps import get_d1
from src.core.money import to_ksh
from src.db.d1 import D1

router = APIRouter(tags=["Open Graph"])


@router.get("/og/{tracking_token}")
def serve_og(tracking_token: str, request: Request, d1: D1 = Depends(get_d1)):
    plan = d1.query_one(
        "SELECT p.*, v.shop_name AS vendor_name, c.full_name AS customer_name "
        "FROM installment_plans p "
        "JOIN vendors v ON v.id = p.vendor_id "
        "JOIN customers c ON c.id = p.customer_id "
        "WHERE p.tracking_token = ?",
        tracking_token,
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    paid = plan["deposit_paid"] + plan["amount_paid"]
    total = plan["total_price"]
    balance = total - paid
    progress_pct = round((paid / total) * 100) if total > 0 else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta property="og:title" content="Lipa Pole Pole - {plan['product_name']}" />
<meta property="og:description" content="{plan['customer_name']} is paying KSh {to_ksh(total)} for {plan['product_name']} at {plan['vendor_name']}. Paid KSh {to_ksh(paid)} — {progress_pct}% complete." />
<meta property="og:image" content="https://placehold.co/1200x630?text=Lipa+Pole+Pole" />
<meta property="og:url" content="{str(request.url)}" />
<meta property="og:type" content="website" />
<meta name="twitter:card" content="summary_large_image" />
<title>Lipa Pole Pole - {plan['product_name']}</title>
</head>
<body>
<h1>Lipa Pole Pole</h1>
<p>{plan['customer_name']} is paying KSh {to_ksh(total)} for {plan['product_name']} at {plan['vendor_name']}.</p>
<p>Paid: KSh {to_ksh(paid)} ({progress_pct}%) | Balance: KSh {to_ksh(balance)}</p>
</body>
</html>"""
    from fastapi.responses import HTMLResponse

    return HTMLResponse(content=html)
