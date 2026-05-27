import re


def validate_pmid(pmid) -> str:
    """Validates that the given PMID is a valid PubMed ID. A valid PMID is a string of 1 to 8 digits.
    Raises a ValueError if the PMID is not valid."""
    pmid = str(pmid).strip()
    if not re.match(r'^\d{1,8}$', pmid):
        raise ValueError(f'Invalid PMID format: {pmid}')
    return pmid
