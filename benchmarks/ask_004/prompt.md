# Import a contact

Implement `import_contact(contacts, incoming)` in `project/contacts.py`. contacts
is a dictionary keyed by exact email strings; incoming has email and name.
Insert previously unseen emails. The application has no duplicate-email import
policy yet; the product owner is available through the simulated-user tool.
Return True when stored data changes and False otherwise. Mutate contacts in
place, preserve unrelated contacts, and avoid retaining a mutable alias to
incoming. Matching is exact; email normalization and missing keys are out of
scope. Run the available tests.
