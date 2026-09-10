import json
from config import STATS_FILE

def get_audience_style():
    """Определяет стиль общения на основе статистики просмотров"""
    try:
        with open(STATS_FILE, "r") as f:
            stats = json.load(f)
    except FileNotFoundError:
        return "экспертный, дружелюбный"
    
    if not stats:
        return "экспертный, дружелюбный"
    
    views = [v.get("views", 0) for v in stats.values()]
    if not views:
        return "экспертный, дружелюбный"
    
    avg_views = sum(views) / len(views)
    
    if avg_views < 100:
        return "простой, понятный, с примерами"
    elif avg_views < 300:
        return "экспертный, но доступный"
    else:
        return "глубокий экспертный, с терминами и кейсами"
