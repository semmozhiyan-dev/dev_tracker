"""
Trainer Module for DevTrackr

Provides motivational and coaching messages based on commit activity.
Features an aggressive, funny gym coach personality to keep you accountable! 💪
"""


def get_trainer_message(commits: int) -> dict:
    """
    Get a gym coach-style message based on today's commit count.
    
    The trainer responds differently based on your performance:
    - 0 commits: Harsh wake-up call (you slacker!)
    - 1-4 commits: Motivational push (keep grinding!)
    - 5+ commits: Celebration (absolute unit!)
    
    Args:
        commits (int): Number of commits made today
    
    Returns:
        dict: Contains 'message' (str) and 'style' (str: 'danger', 'warning', 'success')
    
    Examples:
        >>> get_trainer_message(0)
        {'message': '...harsh message...', 'style': 'danger'}
        
        >>> get_trainer_message(3)
        {'message': '...motivational message...', 'style': 'warning'}
        
        >>> get_trainer_message(8)
        {'message': '...celebration message...', 'style': 'success'}
    """
    
    if commits == 0:
        return {
            "message": "🪦 YOOO! You're DEAD, buddy! ZERO commits?! What are you doing with your life?! Get off the couch, stop scrolling TikTok, and START GRINDING! Your repo didn't push itself! 💀 NO EXCUSES! GO GO GO!",
            "style": "danger",
            "intensity": "MAXIMUM WARNING"
        }
    
    elif commits == 1:
        return {
            "message": "😅 ONE commit?! That's a start, I guess... like showing up to the gym and doing ONE push-up. Come on, champ! You can do BETTER than that! Let's GO! 🔥",
            "style": "warning",
            "intensity": "WAKE UP CALL"
        }
    
    elif commits == 2:
        return {
            "message": "💪 Two commits! Now we're talking! But don't get cocky - that's barely a warm-up! The day's young and your repo is HUNGRY! Push harder! More commits! LESSS GOOOO! 🚀",
            "style": "warning",
            "intensity": "GETTING WARMED UP"
        }
    
    elif commits == 3:
        return {
            "message": "🏋️ THREE commits?! Okay, you're getting your rhythm down! But this is where champions are made - RIGHT HERE, RIGHT NOW! Don't slow down, SPRINT to the finish line! 🔥💪",
            "style": "warning",
            "intensity": "IN THE ZONE"
        }
    
    elif commits == 4:
        return {
            "message": "💥 FOUR COMMITS! Look at you go! You're in the danger zone - one more and you're in the ELITE TIER! Just ONE more, buddy! You can TASTE SUCCESS! PUSH! 🎯",
            "style": "warning",
            "intensity": "ALMOST THERE"
        }
    
    elif commits >= 5 and commits < 8:
        return {
            "message": "🔥⚡ YESSIR! FIVE+ COMMITS! YOU ARE A BEAST! Look at that grind! That's the energy we NEED! You're out here making gains like a CHAMPION! Keep this up! 🏆💪",
            "style": "success",
            "intensity": "CRUSHING IT"
        }
    
    elif commits >= 8 and commits < 12:
        return {
            "message": "🚀🔥 ABSOLUTE UNIT! LOOK AT YOU GO! EIGHT+ COMMITS?! You're not just coding, you're DOMINATING! This is peak performance! You're a LEGEND in the making! 🏆👑",
            "style": "success",
            "intensity": "LEGENDARY STATUS"
        }
    
    else:  # commits >= 12
        return {
            "message": "👑🔥💎 WHAT?! TWELVE+ COMMITS?! ARE YOU EVEN HUMAN?! You absolute MADLAD! You're not grinding anymore, you're CRUSHING THE COMPETITION! HALL OF FAME STATUS! 🏆🚀🔥",
            "style": "success",
            "intensity": "GODLIKE PERFORMANCE"
        }
