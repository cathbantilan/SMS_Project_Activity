import requests
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from .forms import SMSForm
from .models import SMSLog, IncomingSMS


def sync_incoming_sms():
    api_key = settings.TEXTBEE_API_KEY
    device_id = settings.TEXTBEE_DEVICE_ID
    if not all([api_key, device_id]):
        return

    url = f"https://textbee.dev{device_id}/get-received-sms"
    headers = {"x-api-key": api_key}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            items = response.json().get("data", [])
            for item in items:
                msg_id = str(item.get("_id", ""))
                if msg_id and not IncomingSMS.objects.filter(provider_id=msg_id).exists():
                    raw_time = item.get("receivedAt") or item.get("createdAt")
                    parsed_time = parse_datetime(raw_time) if raw_time else timezone.now()
                    IncomingSMS.objects.create(
                        sender=item.get("sender", "Unknown"),
                        message=item.get("message", ""),
                        provider_id=msg_id,
                        received_at=parsed_time or timezone.now(),
                    )
    except requests.RequestException as e:
        print("TEXTBEE SYNC ERROR:", repr(e))


def send_sms_view(request):
    sync_incoming_sms()
    logs = SMSLog.objects.order_by('-created_at')[:10]
    inbox = IncomingSMS.objects.order_by('-received_at')[:10]

    if request.method == 'POST':
        form = SMSForm(request.POST)
        if form.is_valid():
            recipient = form.cleaned_data['recipient']
            body = form.cleaned_data['message']

            api_key = settings.TEXTBEE_API_KEY
            device_id = settings.TEXTBEE_DEVICE_ID

            if not all([api_key, device_id]):
                messages.error(request, "SMS service credentials are not configured on the server.")
                return render(request, 'sms_app/index.html', {'form': form, 'logs': logs, 'inbox': inbox})

            url = "https://api.textbee.dev/api/v1/gateway/send-sms"
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
            }
            payload = {
                "recipients": [recipient],
                "message": body,
                "deviceId": device_id,
            }

            try:
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                if response.status_code in (200, 201):
                    data = response.json()
                    batch_id = data.get("data", {}).get("smsBatchId") or data.get("data", {}).get("_id", "")
                    SMSLog.objects.create(
                        recipient=recipient,
                        message=body,
                        status="Submitted (queued)",
                        provider_sid=str(batch_id)
                    )
                    messages.success(
                        request,
                        "Message submitted to provider (Status: queued). "
                        "Note: Final carrier delivery depends on recipient network availability."
                    )
                else:
                    print("TEXTBEE ERROR DETAIL:", response.status_code, response.text)
                    SMSLog.objects.create(
                        recipient=recipient,
                        message=body,
                        status="Failed (Provider Error)"
                    )
                    messages.error(
                        request,
                        f"Provider rejected the message (HTTP {response.status_code}). Check your API key or Device ID."
                    )
                return redirect('send_sms')

            except requests.RequestException as e:
                print("TEXTBEE NETWORK ERROR:", repr(e))
                SMSLog.objects.create(recipient=recipient, message=body, status="Failed (Network Error)")
                messages.error(request, f"Network Error: {e}")
                return redirect('send_sms')
    else:
        form = SMSForm()

    return render(request, 'sms_app/index.html', {'form': form, 'logs': logs, 'inbox': inbox})
