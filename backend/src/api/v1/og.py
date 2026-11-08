from core.deps import get_d1
from core.money import to_ksh
from core.router import HTTPException, Router, html_response
from db.d1 import D1

router = Router(prefix="/api/v1/og")


@router.get("/view/{tracking_token}")
async def serve_og(request, env, params):
    tracking_token = params["tracking_token"]
    d1: D1 = get_d1(env)

    plan = await d1.query_one(
        "SELECT p.*, v.shop_name AS vendor_name, c.full_name AS customer_name "
        "FROM installment_plans p "
        "JOIN vendors v ON v.id = p.vendor_id "
        "JOIN customers c ON c.id = p.customer_id "
        "WHERE p.tracking_token = ?",
        tracking_token,
    )
    if not plan:
        raise HTTPException(404, "Plan not found")

    paid = plan["deposit_paid"] + plan["amount_paid"]
    total = plan["total_price"]
    balance = total - paid
    progress_pct = round((paid / total) * 100) if total > 0 else 0

    url = str(request.url)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta property="og:title" content="Lipa Pole Pole - {plan['product_name']}" />
<meta property="og:description" content="{plan['customer_name']} is paying KSh {to_ksh(total)} for {plan['product_name']} at {plan['vendor_name']}. Paid KSh {to_ksh(paid)} — {progress_pct}% complete." />
<meta property="og:image" content="https://placehold.co/1200x630?text=Lipa+Pole+Pole" />
<meta property="og:url" content="{url}" />
<meta property="og:type" content="website" />
<meta name="twitter:card" content="summary_large_image" />
<title>Lipa Pole Pole - {plan['product_name']}</title>
</head>
<body>
<h1>Lipa Pole Pole</h1>
<p>{plan['customer_name']} is paying KSh {to_ksh(total)} for {plan['product_name']} at {plan['vendor_name']}.</p>
<p>Paid: KSh {to_ksh(paid)} ({progress_pct}%) | Balance: KSh {to_ksh(balance)}</p>
<footer style="margin-top:2em;font-size:0.85em;color:#666;border-top:1px solid #ddd;padding-top:1em">
  Designed &amp; Developed by <a href="https://viqsystems.tech" target="_blank" rel="noopener noreferrer">Viq Systems</a>
</footer>
</body>
</html>"""
    origin = request.headers.get("Origin") if hasattr(request, "headers") else None
    return html_response(html, origin=origin)
