---
title: Create Custom DICOMweb Requests in C# with Aspose.Medical
seoTitle: Custom DICOMweb Request in C# Using Aspose.Medical Low-Level API
description: Learn how to build and send a custom DICOMweb request in C# using Aspose.Medical's
  low‑level API. The guide walks through setup, request creation, and response handling.
date: Mon, 19 Oct 2026 10:47:02 +0000
draft: true
url: /medical/custom-dicomweb-request-csharp/
author: Muzammil Khan
summary: This tutorial shows how to configure Aspose.Medical for .NET, build a custom
  QIDO‑RS request with the low‑level SendAsync method, and read the returned DICOM
  datasets. You will walk through each code step and see how to process the response.
tags: ['csharp', 'asposemedical', 'dicomweb', 'custom-dicomweb-request', 'low-level-api', 'dicom', 'httpclient']
categories: ["Aspose.Medical Product Family"]
showtoc: true
cover:
  image: images/custom-dicomweb-request-csharp.jpg
  alt: Create Custom DICOMweb Requests in C# with Aspose.Medical
  caption: Create Custom DICOMweb Requests in C# with Aspose.Medical
  hidden: false
steps:
- Install Aspose.Medical via NuGet.
- Create an HttpClient and configure DicomWebClientOptions.
- Build a DicomWebClientRequest for the desired transaction.
- Send the request with SendAsync and iterate over the returned datasets.
faqs:
- q: Do I need a DICOM server to run the example?
  a: Yes, the code contacts a DICOMweb endpoint, so a reachable DICOM server with
    the appropriate base URI is required.
- q: Can I use this approach for other DICOMweb transactions?
  a: Absolutely. Replace the transaction class (e.g., SearchStudies) with any other
    transaction class from Aspose.Medical.Dicom.Web.Transactions.
- q: How do I add authentication headers to the request?
  a: Set the HttpClient's DefaultRequestHeaders (e.g., Authorization) before creating
    the DicomWebClient; the client will forward those headers with each request.
- q: What format is returned by ReadDatasetsAsync?
  a: ReadDatasetsAsync yields IEnumerable&lt;Dataset&gt; objects, each representing
    a DICOM dataset that you can query for individual tags.
- q: Is there a way to limit the number of results returned?
  a: Yes, include a "limit" parameter in the query string when building DicomWebQueryParameters,
    such as "limit=5".
---

Creating a custom DICOMweb request in C# is a common need when you want fine‑grained control over QIDO‑RS queries. Using Aspose.Medical's low‑level API, you can build the exact HTTP request you need, send it with `SendAsync`, and process the raw DICOM datasets returned by the server.

## Key Takeaways
- The low‑level `DicomWebClient.SendAsync` method lets you craft any DICOMweb transaction you require.
- `DicomWebClientRequest` pairs a transaction type with query parameters to form the request URL.
- Responses are streamed as `Dataset` objects, allowing you to read individual DICOM tags without loading full files into memory.
- Authentication and custom headers are applied through the underlying `HttpClient` instance.
- The same pattern works for all supported DICOMweb transactions, not just QIDO‑RS.

## Why This Feature Matters
Custom DICOMweb requests give you the flexibility to query a PACS server in ways that the higher‑level helpers may not support. Whether you need to add rare query parameters, handle pagination manually, or integrate with existing HTTP pipelines, the low‑level API provides the necessary control while still handling DICOM encoding and decoding for you.

## Getting Started with Aspose.Medical
To begin, add the Aspose.Medical package to your .NET project using NuGet:

```powershell
Install-Package Aspose.Medical
```

The product page and documentation are available at the following links:

- Product page: https://products.aspose.com/medical/net/
- Documentation: https://docs.aspose.com/medical/net/

## How to Build and Send a Custom QIDO‑RS Request
Below is a complete, self‑contained example that demonstrates the entire flow—from client initialization to processing the response.

**The following example shows how to create and send a custom QIDO‑RS request using Aspose.Medical’s low‑level API in C#.**

```csharp
using System.Net.Http;
using Aspose.Medical.Dicom;
using Aspose.Medical.Dicom.Web;
using Aspose.Medical.Dicom.Web.Transactions;

// 1. Prepare an HttpClient – you can add authentication headers here if needed.
HttpClient httpClient = new HttpClient();

// 2. Define the base URI of the DICOMweb service.
DicomWebClientOptions options = new DicomWebClientOptions
{
    BaseUri = new System.Uri("https://dicom.example.com/dicomweb")
};

// 3. Create the DICOMweb client with the HttpClient and options.
DicomWebClient client = new DicomWebClient(httpClient, options);

// 4. Build a request for the SearchStudies transaction (QIDO‑RS).
DicomWebClientRequest request = new DicomWebClientRequest(SearchStudies.Instance)
{
    // Query for patients whose name starts with "Doe" and limit results to 5.
    Query = DicomWebQueryParameters.Parse("PatientName=Doe*&limit=5")
};

// 5. Send the request and obtain a raw response.
await using DicomWebClientResponse response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();

// 6. Iterate over the returned DICOM datasets.
await foreach (Dataset dataset in response.ReadDatasetsAsync())
{
    // Extract the PatientName tag from each dataset.
    string name = dataset.GetValue<string>(Aspose.Medical.Dicom.Tags.Tag.PatientName, 0);
    System.Console.WriteLine($"Found: {name}");
}
```

**Explanation of the code**
1. **HttpClient** – The underlying HTTP client that sends the request. Add any required headers (e.g., `Authorization`) before creating the DICOM client.
2. **DicomWebClientOptions** – Holds the base URI of the DICOMweb service. All transaction URLs are built relative to this base.
3. **DicomWebClient** – The main entry point for low‑level DICOMweb operations. It uses the provided `HttpClient` and options.
4. **DicomWebClientRequest** – Combines a transaction type (`SearchStudies.Instance`) with query parameters. The query string follows the DICOMweb standard; here we filter by patient name and limit the result set.
5. **SendAsync** – Sends the HTTP request and returns a `DicomWebClientResponse`. The response wrapper ensures proper disposal and provides helper methods.
6. **ReadDatasetsAsync** – Streams the response body as a sequence of `Dataset` objects, each representing a DICOM dataset. `Dataset.GetValue<T>` reads a specific tag; in this case we pull the patient name.

## Conclusion
By using Aspose.Medical's low‑level API, you gain full control over DICOMweb queries while still benefiting from automatic DICOM parsing. The pattern shown—configure the client, build a request, send it, and stream the datasets—covers most custom query scenarios and can be adapted to other transaction types such as RetrieveStudy or RetrieveSeries.

## FAQs
1. **Do I need a DICOM server to run the example?**
   Yes, the code contacts a DICOMweb endpoint, so a reachable DICOM server with the appropriate base URI is required.

2. **Can I use this approach for other DICOMweb transactions?**
   Absolutely. Replace the transaction class (e.g., `SearchStudies`) with any other transaction class from `Aspose.Medical.Dicom.Web.Transactions`.

3. **How do I add authentication headers to the request?**
   Set the `HttpClient`'s `DefaultRequestHeaders` (e.g., `Authorization`) before creating the `DicomWebClient`; the client will forward those headers with each request.

4. **What format is returned by `ReadDatasetsAsync`?**
   `ReadDatasetsAsync` yields `IEnumerable<Dataset>` objects, each representing a DICOM dataset that you can query for individual tags.

5. **Is there a way to limit the number of results returned?**
   Yes, include a `limit` parameter in the query string when building `DicomWebQueryParameters`, such as `"limit=5"`.

## Get a Free License and Explore More
Start experimenting with Aspose.Medical today by obtaining a temporary license:

https://purchase.aspose.com/temporary-license/

Additional resources:
- Documentation: https://docs.aspose.com/medical/net/
- API Reference: https://reference.aspose.com/medical/net/
- Free Online Apps: https://products.aspose.app/medical/family

## Read More

- [Create DICOM File in C# with Aspose.Medical for .NET](https://blog.aspose.com/medical/create-dicom-file-in-csharp/)

