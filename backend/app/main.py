from fastapi import FastAPI, HTTPException

from .order_service import get_order
from .return_service import get_return

app = FastAPI(
    title="Customer Support API",
    version="1.0.0",
    description="Customer Support APIs for Order Tracking and Return/Refund Status"
)


@app.get("/")
def root():
    return {
        "message": "Customer Support API Running"
    }


@app.get("/support/order/{order_id}")
def get_order_details(order_id: str):

    order = get_order(order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order


@app.get("/support/return/{order_id}")
def get_return_details(order_id: str):

    return_details = get_return(order_id)

    if return_details is None:
        raise HTTPException(
            status_code=404,
            detail="Return record not found"
        )

    return return_details