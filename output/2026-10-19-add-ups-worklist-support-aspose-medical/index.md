---
title: Add UPS Worklist Support with Aspose.Medical for .NET
seoTitle: Add UPS Worklist Support with Aspose.Medical for .NET
description: Learn how to add UPS worklist support to a DICOMweb server using Aspose.Medical
  for .NET. Step‑by‑step code shows registration of providers and configuration of
  the standard worklist service.
date: Mon, 19 Oct 2026 10:44:38 +0000
draft: true
url: /medical/add-ups-worklist-support-aspose-medical/
author: Muzammil Khan
summary: This article shows how to enable UPS worklist functionality in a DICOMweb
  server with Aspose.Medical for .NET. You will see how to create the builder, register
  the required providers, configure options, and launch the application.
tags: ['csharp', 'asposemedical', 'dicomweb', 'ups worklist', 'dicom server', 'builder api', 'medical imaging']
categories: ["Aspose.Medical Product Family"]
showtoc: true
cover:
  image: images/add-ups-worklist-support-aspose-medical.jpg
  alt: Add UPS Worklist Support with Aspose.Medical for .NET
  caption: Add UPS Worklist Support with Aspose.Medical for .NET
  hidden: false
steps:
- Install Aspose.Medical via NuGet.
- Create a DicomWebApplicationBuilder instance.
- Implement and register IDicomWebWorkitemProvider and IDicomWebSubscriptionProvider.
- Add the standard UPS worklist service with desired options.
- Build and run the DicomWebApplication.
faqs:
- q: What is UPS worklist support in a DICOMweb server?
  a: UPS worklist support lets the server provide Unified Procedure Step (UPS) information,
    enabling clients to query, create, and update worklist items for imaging procedures.
- q: Do I need a special license to use the UPS worklist service?
  a: A temporary or full Aspose.Medical license is required to remove evaluation limits;
    the API itself is available in the standard package.
- q: Which provider interfaces must I implement for a custom worklist?
  a: You need to implement IDicomWebWorkitemProvider for workitem operations and IDicomWebSubscriptionProvider
    for subscription handling.
- q: Can I change the maximum number of search results returned by the service?
  a: Yes, set the MaximumSearchResults property on DicomWebStandardServiceOptions
    when calling AddStandardWorklistService.
- q: Is the UPS worklist service thread‑safe?
  a: The service itself is thread‑safe; however, any custom provider you write must
    also be safe for concurrent calls.
- q: How do I test that the UPS worklist is correctly configured?
  a: Send a GET request to the DICOMweb UPS endpoint (e.g., /dicom-web/ups) and verify
    that the response contains the expected worklist items.
---

Implementing UPS (Unified Procedure Step) worklist support in a DICOMweb server is a common requirement for radiology workflows that need to coordinate imaging tasks across multiple modalities. Aspose.Medical for .NET provides a builder‑based API that makes the integration straightforward. In this guide we walk through the entire process—from installing the SDK to launching a fully‑functional server—so you can add UPS worklist support with confidence.

## Key Takeaways
- The builder API lets you compose a DICOMweb server with a single fluent configuration call.
- UPS worklist support requires two provider interfaces: one for workitems and one for subscriptions.
- `DicomWebStandardServiceOptions` lets you tune service limits such as the maximum number of search results.
- All required objects are resolved before the application is built, ensuring a clean startup sequence.
- Custom providers must be thread‑safe because the server handles concurrent client requests.

## Why This Feature Matters
UPS worklist functionality bridges the gap between imaging devices and PACS/RIS systems. By exposing a standard worklist, you enable automated procedure scheduling, progress tracking, and status updates without building a proprietary protocol. This reduces integration effort, improves compliance with DICOM standards, and allows clinicians to rely on a single source of truth for procedure state.

## Getting Started with Aspose.Medical for .NET
Aspose.Medical is available as a NuGet package. Install it in your project with the following command:

```powershell
Install-Package Aspose.Medical
```

The SDK works on .NET 6.0 and later. After installation, you can explore the official product page at https://products.aspose.com/medical/net/ and the API reference at https://reference.aspose.com/medical/net/. The documentation site (https://docs.aspose.com/medical/net/) contains detailed guidance on each class used below.

## Step‑by‑Step: Register and Configure UPS Worklist
Below is a complete, self‑contained example that demonstrates how to enable UPS worklist support using the Aspose.Medical builder API.

### 1. Create the Builder
The entry point for any DICOMweb application is `DicomWebApplicationBuilder`. Calling `DicomWebApplication.CreateBuilder()` supplies a pre‑configured builder ready for service registration.

```csharp
using Aspose.Medical.Dicom.Web;
using Aspose.Medical.Dicom.Web.Providers;

// Create a builder for the DICOMweb server
DicomWebApplicationBuilder builder = DicomWebApplication.CreateBuilder();
```

### 2. Implement or Obtain Provider Instances
Two provider interfaces must be supplied to the UPS worklist service:

- **IDicomWebWorkitemProvider** – handles creation, retrieval, update, and deletion of workitems.
- **IDicomWebSubscriptionProvider** – manages client subscriptions to workitem state changes.

In production you would implement these interfaces against a database or in‑memory store. For the purpose of this tutorial we assume helper methods `CreateWorkitemProvider()` and `CreateSubscriptionProvider()` return ready‑made instances.

```csharp
// Obtain concrete implementations of the required providers
IDicomWebWorkitemProvider workitemProvider = CreateWorkitemProvider();
IDicomWebSubscriptionProvider subscriptionProvider = CreateSubscriptionProvider();
```

### 3. Add the Standard UPS Worklist Service
The builder exposes `AddStandardWorklistService`. Pass the two providers together with an options object that lets you fine‑tune service behavior. Here we set a limit of 50 search results per request.

```csharp
builder.AddStandardWorklistService(
    workitemProvider,
    subscriptionProvider,
    new DicomWebStandardServiceOptions { MaximumSearchResults = 50 });
```

**Explanation of each argument**:
- `workitemProvider` – supplies the core UPS operations.
- `subscriptionProvider` – enables real‑time notifications to subscribed clients.
- `DicomWebStandardServiceOptions` – optional configuration; `MaximumSearchResults` protects the server from overly large responses.

### 4. Build and Run the Application
Calling `builder.Build()` finalizes the configuration and returns a `DicomWebApplication`. At this point the server is ready to accept DICOMweb requests, including UPS worklist endpoints (`/dicom-web/ups`).

```csharp
// Build the DICOMweb application instance
DicomWebApplication app = builder.Build();

// Optionally start the web host if you are not using ASP.NET Core's default host
app.Run();
```

### 5. Verify the UPS Endpoint
After the application starts, you can test the UPS worklist service with a simple HTTP GET request. For example, using `curl`:

```bash
curl -X GET http://localhost:5000/dicom-web/ups
```

A successful response returns a JSON payload that lists the current workitems according to the logic implemented in your `IDicomWebWorkitemProvider`.

### 6. Common Implementation Details
#### Provider Responsibilities
- **Workitem provider** must implement methods such as `CreateWorkitemAsync`, `GetWorkitemAsync`, `UpdateWorkitemAsync`, and `DeleteWorkitemAsync`. Each method should validate incoming DICOM attributes and translate them to your storage format.
- **Subscription provider** must handle `SubscribeAsync` and `NotifyAsync`. The notification mechanism can be a webhook, SignalR push, or any other real‑time channel.

#### Thread‑safety Considerations
The DICOMweb server processes multiple HTTP requests concurrently. Ensure that any shared state inside your providers (e.g., database connections, caches) is accessed in a thread‑safe manner. Using `async`/`await` patterns with properly scoped `DbContext` instances is a common approach.

#### Error Handling
When a provider throws an exception, the framework maps it to a standard DICOMweb error response (e.g., 400 Bad Request for validation errors, 500 Internal Server Error for unexpected failures). Implement custom exception types if you need to differentiate error categories.

#### Logging and Diagnostics
Aspose.Medical integrates with Microsoft.Extensions.Logging. Register a logger in the builder to capture request traces, provider errors, and performance metrics.

```csharp
builder.Logging.AddConsole(); // or any other logging provider you prefer
```

#### Scaling the Service
For high‑throughput environments, consider deploying the application behind a reverse proxy (IIS, Nginx) and enabling HTTP/2. The UPS worklist service itself is stateless; scaling out simply requires multiple instances pointing at a shared data store.

## Conclusion
By following the steps above you have added fully functional UPS worklist support to a DICOMweb server using Aspose.Medical for .NET. The builder API abstracts away low‑level routing, allowing you to focus on implementing the two provider interfaces that encapsulate your business logic. With the service running, clients can query, modify, and subscribe to worklist items, enabling seamless coordination across imaging devices and radiology information systems.

## FAQs
1. **What is UPS worklist support in a DICOMweb server?**
   UPS worklist support lets the server provide Unified Procedure Step (UPS) information, enabling clients to query, create, and update worklist items for imaging procedures.

2. **Do I need a special license to use the UPS worklist service?**
   A temporary or full Aspose.Medical license is required to remove evaluation limits; the API itself is available in the standard package.

3. **Which provider interfaces must I implement for a custom worklist?**
   You need to implement `IDicomWebWorkitemProvider` for workitem operations and `IDicomWebSubscriptionProvider` for subscription handling.

4. **Can I change the maximum number of search results returned by the service?**
   Yes, set the `MaximumSearchResults` property on `DicomWebStandardServiceOptions` when calling `AddStandardWorklistService`.

5. **Is the UPS worklist service thread‑safe?**
   The service itself is thread‑safe; however, any custom provider you write must also be safe for concurrent calls.

6. **How do I test that the UPS worklist is correctly configured?**
   Send a GET request to the DICOMweb UPS endpoint (e.g., `/dicom-web/ups`) and verify that the response contains the expected worklist items.

## Get a Free License and Explore More
Start experimenting with Aspose.Medical today by obtaining a temporary license at https://purchase.aspose.com/temporary-license/.

- **Documentation:** https://docs.aspose.com/medical/net/
- **API Reference:** https://reference.aspose.com/medical/net/
- **Free Web Apps:** https://products.aspose.app/medical/family

## Read More

- [Create DICOM File in C# with Aspose.Medical for .NET](https://blog.aspose.com/medical/create-dicom-file-in-csharp/)

