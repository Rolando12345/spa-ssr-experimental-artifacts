import requests


def server_online(url: str) -> bool:
    """
    Checks whether the target application endpoint is available.

    Parameters
    ----------
    url : str
        URL of the endpoint to verify.

    Returns
    -------
    bool
        True if the endpoint is reachable and returns
        a successful HTTP response; otherwise False.
    """

    try:

        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True
        )

        return response.ok

    except requests.RequestException:

        return False