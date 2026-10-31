
from ipaddress import ip_address
from urllib.parse import urlsplit


SUSPICIOUS_TERMS = {
    "login", "verify", "account", "password",
    "wallet", "secure", "update", "free-gift",
}


def analyze_url(url: str) -> dict:
    url = url.strip()

    if not url:
        return {
            "valid": False,
            "error": "Enter a URL to investigate.",
        }

    try:
        parsed = urlsplit(url)

        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or any(char.isspace() for char in url)
        ):
            raise ValueError("Enter a complete HTTP or HTTPS URL.")

        hostname = parsed.hostname.lower()
        score = 0
        findings = []

        # An IP address used as the hostname can deserve scrutiny.
        try:
            ip_address(hostname)
            score += 25
            findings.append(
                "The hostname is an IP address rather than a domain."
            )
        except ValueError:
            pass

        # Internationalized domain names can conceal lookalikes.
        if "xn--" in hostname:
            score += 25
            findings.append(
                "The domain contains an encoded internationalized label."
            )

        # User information before @ can obscure the displayed destination.
        if "@" in parsed.netloc:
            score += 20
            findings.append(
                "The URL contains user-information syntax (@)."
            )

        if len(hostname.split(".")) >= 5:
            score += 10
            findings.append(
                "The hostname contains many domain labels."
            )

        full_url = url.lower()
        matched_terms = sorted(
            term for term in SUSPICIOUS_TERMS
            if term in full_url
        )

        if matched_terms:
            score += min(20, 5 * len(matched_terms))
            findings.append(
                "Potentially sensitive terms appear in the URL: "
                + ", ".join(matched_terms)
            )

        if len(url) > 120:
            score += 10
            findings.append(
                "The URL is unusually long."
            )

        if parsed.scheme != "https":
            score += 5
            findings.append(
                "The URL uses HTTP rather than HTTPS."
            )

        score = min(score, 100)

        if score >= 70:
            level = "Critical"
        elif score >= 45:
            level = "High"
        elif score >= 20:
            level = "Moderate"
        else:
            level = "Low"

        if not findings:
            findings.append(
                "No configured URL warning indicators were detected."
            )

        return {
            "valid": True,
            "url": url,
            "hostname": hostname,
            "risk_score": score,
            "risk_level": level,
            "findings": findings,
            "method": "Local URL heuristics",
        }

    except ValueError as error:
        return {
            "valid": False,
            "error": str(error),
        }
