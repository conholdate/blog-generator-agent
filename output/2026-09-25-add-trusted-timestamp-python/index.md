---
title: Add Trusted Timestamp to Digital Signature in Python
seoTitle: Add Trusted Timestamp to Digital Signature in Python
description: Add a trusted timestamp to a digital signature in Python using Aspose.Words,
  configuring SignOptions and DigitalSignatureTimestampSettings for secure documents.
date: Fri, 25 Sep 2026 04:49:05 +0000
draft: true
url: /words/add-trusted-timestamp-python/
author: Muzammil Khan
summary: This tutorial shows how to embed a trusted timestamp into a DOCX digital
  signature using Aspose.Words for Python. You will learn the required API calls,
  how to configure the timestamp authority, and how to verify the result.
tags: ['add trusted timestamp to digital signature in python', 'digital signature timestamping using python', 'how to add trusted timestamp to a signed document in python', 'python library for trusted timestamp in digital signatures']
categories: ["Aspose.Words Product Family"]
showtoc: true
cover:
  image: images/add-trusted-timestamp-python.jpg
  alt: Add Trusted Timestamp to Digital Signature in Python
  caption: Add Trusted Timestamp to Digital Signature in Python
  hidden: false
steps:
- Install Aspose.Words for Python via pip.
- Create a SignOptions object and set XmlDsigLevel to XAdES‑T.
- Configure DigitalSignatureTimestampSettings with your TSA server credentials.
- Load the signing certificate and call DigitalSignatureUtil.sign.
- Validate that the signature and timestamp were applied correctly.
faqs:
- q: What does a trusted timestamp add to a digital signature?
  a: A trusted timestamp proves that the signature existed at a specific point in
    time, protecting it against later key compromise.
- q: Do I need a certificate authority to use the timestamp feature?
  a: You need a signing certificate for the document and a timestamp authority (TSA)
    URL; the TSA does not require a separate certificate.
- q: Which XmlDsigLevel value enables timestamping?
  a: Set SignOptions.xml_dsig_level to XmlDsigLevel.X_AD_ES_T to request an XAdES‑T
    signature that includes a timestamp.
- q: Can I use a custom timeout for the TSA request?
  a: Yes, DigitalSignatureTimestampSettings accepts a timeout argument; the default
    is 100 seconds.
- q: Is timestamping supported for formats other than DOCX?
  a: Aspose.Words applies digital signatures to all WordProcessing formats it supports,
    and the timestamping options work across them.
- q: How do I verify that the timestamp was applied?
  a: After signing, load the document and check signed_doc.digital_signatures[0].timestamp.time_stamp
    exists and is valid.
---

Adding a trusted timestamp to a digital signature strengthens the legal standing of your Word documents. In Python, Aspose.Words provides a straightforward API that lets you configure the timestamp authority, embed the timestamp, and verify the result—all without leaving the language.

## Key Takeaways
- A trusted timestamp guarantees the signing time of a document, mitigating future key compromise.
- Aspose.Words for Python uses `SignOptions` and `DigitalSignatureTimestampSettings` to embed timestamps.
- The `XmlDsigLevel.X_AD_ES_T` enum value activates XAdES‑T, the format that carries the timestamp.
- You only need a signing certificate and a reachable TSA URL; the SDK handles the protocol details.
- Validation can be performed programmatically after the signing operation.

## Why Add Trusted Timestamp to Digital Signature?
A trusted timestamp provides a cryptographically secure proof of when a document was signed. This proof is crucial for compliance, audit trails, and scenarios where the signing key might be revoked later. Embedding the timestamp directly into the signature binds the time to the document, making it immutable.

## Getting Started with Aspose.Words for Python
Aspose.Words for Python is a fully managed library that works on any platform supporting Python 3. Install it via pip and you are ready to start:

```bash
pip install aspose-words
```

The product page and full documentation are available at the following links:
- Product page: https://products.aspose.com/words/python-net/
- Docs: https://docs.aspose.com/words/python-net/
- API reference: https://reference.aspose.com/words/python/

## Understanding Timestamping Options
Aspose.Words separates the signature configuration (`SignOptions`) from the timestamp configuration (`DigitalSignatureTimestampSettings`).

- **`SignOptions.xml_dsig_level`** – Determines the XML‑DSig profile. The enum `XmlDsigLevel.X_AD_ES_T` requests an XAdES‑T signature, which is the standard for timestamped signatures.
- **`DigitalSignatureTimestampSettings`** – Holds the TSA URL, optional credentials, and a timeout. These settings are attached to `SignOptions.timestamp_settings`.

Choosing the correct `XmlDsigLevel` is essential; other levels (e.g., `XAdES‑B`) do not include a timestamp.

## How to Configure Timestamp Settings
The first concrete step is to build the timestamp settings object and attach it to the signature options.

1. Create a `SignOptions` instance.
2. Set `xml_dsig_level` to `XmlDsigLevel.X_AD_ES_T`.
3. Instantiate `DigitalSignatureTimestampSettings` with the TSA endpoint, optional user name, and password.
4. Assign the timestamp settings to `sign_options.timestamp_settings`.

The following example demonstrates this configuration:

The following example shows how to configure timestamp settings using Aspose.Words for Python.

```python
import aspose.words as aw
import datetime

# Prepare the Signing Options
sign_options = aw.digitalsignatures.SignOptions()
# Request an XAdES‑T Signature (Timestamped)
sign_options.xml_dsig_level = aw.digitalsignatures.XmlDsigLevel.X_AD_ES_T

# Configure the Timestamp Authority (TSA)
sign_options.timestamp_settings = aw.digitalsignatures.DigitalSignatureTimestampSettings(
    server_url="https://freetsa.org/tsr",
    user_name="JohnDoe",
    password="MyPassword"
)

# Optional: Change the Default Timeout (Default Is 100 Seconds)
sign_options.timestamp_settings.timeout = datetime.timedelta(minutes=30)
```

**Explanation**
- `SignOptions()` creates the container for all signature‑related settings.
- Setting `xml_dsig_level` to `X_AD_ES_T` tells the SDK to produce a timestamped signature.
- `DigitalSignatureTimestampSettings` points to a public TSA (`https://freetsa.org/tsr`). If the TSA requires authentication, supply `user_name` and `password`.
- The `timeout` property controls how long the SDK waits for the TSA response before aborting.

## How to Sign the Document with a Trusted Timestamp
With the timestamp settings ready, the next step is to sign the Word document using a certificate.

1. Load the signing certificate (`.pfx` file) via `CertificateHolder.create`.
2. Call `DigitalSignatureUtil.sign`, passing source and destination paths, the certificate holder, and the prepared `sign_options`.
3. Open the signed document to confirm that a signature exists and is valid.

The code below puts these steps together:

The following example demonstrates signing a DOCX file with a trusted timestamp.

```python
# Load the Signing Certificate (Replace the Path and Password as Needed)
cert = aw.digitalsignatures.CertificateHolder.create(
    file_name=MY_DIR + "morzal.pfx",
    password="aw"
)

# Perform the Signing Operation. the Destination File Will Contain the Timestamp.
aw.digitalsignatures.DigitalSignatureUtil.sign(
    src_file_name=MY_DIR + "Digitally signed.docx",
    dst_file_name=ARTIFACTS_DIR + "DigitalSignatureUtil.Timestamped.docx",
    cert_holder=cert,
    sign_options=sign_options
)

# Load the Signed Document to Verify the Signature and Timestamp.
signed_doc = aw.Document(file_name=ARTIFACTS_DIR + "DigitalSignatureUtil.Timestamped.docx")

# Basic Sanity Checks – These Assertions Illustrate the Expected State.
assert signed_doc.digital_signatures.count == 1
assert signed_doc.digital_signatures[0].is_valid
# The Timestamp Settings Object Still Holds the TSA Details for Reference.
assert sign_options.timestamp_settings.server_url == "https://freetsa.org/tsr"
assert sign_options.timestamp_settings.user_name == "JohnDoe"
```

**Explanation**
- `CertificateHolder.create` loads the PKCS#12 certificate used for signing.
- `DigitalSignatureUtil.sign` writes a new DOCX file (`Timestamped.docx`) that contains the XAdES‑T signature.
- After signing, the `Document` object exposes the `digital_signatures` collection; a count of `1` confirms that a signature was created.
- The `is_valid` property verifies the cryptographic integrity of the signature and the embedded timestamp.

## Verifying the Timestamp and Signature Validity
Beyond the simple `assert` checks shown above, you can inspect the timestamp details directly:

```python
signature = signed_doc.digital_signatures[0]
if signature.timestamp is not None:
    print("Timestamp URL:", signature.timestamp.tsa_url)
    print("Timestamp time:", signature.timestamp.time)
```

- `signature.timestamp.tsa_url` returns the TSA endpoint used during signing.
- `signature.timestamp.time` provides the exact UTC time the TSA asserted.
- If `timestamp` is `None`, the signature was created without a TSA or the TSA response was invalid.

## Common Pitfalls and How to Avoid Them
| Symptom | Cause | Remedy |
|---|---|---|
| `DigitalSignatureUtil.sign` throws a network‑related exception | TSA URL unreachable or blocked by firewall | Verify connectivity to the TSA endpoint and ensure the server URL uses HTTPS. |
| `sign_options.timestamp_settings.timeout` is too short | Large documents cause the TSA request to exceed the timeout | Increase the timeout (e.g., `datetime.timedelta(minutes=5)`). |
| Signature appears but `is_valid` is `False` | Incorrect or expired signing certificate | Use a valid, non‑expired `.pfx` file and ensure the password is correct. |
| Timestamp not present in the signature | `xml_dsig_level` not set to `X_AD_ES_T` | Set `sign_options.xml_dsig_level = XmlDsigLevel.X_AD_ES_T` before signing. |

Addressing these issues early saves time and ensures that the final document meets compliance requirements.

## Conclusion
By configuring `SignOptions` with `XmlDsigLevel.X_AD_ES_T` and providing a `DigitalSignatureTimestampSettings` instance, you can embed a trusted timestamp into any Word document using Aspose.Words for Python. The process involves installing the library, setting up the timestamp authority, loading a signing certificate, and invoking `DigitalSignatureUtil.sign`. After signing, the SDK lets you verify both the signature and the attached timestamp, offering a complete, programmatic workflow for secure, time‑bound documents.

## FAQs
1. **What does a trusted timestamp add to a digital signature?**
   A trusted timestamp proves that the signature existed at a specific point in time, protecting it against later key compromise.
2. **Do I need a certificate authority to use the timestamp feature?**
   You need a signing certificate for the document and a timestamp authority (TSA) URL; the TSA does not require a separate certificate.
3. **Which XmlDsigLevel value enables timestamping?**
   Set `SignOptions.xml_dsig_level` to `XmlDsigLevel.X_AD_ES_T` to request an XAdES‑T signature that includes a timestamp.
4. **Can I use a custom timeout for the TSA request?**
   Yes, `DigitalSignatureTimestampSettings` accepts a `timeout` argument; the default is 100 seconds.
5. **Is timestamping supported for formats other than DOCX?**
   Aspose.Words applies digital signatures to all WordProcessing formats it supports, and the timestamping options work across them.
6. **How do I verify that the timestamp was applied?**
   After signing, load the document and check `signed_doc.digital_signatures[0].timestamp` for TSA details and a valid time value.

## Get a Free License and Explore More
You can request a temporary free license to evaluate Aspose.Words for Python without restrictions.

- [Free Temporary License](https://purchase.aspose.com/temporary-license/)
- [Documentation](https://docs.aspose.com/words/python-net/)
- [API Reference](https://reference.aspose.com/words/python/)
- [Free Online Apps](https://products.aspose.app/words/family)

