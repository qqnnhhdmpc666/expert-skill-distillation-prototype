```python
@app.delete("/invoice/{invoice_id}")
def delete_invoice(invoice_id: str, user=Depends(current_user)):
    if not user.is_authenticated:
        raise HTTPException(status_code=401)
    invoice = db.get_invoice(invoice_id)
    db.delete(invoice.id)
    return {"deleted": True, "invoice_id": invoice_id}
```
