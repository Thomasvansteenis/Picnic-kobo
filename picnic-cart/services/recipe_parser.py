"""Recipe parsing service with AI ingredient extraction."""

import os
import re
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from .mcp_client import get_mcp_client

logger = logging.getLogger(__name__)

# Home Assistant API configuration
HA_URL = os.getenv('HA_URL', 'http://supervisor/core')
HA_TOKEN = os.getenv('SUPERVISOR_TOKEN', '')

# Confidence thresholds
CONFIDENCE_HIGH = 0.7  # Auto-select
CONFIDENCE_MEDIUM = 0.4  # Show for review
CONFIDENCE_LOW = 0.2  # Uncertain, needs user verification

# Common ingredient synonyms and search term mappings (Dutch)
INGREDIENT_SYNONYMS = {
    'ei': ['eieren', 'ei'],
    'eieren': ['eieren', 'ei'],
    'bloem': ['bloem', 'tarwebloem', 'patentbloem'],
    'suiker': ['suiker', 'kristalsuiker', 'witte suiker'],
    'boter': ['boter', 'roomboter'],
    'melk': ['melk', 'volle melk'],
    'olie': ['olie', 'zonnebloemolie', 'olijfolie'],
    'olijfolie': ['olijfolie', 'olie'],
    'zout': ['zout', 'zeezout'],
    'peper': ['peper', 'zwarte peper'],
    'knoflook': ['knoflook', 'teentje knoflook'],
    'ui': ['ui', 'uien'],
    'uien': ['uien', 'ui'],
    'paprika': ['paprika', 'rode paprika', 'gele paprika'],
    'tomaat': ['tomaat', 'tomaten'],
    'tomaten': ['tomaten', 'tomaat'],
    'aardappel': ['aardappel', 'aardappelen', 'aardappels'],
    'aardappelen': ['aardappelen', 'aardappel'],
    'wortel': ['wortel', 'wortelen', 'wortels'],
    'sla': ['sla', 'kropsla', 'ijsbergsla'],
    'kaas': ['kaas', 'geraspte kaas'],
    'room': ['room', 'slagroom', 'kookroom'],
    'yoghurt': ['yoghurt', 'griekse yoghurt'],
    'kip': ['kip', 'kipfilet', 'kippenfilet'],
    'kipfilet': ['kipfilet', 'kip'],
    'gehakt': ['gehakt', 'rundergehakt', 'half-om-half gehakt'],
    'rijst': ['rijst', 'witte rijst', 'basmatirijst'],
    'pasta': ['pasta', 'spaghetti', 'penne'],
}

# Words to remove from search terms (Dutch articles, prepositions)
STOP_WORDS = {'de', 'het', 'een', 'van', 'met', 'voor', 'en', 'of', 'in', 'op', 'aan', 'te'}

# Words that indicate preparation method (should be stripped)
PREP_WORDS = {'gesneden', 'gehakt', 'fijngesneden', 'grof', 'fijn', 'vers', 'verse',
              'gedroogd', 'gedroogde', 'gekookt', 'gekookte', 'gebakken', 'geraspt',
              'geschild', 'gewassen', 'ontdooid', 'warm', 'koud', 'klein', 'grote', 'groot'}


@dataclass
class ParsedIngredient:
    """A parsed ingredient with quantity and unit."""
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    original_text: str = ''


@dataclass
class MatchedProduct:
    """A Picnic product matched to an ingredient."""
    ingredient: ParsedIngredient
    product_id: str
    product_name: str
    price: int
    image_url: Optional[str] = None
    confidence: float = 0.0
    suggested_quantity: int = 1


class RecipeParserService:
    """Service for parsing recipes and matching ingredients to products."""

    def __init__(self):
        self.mcp_client = get_mcp_client()

    def parse_url(self, url: str) -> Dict[str, Any]:
        """Parse a recipe from a URL."""
        try:
            # Fetch the page
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; PicnicRecipeParser/1.0)'
            })
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # Try to extract recipe title
            title = self._extract_title(soup, url)

            # Try to extract ingredients using common patterns
            ingredients_html = self._extract_ingredients_html(soup)

            # If we found ingredients in HTML, parse them
            if ingredients_html:
                ingredients = self._parse_ingredients_from_html(ingredients_html)
            else:
                # Fall back to AI extraction
                page_text = self._extract_recipe_text(soup)
                ingredients = self._extract_ingredients_with_ai(page_text)

            return {
                'success': True,
                'title': title,
                'url': url,
                'ingredients': [self._ingredient_to_dict(i) for i in ingredients],
                'raw_count': len(ingredients)
            }

        except Exception as e:
            logger.error(f"Failed to parse recipe URL: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    def parse_text(self, text: str) -> Dict[str, Any]:
        """Parse ingredients from plain text."""
        try:
            ingredients = self._extract_ingredients_with_ai(text)

            return {
                'success': True,
                'ingredients': [self._ingredient_to_dict(i) for i in ingredients],
                'raw_count': len(ingredients)
            }

        except Exception as e:
            logger.error(f"Failed to parse recipe text: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def match_products(
        self,
        ingredients: List[Dict],
        auto_add: bool = False
    ) -> Dict[str, Any]:
        """Match parsed ingredients to Picnic products with improved matching."""
        matches: List[Dict] = []
        not_found: List[Dict] = []
        needs_review: List[int] = []  # Indices of matches needing user review

        for ingredient in ingredients:
            name = ingredient.get('name', '')
            if not name:
                continue

            # Get normalized search terms
            search_terms = self._get_search_terms(name)
            all_results = []

            # Search with multiple terms to get better coverage
            for term in search_terms[:3]:  # Limit to 3 search attempts
                try:
                    results = self.mcp_client.search_products(term)
                    if results:
                        all_results.extend(results)
                except Exception as e:
                    logger.warning(f"Search failed for term '{term}': {e}")

            if all_results:
                # Remove duplicates and score all results
                scored_matches = self._score_all_matches(name, all_results)

                if scored_matches:
                    # Get top 5 matches with confidence scores
                    top_matches = scored_matches[:5]
                    best_match = top_matches[0]
                    best_confidence = best_match[0]

                    # Determine status based on confidence
                    if best_confidence >= CONFIDENCE_HIGH:
                        status = 'matched'
                    elif best_confidence >= CONFIDENCE_MEDIUM:
                        status = 'partial'
                        needs_review.append(len(matches))
                    else:
                        status = 'uncertain'
                        needs_review.append(len(matches))

                    match = {
                        'ingredient': ingredient,
                        'matches': [
                            {
                                'id': m[1].get('id'),
                                'name': m[1].get('name'),
                                'price': m[1].get('price'),
                                'image_url': m[1].get('image_url'),
                                'unit_quantity': m[1].get('unit_quantity'),
                                'confidence': round(m[0], 2)
                            }
                            for m in top_matches
                        ],
                        'status': status,
                        'best_confidence': round(best_confidence, 2),
                        'needs_review': best_confidence < CONFIDENCE_HIGH,
                        'suggested_quantity': self._suggest_quantity(ingredient, best_match[1])
                    }
                    matches.append(match)
                else:
                    not_found.append(ingredient)
            else:
                not_found.append(ingredient)

        result = {
            'matches': matches,
            'not_found': not_found,
            'needs_review_indices': needs_review,
            'total_ingredients': len(ingredients),
            'matched_count': len(matches),
            'high_confidence_count': sum(1 for m in matches if m['best_confidence'] >= CONFIDENCE_HIGH),
            'needs_review_count': len(needs_review),
            'estimated_total': sum(
                m['matches'][0]['price'] * m['suggested_quantity']
                for m in matches
                if m['matches'] and m['matches'][0].get('price')
            )
        }

        # Auto-add to cart only for high-confidence matches if requested
        if auto_add and matches:
            items_to_add = [
                {'productId': m['matches'][0]['id'], 'count': m['suggested_quantity']}
                for m in matches
                if m['matches'] and m['matches'][0].get('id') and m['best_confidence'] >= CONFIDENCE_HIGH
            ]

            if items_to_add:
                try:
                    add_result = self.mcp_client.bulk_add_to_cart(items_to_add)
                    result['cart_result'] = add_result
                except Exception as e:
                    logger.error(f"Failed to add items to cart: {e}")
                    result['cart_error'] = str(e)

        return result

    def _get_search_terms(self, ingredient_name: str) -> List[str]:
        """Generate multiple search terms for an ingredient."""
        terms = []
        name_lower = ingredient_name.lower().strip()

        # Clean the name: remove stop words and prep words
        words = name_lower.split()
        clean_words = [w for w in words if w not in STOP_WORDS and w not in PREP_WORDS]
        clean_name = ' '.join(clean_words) if clean_words else name_lower

        # Add the cleaned name first
        terms.append(clean_name)

        # Add original if different
        if name_lower != clean_name:
            terms.append(name_lower)

        # Check for synonyms
        for word in clean_words:
            if word in INGREDIENT_SYNONYMS:
                for synonym in INGREDIENT_SYNONYMS[word]:
                    if synonym not in terms:
                        terms.append(synonym)

        # Add individual important words if multi-word ingredient
        if len(clean_words) > 1:
            # Try the last word (often the main ingredient)
            terms.append(clean_words[-1])
            # Try first word if it's not a quantity descriptor
            if clean_words[0] not in {'halve', 'kwart', 'grote', 'kleine'}:
                terms.append(clean_words[0])

        return terms

    def _score_all_matches(self, ingredient_name: str, search_results: List[Dict]) -> List[Tuple[float, Dict]]:
        """Score and rank all search results for an ingredient."""
        ingredient_lower = ingredient_name.lower().strip()
        ingredient_words = set(w for w in ingredient_lower.split() if w not in STOP_WORDS)

        # Remove duplicates by product ID
        seen_ids = set()
        unique_results = []
        for result in search_results:
            pid = result.get('id')
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                unique_results.append(result)

        scored = []
        for result in unique_results:
            product_name = result.get('name', '').lower()
            product_words = set(product_name.split())
            score = 0.0

            # Exact substring match (ingredient in product name)
            if ingredient_lower in product_name:
                score += 0.5

            # Exact substring match (product key word in ingredient)
            key_product_words = product_words - STOP_WORDS
            for pw in key_product_words:
                if pw in ingredient_lower and len(pw) > 2:
                    score += 0.3
                    break

            # Word overlap scoring
            overlap = ingredient_words & product_words
            if overlap:
                # More overlap = better match
                overlap_ratio = len(overlap) / max(len(ingredient_words), 1)
                score += overlap_ratio * 0.3

            # Penalize very long product names (likely wrong product)
            if len(product_name) > 60:
                score -= 0.1

            # Penalize if product name has many extra words
            extra_words = len(product_words - ingredient_words)
            if extra_words > 5:
                score -= 0.1

            # Boost if product name is short and contains key ingredient word
            if len(product_name) < 30:
                for iw in ingredient_words:
                    if len(iw) > 3 and iw in product_name:
                        score += 0.1
                        break

            # Cap score at 1.0
            score = min(max(score, 0.0), 1.0)

            scored.append((score, result))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        return scored

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract recipe title from the page."""
        # Try schema.org Recipe
        recipe_schema = soup.find('script', type='application/ld+json')
        if recipe_schema:
            try:
                data = json.loads(recipe_schema.string)
                if isinstance(data, dict) and data.get('@type') == 'Recipe':
                    return data.get('name', '')
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Recipe':
                            return item.get('name', '')
            except:
                pass

        # Try common title elements
        for selector in ['h1.recipe-title', 'h1.wprm-recipe-name', 'h1[itemprop="name"]', 'h1']:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)

        # Fall back to page title
        if soup.title:
            return soup.title.string or ''

        return ''

    def _extract_ingredients_html(self, soup: BeautifulSoup) -> List[str]:
        """Extract ingredients from HTML structure."""
        ingredients = []

        # Try schema.org Recipe
        recipe_schema = soup.find('script', type='application/ld+json')
        if recipe_schema:
            try:
                data = json.loads(recipe_schema.string)
                if isinstance(data, dict) and data.get('@type') == 'Recipe':
                    return data.get('recipeIngredient', [])
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Recipe':
                            return item.get('recipeIngredient', [])
            except:
                pass

        # Try common ingredient list selectors
        selectors = [
            'li[itemprop="recipeIngredient"]',
            '.wprm-recipe-ingredient',
            '.ingredient-list li',
            '.ingredients li',
            '[class*="ingredient"] li',
            '.recipe-ingredients li'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 2:
                        ingredients.append(text)
                if ingredients:
                    return ingredients

        return ingredients

    def _parse_ingredients_from_html(self, ingredients_html: List[str]) -> List[ParsedIngredient]:
        """Parse ingredient strings into structured data."""
        parsed = []

        for text in ingredients_html:
            ingredient = self._parse_ingredient_text(text)
            if ingredient:
                parsed.append(ingredient)

        return parsed

    def _parse_ingredient_text(self, text: str) -> Optional[ParsedIngredient]:
        """Parse a single ingredient text into structured data."""
        text = text.strip()
        if not text:
            return None

        # Common patterns for quantity + unit + ingredient
        patterns = [
            # "2 el olijfolie" or "200 gram bloem"
            r'^(\d+(?:[.,]\d+)?)\s*(el|eetlepel|tl|theelepel|gram|g|kg|ml|l|liter|stuks?|st)\s+(.+)$',
            # "2 eieren" or "1 ui"
            r'^(\d+(?:[.,]\d+)?)\s+(.+)$',
            # Just ingredient name
            r'^(.+)$'
        ]

        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()

                if len(groups) == 3:
                    quantity = float(groups[0].replace(',', '.'))
                    unit = groups[1].lower()
                    name = groups[2]
                elif len(groups) == 2:
                    quantity = float(groups[0].replace(',', '.'))
                    unit = None
                    name = groups[1]
                else:
                    quantity = None
                    unit = None
                    name = groups[0]

                return ParsedIngredient(
                    name=name.strip(),
                    quantity=quantity,
                    unit=unit,
                    original_text=text
                )

        return None

    def _extract_recipe_text(self, soup: BeautifulSoup) -> str:
        """Extract relevant recipe text from the page."""
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # Get text content
        text = soup.get_text(separator='\n', strip=True)

        # Limit text length
        return text[:5000]

    def _extract_ingredients_with_ai(self, text: str) -> List[ParsedIngredient]:
        """Use Gemini via HA to extract ingredients from text."""
        if not HA_TOKEN:
            logger.warning("No HA token available, falling back to simple parsing")
            return self._simple_ingredient_extraction(text)

        try:
            # Call Home Assistant's conversation.process service
            prompt = f"""Extract the list of ingredients from this recipe text.
For each ingredient, provide:
- name: the ingredient name (e.g., "bloem", "eieren", "melk")
- quantity: the numeric quantity (or null if not specified)
- unit: the unit of measurement (e.g., "gram", "stuks", "el") or null

Return as JSON array. Only include food ingredients, not equipment or utensils.

Recipe text:
{text[:3000]}"""

            response = requests.post(
                f"{HA_URL}/api/conversation/process",
                headers={
                    'Authorization': f'Bearer {HA_TOKEN}',
                    'Content-Type': 'application/json'
                },
                json={
                    'text': prompt,
                    'agent_id': 'conversation.google_generative_ai'  # Gemini agent
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                speech = data.get('response', {}).get('speech', {}).get('plain', {}).get('speech', '')

                # Try to parse JSON from the response
                json_match = re.search(r'\[[\s\S]*\]', speech)
                if json_match:
                    ingredients_data = json.loads(json_match.group())
                    return [
                        ParsedIngredient(
                            name=item.get('name', ''),
                            quantity=item.get('quantity'),
                            unit=item.get('unit'),
                            original_text=item.get('name', '')
                        )
                        for item in ingredients_data
                        if item.get('name')
                    ]

        except Exception as e:
            logger.warning(f"AI extraction failed: {e}")

        # Fall back to simple extraction
        return self._simple_ingredient_extraction(text)

    def _simple_ingredient_extraction(self, text: str) -> List[ParsedIngredient]:
        """Simple rule-based ingredient extraction."""
        ingredients = []

        # Look for lines that look like ingredients
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line or len(line) < 3 or len(line) > 100:
                continue

            # Skip obvious non-ingredients
            skip_patterns = [
                r'^\d+\s*min',  # Time indicators
                r'^stap\s+\d',  # Step indicators
                r'^bereid',  # Preparation instructions
                r'^http',  # URLs
            ]

            if any(re.match(p, line, re.IGNORECASE) for p in skip_patterns):
                continue

            # Look for ingredient patterns
            if re.match(r'^\d+', line) or any(unit in line.lower() for unit in
                ['gram', 'el', 'tl', 'stuks', 'ml', 'liter', 'kg', 'eetlepel', 'theelepel']):
                parsed = self._parse_ingredient_text(line)
                if parsed:
                    ingredients.append(parsed)

        return ingredients

    def _find_best_match(self, ingredient_name: str, search_results: List[Dict]) -> Optional[Dict]:
        """Find the best matching product for an ingredient."""
        if not search_results:
            return None

        ingredient_lower = ingredient_name.lower()

        # Score each result
        scored = []
        for result in search_results:
            product_name = result.get('name', '').lower()
            score = 0

            # Exact match bonus
            if ingredient_lower in product_name:
                score += 10

            # Word overlap
            ingredient_words = set(ingredient_lower.split())
            product_words = set(product_name.split())
            overlap = len(ingredient_words & product_words)
            score += overlap * 2

            # Shorter names often better (more specific)
            if len(product_name) < 50:
                score += 1

            scored.append((score, result))

        # Return highest scored result
        scored.sort(key=lambda x: x[0], reverse=True)

        if scored and scored[0][0] > 0:
            return scored[0][1]

        # Return first result as fallback
        return search_results[0] if search_results else None

    def _calculate_confidence(self, ingredient_name: str, product_name: str) -> float:
        """Calculate match confidence between ingredient and product."""
        if not ingredient_name or not product_name:
            return 0.0

        ingredient_lower = ingredient_name.lower()
        product_lower = product_name.lower()

        # Exact match
        if ingredient_lower in product_lower:
            return 0.9

        # Word overlap
        ingredient_words = set(ingredient_lower.split())
        product_words = set(product_lower.split())
        overlap = len(ingredient_words & product_words)

        if overlap > 0:
            return min(0.3 + (overlap * 0.2), 0.8)

        return 0.3

    def _suggest_quantity(self, ingredient: Dict, product: Dict) -> int:
        """Suggest quantity to add based on ingredient and product."""
        # Simple logic - can be enhanced
        ingredient_qty = ingredient.get('quantity', 1) or 1
        unit = ingredient.get('unit', '')

        # For now, just suggest 1 unless quantity is large
        if ingredient_qty > 500 and unit in ['gram', 'g', 'ml']:
            return 2

        return 1

    def _ingredient_to_dict(self, ingredient: ParsedIngredient) -> Dict:
        """Convert ParsedIngredient to dictionary."""
        return {
            'name': ingredient.name,
            'quantity': ingredient.quantity,
            'unit': ingredient.unit,
            'original_text': ingredient.original_text
        }


# Global instance
_recipe_parser = None


def get_recipe_parser() -> RecipeParserService:
    """Get the recipe parser singleton."""
    global _recipe_parser
    if _recipe_parser is None:
        _recipe_parser = RecipeParserService()
    return _recipe_parser
