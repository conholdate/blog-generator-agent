---
title: Receive UPS Notifications via Aspose.Medical WebSocket in C#
seoTitle: Receive UPS Notifications with Aspose.Medical WebSocket API (C#)
description: Learn how to subscribe to worklist notifications and receive UPS events
  using Aspose.Medical's WebSocket API in C#. It runs in minutes.
date: Mon, 19 Oct 2026 10:54:33 +0000
draft: true
url: /medical/receive-ups-notifications-csharp/
author: Muzammil Khan
summary: This tutorial shows how to use Aspose.Medical's DICOM Web client to subscribe
  to worklist notifications and open a WebSocket connection that streams real‑time
  UPS events. A complete C# example walks you through each API call.
tags: ['csharp', 'aspnet', 'asposemedical', 'dicom websocket', 'ups notifications', 'real-time notifications', 'dicom worklist', 'websocket api']
categories: ["Aspose.Medical Product Family"]
showtoc: true
cover:
  image: images/receive-ups-notifications-csharp.jpg
  alt: Receive UPS Notifications via Aspose.Medical WebSocket in C#
  caption: Receive UPS Notifications via Aspose.Medical WebSocket in C#
  hidden: false
steps:
- Install Aspose.Medical via NuGet.
- Create a DicomWebClient and configure the base URI.
- Subscribe to worklist notifications with SubscribeWorklistAsync.
- Connect to the UPS notification WebSocket and handle incoming messages.
faqs:
- q: What is a UPS notification in Aspose.Medical?
  a: A UPS (Update Service) notification is a real‑time message sent over a WebSocket
    when a DICOM worklist changes, allowing clients to react immediately.
- q: Do I need a DICOM server to receive UPS notifications?
  a: Yes, the client connects to a DICOMweb endpoint that implements the UPS notification
    service.
- q: Which .NET namespaces contain the required classes?
  a: The APIs reside in Aspose.Medical.Dicom and Aspose.Medical.Dicom.Web namespaces.
- q: How can I handle multiple notifications efficiently?
  a: Use an asynchronous loop with ReceiveAsync and process each Dataset as it arrives,
    keeping the connection open for the server's lifetime.
- q: Is there a way to filter which UPS events I receive?
  a: The API delivers all notifications for the subscribed AE title; you can filter
    them in your code after they are received.
- q: Can I use this API in .NET Core or .NET Framework?
  a: Aspose.Medical targets .NET Standard, so it works with both .NET Framework and
    .NET Core/.NET 5+ projects.
---

Aspose.Medical introduces a WebSocket‑based UPS (Update Service) notification channel that lets .NET applications listen for real‑time worklist changes. In this guide you’ll learn how to subscribe to worklist notifications and receive UPS events using the Aspose.Medical DICOM Web client in C#.

## Key Takeaways
- Subscribing to worklist notifications creates a session that can be used for real‑time UPS events.
- The WebSocket connection is managed through `DicomWebNotificationConnection` and delivers `Dataset` objects.
- All required classes live in the `Aspose.Medical.Dicom.Web` namespace, and the library works with .NET Standard.
- A short asynchronous loop is enough to continuously process incoming UPS messages.

## Why Receive UPS Notifications?
Receiving UPS notifications eliminates the need for periodic polling of a DICOM worklist. When a new study or patient arrives, the server pushes a notification instantly, enabling your application to update UI, trigger workflows, or allocate resources without delay.

## Getting Started with Aspose.Medical for .NET
First, add the Aspose.Medical package to your project:

```powershell
Install-Package Aspose.Medical
```

The library works with any .NET environment that supports .NET Standard. For detailed documentation, visit the [Aspose.Medical product page](https://products.aspose.com/medical/net/) and the official [API reference](https://reference.aspose.com/medical/net/).

## Step‑by‑Step Guide to Subscribing and Receiving UPS Events
Below is a complete C# example that demonstrates the entire flow—from creating the client to handling incoming UPS notifications.

**The following example shows how to subscribe to a worklist and receive UPS notifications using C#.**

```csharp
using System.Net.Http;
using Aspose.Medical.Dicom;
using Aspose.Medical.Dicom.Web;

// Create an HttpClient that will be reused for the DICOM Web client.
HttpClient httpClient = new HttpClient();

// Configure the base URI of your DICOMweb service.
DicomWebClientOptions options = new DicomWebClientOptions
{
    BaseUri = new System.Uri("https://dicom.example.com/dicomweb")
};

// Initialize the DICOM Web client.
DicomWebClient client = new DicomWebClient(httpClient, options);

// Subscribe to worklist notifications for a specific AE title.
await client.Worklist.SubscribeWorklistAsync(
    "MY_AE_TITLE",
    new DicomWebRequestOptions());

// Open a WebSocket connection that will deliver UPS notifications.
await using DicomWebNotificationConnection connection =
    await client.ConnectNotificationsAsync("MY_AE_TITLE");

// Continuously receive notifications until the server closes the connection.
while (await connection.ReceiveAsync() is Dataset notification)
{
    System.Console.WriteLine("Received UPS notification");
    // You can inspect the Dataset object here to extract details such as StudyInstanceUID.
}
```

**Explanation of the code**
1. **HttpClient** – A reusable HTTP client that underpins all DICOM Web calls.
2. **DicomWebClientOptions** – Sets the base URI of the DICOMweb endpoint.
3. **DicomWebClient** – The main entry point for DICOM operations such as worklist subscription and notification handling.
4. **SubscribeWorklistAsync** – Registers the client to receive worklist change events for the given AE title.
5. **ConnectNotificationsAsync** – Opens a WebSocket session that streams UPS notifications.
6. **ReceiveAsync** – Asynchronously reads each incoming `Dataset` representing a UPS event. The loop runs until the server terminates the connection.

The sample does not include any UI code; you can integrate the `while` loop into a background service, a hosted worker, or any asynchronous processing pipeline.

## Conclusion
By following the steps above, you can smoothly integrate Aspose.Medical’s WebSocket UPS notification feature into any C# application. This eliminates polling, reduces latency, and gives you immediate insight into worklist changes, which is essential for modern medical imaging workflows.

## FAQs
1. **What is a UPS notification in Aspose.Medical?** A UPS (Update Service) notification is a real‑time message sent over a WebSocket when a DICOM worklist changes, allowing clients to react immediately.
2. **Do I need a DICOM server to receive UPS notifications?** Yes, the client connects to a DICOMweb endpoint that implements the UPS notification service.
3. **Which .NET namespaces contain the required classes?** The APIs reside in `Aspose.Medical.Dicom` and `Aspose.Medical.Dicom.Web` namespaces.
4. **How can I handle multiple notifications efficiently?** Use an asynchronous loop with `ReceiveAsync` and process each `Dataset` as it arrives, keeping the connection open for the server's lifetime.
5. **Is there a way to filter which UPS events I receive?** The API delivers all notifications for the subscribed AE title; you can filter them in your code after they are received.
6. **Can I use this API in .NET Core or .NET Framework?** Aspose.Medical targets .NET Standard, so it works with both .NET Framework and .NET Core/.NET 5+ projects.

## Get a Free License and Explore More
Start experimenting with Aspose.Medical today by obtaining a temporary license:

[Get a Free Temporary License](https://purchase.aspose.com/temporary-license/)

- [Documentation Center](https://docs.aspose.com/medical/net/)
- [API Reference](https://reference.aspose.com/medical/net/)
- [Free Web Apps](https://products.aspose.app/medical/family)

