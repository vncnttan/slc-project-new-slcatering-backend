from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt  # Duitku will send a POST request, which requires CSRF exemption
def payment_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))

            # Extract data from the POST request
            transaction_status = data.get('status', None)
            order_id = data.get('order_id', None)
            amount = data.get('amount', None)

            if transaction_status == 'success':
                # Handle success logic (e.g., marking order as paid)
                pass
            elif transaction_status == 'failed':
                # Handle failure logic
                pass

            return JsonResponse({'message': 'Callback received'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)