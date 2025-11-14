# ============================================================
# AI MATCHLAB — FIXTURES ENGINE
# Ανάκτηση & καθαρισμός HTML fixtures
# ============================================================

import re
from typing import Optional
from .provider_client import provider_client


class FixturesEngine:
    """
    Παίρνει HTML από εξωτερικές πηγές μέσω provider_client.get_html()
    Καθαρίζει το HTML από περιττές script/css
    Δίνει fallback αν δεν υπάρχει πρόσβαση
    """

    # ------------------------------------------------------------
    async def fetch_fixtures(self, url: str) -> str:
        """
        Παίρνει fixtures HTML μέσω HTTP.
        Επιστρέφει πάντα καθαρό HTML string ή fallback message.
        """
        html = await provider_client.get_html(url)

        if not html:
            return self.fallback_html()

        cleaned = self.clean_html(html)
        return cleaned or self.fallback_html()

    # ------------------------------------------------------------
    def clean_html(self, html: str) -> str:
        """
        Καθαρισμός περιττών script/style tags
        για σταθερή εμφάνιση μέσα στο iframe.
        """

        try:
            # Αφαίρεση CSS
            html = re.sub(r"<style.*?>.*?</style>", "", html, flags=re.DOTALL)

            # Αφαίρεση JS
            html = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.DOTALL)

            # Αφαίρεση meta refresh / redirects
            html = re.sub(r"<meta.*?>", "", html)

            return html

        except Exception as e:
            print(f"[FixturesEngine] ❌ clean_html error: {e}")
            return html

    # ------------------------------------------------------------
    def fallback_html(self) -> str:
        """
        HTML fallback αν δεν υπάρχει πρόσβαση στα fixtures.
        """
        return """
        <div style="padding:20px; font-family:sans-serif; color:#ccc;">
            <h3>⚠ Δεν ήταν δυνατή η φόρτωση των Fixtures</h3>
            <p>Παρακαλούμε προσπαθήστε ξανά σε λίγο.</p>
        </div>
        """


# Singleton instance
fixtures_engine = FixturesEngine()
