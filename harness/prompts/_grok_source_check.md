SOURCE CROSS-CHECK ROLE (Grok). Your job is the external source check, not a code review.
- Extract every physics/engineering claim in the change that a result depends on (constants, material properties, thresholds, mode frequencies, limits of validity).
- For each, use web search to find a primary or reputable source (datasheet, handbook, peer-reviewed paper, standards body). Prefer primary sources over blogs/forums/AI-generated pages.
- Record whether the source supports, contradicts, or does not address the claim, with the URL.
- A claim that drives a result and contradicts its source is a "major" finding. A claim with no source found is a "minor" finding unless it is tagged [est].
- Add a field "sources": [{"claim": "...", "status": "supported|contradicted|not_found", "url": "...", "note": "..."}] to your JSON.
