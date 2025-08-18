import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import yt_dlp

logger = logging.getLogger(__name__)


def extract_video_info(url):
    """Extract video information using yt-dlp without downloading"""
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', ''),
                'description': info.get('description', ''),
                'duration': info.get('duration', 0),  # in seconds
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),  # YYYYMMDD format
                'thumbnail': info.get('thumbnail', ''),
                'channel': info.get('uploader', ''),
                'channel_logo': info.get('uploader_avatar', ''),
            }
    except Exception as e:
        logger.error(f"Error extracting video info: {str(e)}")
        raise


@csrf_exempt
@require_http_methods(["POST"])
def get_video_info(request):
    """
    API endpoint to get YouTube video information
    """
    try:
        data = json.loads(request.body)
        url = data.get('url')

        if not url:
            return JsonResponse({'error': 'URL is required'}, status=400)

        video_info = extract_video_info(url)

        # Format duration as MM:SS
        minutes, seconds = divmod(video_info['duration'], 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            duration_formatted = f"{minutes:02d}:{seconds:02d}"

        # Format upload date
        upload_date = video_info['upload_date']
        if len(upload_date) == 8:  # YYYYMMDD
            formatted_date = f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[0:4]}"
        else:
            formatted_date = upload_date

        # Format view count
        views = video_info['view_count']
        if views >= 1000000:
            views_formatted = f"{views / 1000000:.1f}M views"
        elif views >= 1000:
            views_formatted = f"{views / 1000:.1f}K views"
        else:
            views_formatted = f"{views} views"

        response_data = {
            'title': video_info['title'],
            'description': video_info['description'],
            'duration': duration_formatted,
            'views': views_formatted,
            'date': formatted_date,
            'thumbnail': video_info['thumbnail'],
            'channel': video_info['channel'],
            'channelLogo': video_info['channel_logo'] or '',  # Handle None values
        }

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return JsonResponse({'error': f'Failed to process video: {str(e)}'}, status=500)