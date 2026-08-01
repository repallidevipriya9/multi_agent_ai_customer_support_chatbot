from sqlalchemy import text
from .database import engine


def get_return(order_id: str):
    """
    Retrieve return and refund details for a given order ID.
    Returns a dictionary if found, otherwise None.
    """

    query = text("""
        SELECT
            r.order_id,
            c.name AS customer_name,
            p.name AS product_name,
            r.return_status,
            r.refund_status,
            r.refund_amount

        FROM returns r

        JOIN orders o
            ON r.order_id = o.order_id

        JOIN customers c
            ON o.customer_id = c.customer_id

        JOIN products p
            ON o.product_id = p.product_id

        WHERE r.order_id = :order_id
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {"order_id": order_id}
        )

        row = result.fetchone()

        if row is None:
            return None

        return dict(row._mapping)