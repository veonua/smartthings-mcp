

from requests import Session
import logging

import requests

logger = logging.getLogger(__name__)


class CustomSession(Session):
    """
    Custom session class to handle session management for SmartThings API.
    This class is a placeholder for any custom session handling logic that may be needed.
    """

    def __init__(self, base_url:str, auth:str, **kwargs):
        self.base_url = base_url
        self.headers = {
            'Accept': 'application/vnd.smartthings+json;v=20170916',
            'Authorization': "Bearer " + auth,
            # 'cache-control': "no-cache",
        }
        super().__init__(**kwargs)

    def get(self, url, **kwargs):
        """
        Override the get method to add custom behavior if needed.
        """
        # Call the parent class's get method
        try:
            res = super().get(self.base_url + url, **kwargs)
            if res.status_code > 299:
                logger.error(f"GET request failed with status code {res.status_code}: {res.text}")
                res.raise_for_status()
            return res
        
        except Exception as e:
            # Handle exceptions as needed
            logger.error(f"Error occurred while making GET request: {e}")
            raise

    def post(self, url, data=None, json=None, **kwargs):
        """
        Override the post method to add custom behavior if needed.
        """
        # Call the parent class's post method
        try:
            logger.info(f"POST request to {self.base_url + url} with {data=} and {json=}")

            res = super().post(self.base_url + url, data=data, json=json, **kwargs)
            if res.status_code > 299:
                logger.error(f"POST request failed with status code {res.status_code}: {res.text}")
                res.raise_for_status()
            return res
        
        except Exception as e:
            # Handle exceptions as needed
            logger.error(f"Error occurred while making POST request: {e}")
            raise

    def get_json(self, url, **kwargs):
        """
        Convenience method to get JSON response from a GET request.
        """
        response = self.get(url, **kwargs)
        try:
            return response.json()
        except ValueError:
            logger.error(f"Failed to decode JSON from response: {response.text}")
            return {"error": "Failed to decode response", "status": response.status_code, "text": response.text}

    def post_json(self, url, data=None, json=None, **kwargs):
        """
        Convenience method to get JSON response from a POST request.
        """
        response = self.post(url, data=data, json=json, **kwargs)    
            
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            logger.error(f"Failed to decode JSON from response: {response.text}")
            return {"error": "Failed to decode response", "status": response.status_code, "text": response.text}
    
    def close(self):
        """
        Override the close method to ensure proper cleanup of the session.
        """
        super().close()
        # Add any additional cleanup logic if necessary
        # For example, clearing cookies or session data
        self.cookies.clear()
        self.headers.clear()