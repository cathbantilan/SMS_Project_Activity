import re
from django import forms

class SMSForm(forms.Form):
    recipient = forms.CharField(
        label = "Recipient Phone Number",
        max_length = 20,
        widget = forms.TextInput(attrs = {
            'class': 'form-control',
            'placeholder': '+639171234567',
            'required': True
        })
    )
    message = forms.CharField(
        label = "Message",
        max_length = 500,
        widget = forms.Textarea(attrs = {
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Type your message here...',
            'id': 'messageInput',
            'required': True
        })
    )

    def clean_recipient(self):
        number = self.cleaned_data.get('recipient', '').strip()
        if not re.match(r'^\+[1-9]\d{7,14}$', number):
            raise forms.ValidationError(
                "Enter a valid phone number in E.164 format (e.g., +639171234567)."
            )
        return number

    def clean_message(self):
        msg = self.cleaned_data.get('message', '').strip()
        if not msg:
            raise forms.ValidationError("Message cannot be empty or whitespace only.")
        return msg  