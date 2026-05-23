"""Exception classes for the LinkedIn Jobs Scraper SDK."""


class LinkedInJobsError(Exception):
    """Base exception for all SDK errors."""


class AuthenticationError(LinkedInJobsError):
    """Raised when the Apify API token is missing or invalid."""


class ActorRunError(LinkedInJobsError):
    """Raised when the actor run fails on Apify infrastructure."""


class ActorTimeoutError(LinkedInJobsError):
    """Raised when the actor run does not finish within the allowed timeout."""
