from sqlalchemy import text
from .database import engine


def get_order(order_id: str):

    query = text("""
        SELECT
            o.order_id,
            c.name AS customer_name,
            p.name AS product_name,
            o.order_status,
            o.payment_status,
            o.courier_partner,
            o.tracking_number,
            o.expected_delivery
        FROM orders o
        JOIN customers c
            ON o.customer_id = c.customer_id
        JOIN products p
            ON o.product_id = p.product_id
        WHERE o.order_id = :order_id
    """)

    with engine.connect() as conn:

        result = conn.execute(query, {"order_id": order_id})

        row = result.fetchone()

        if row is None:
            return None

        return dict(row._mapping)