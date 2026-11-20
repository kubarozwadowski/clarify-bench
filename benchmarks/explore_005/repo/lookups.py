def find_invoice(invoices, tenant_id, invoice_id):
    for invoice in invoices:
        if invoice["tenant_id"] == tenant_id and invoice["id"] == invoice_id:
            return invoice
    return None


def find_note(notes, tenant_id, note_id):
    for note in notes:
        if note["tenant_id"] == tenant_id and note["id"] == note_id:
            return note
    return None


def find_document(documents, tenant_id, document_id):
    raise NotImplementedError("Add document lookup")
