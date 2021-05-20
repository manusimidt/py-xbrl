"""
This module contains helper functions used by the unit test
"""


def get_bot_header() -> dict or None:
    try:
        f = open("./tests/.env", "r")
        from_header: str or None = None
        user_agent_header: str or None = None
        for line in f:
            env_name, env_value = [x.strip() for x in line.strip().split('=')]
            if env_name == 'FROM':
                from_header = env_value
            elif env_name == 'USER_AGENT':
                user_agent_header = env_value
        if from_header and user_agent_header:
            return {
                'From': from_header,
                'User-Agent': user_agent_header
            }
    except FileNotFoundError:
        return None
    return None
