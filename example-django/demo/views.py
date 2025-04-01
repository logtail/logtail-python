import logging
from django.shortcuts import render
from django.http import HttpResponse

logger = logging.getLogger(__name__)

def index(request):
    logger.info('Accessed index page', extra={
        'request_path': request.path,
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
    })
    return render(request, 'index.html')

def trigger_error(request):
    try:
        # Intentionally raise an error
        raise ValueError("This is a test error")
    except Exception as e:
        logger.error('An error occurred', exc_info=True, extra={
            'request_path': request.path,
            'error_type': type(e).__name__
        })
        return HttpResponse("Error logged successfully!", status=500)

def trigger_warning(request):
    logger.warning('This is a test warning', extra={
        'request_path': request.path,
        'custom_data': {
            'test_key': 'test_value',
            'numbers': [1, 2, 3, 4, 5]
        }
    })
    return HttpResponse("Warning logged successfully!") 