from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.plan import InstallmentPlan

router = APIRouter(tags=["OG"])

OG_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{url}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{description}" />
  <meta http-equiv="refresh" content="0;url={redirect_url}" />
</head>
<body>
  <script>window.location.href = "{redirect_url}";</script>
</body>
</html>"""


@router.get("/og/track/{tracking_token}", response_class=HTMLResponse)
def og_tracking_page(tracking_token: str, request: Request, db: Session = Depends(get_db)):
    """Serve OG meta tags for social sharing of tracking links"""
    plan = db.query(InstallmentPlan).filter(
        InstallmentPlan.tracking_token == tracking_token
    ).first()
    if not plan:
        return HTMLResponse(
            OG_TEMPLATE.format(
                title="Payment Plan Not Found",
                description="This tracking link is invalid. Please check with your vendor.",
                url=str(request.url),
                redirect_url=f"{request.base_url}track/{tracking_token}",
            ),
            status_code=200,
        )

    vendor = plan.customer.vendor
    customer = plan.customer
    base_url = str(request.base_url).rstrip("/")
    redirect_url = f"{base_url}/track/{tracking_token}"

    paid = float(plan.deposit_paid) + float(plan.amount_paid)
    balance = float(plan.total_price) - paid
    pct = min(round((paid / float(plan.total_price)) * 100), 100) if float(plan.total_price) > 0 else 0

    title = f"Payment Plan - {vendor.shop_name}"
    description = (
        f"{customer.full_name} · {plan.product_name} · "
        f"KSh {balance:,.0f} remaining ({pct}% paid) · "
        f"Pay via M-Pesa"
    )

    return HTMLResponse(
        OG_TEMPLATE.format(
            title=title,
            description=description,
            url=str(request.url),
            redirect_url=redirect_url,
        ),
        status_code=200,
    )
