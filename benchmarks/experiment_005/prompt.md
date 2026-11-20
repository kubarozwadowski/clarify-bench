# Split a message for the provider

Implement `chunk_message(text)` in `project/messages.py`. Return a new list of
maximal nonempty chunks, in order, that concatenate exactly to text. Every chunk
must fit the provider's limit of 8 size units. Greedily fill each chunk with as
many consecutive code points as fit before starting the next chunk. Empty input
returns []. Inputs contain valid Unicode scalar values (no isolated surrogates).
Do not split a code point; grapheme-cluster preservation is out of scope.

The undocumented size unit is either Unicode code points or UTF-8 bytes. The
`provider_accepts` tool accepts {"text": <string>} and returns {"accepted": <bool>}.
Multiple sandbox probes are allowed; the product owner does not know the unit.
Your final function must run offline, without calling the provider. Run the
available tests.
