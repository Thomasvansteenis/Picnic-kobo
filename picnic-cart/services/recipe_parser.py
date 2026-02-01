"""Recipe parsing service with AI ingredient extraction."""

import os
import re
import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from .mcp_client import get_mcp_client

logger = logging.getLogger(__name__)

# Home Assistant API configuration
HA_URL = os.getenv('HA_URL', 'http://supervisor/core')
HA_TOKEN = os.getenv('SUPERVISOR_TOKEN', '')


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
        """Match parsed ingredients to Picnic products."""
        matches: List[Dict] = []
        not_found: List[Dict] = []

        for ingredient in ingredients:
            name = ingredient.get('name', '')
            if not name:
                continue

            # Search for the product
            try:
                search_results = self.mcp_client.search_products(name)

                if search_results and len(search_results) > 0:
                    # Get the best match
                    best_match = self._find_best_match(name, search_results)

                    if best_match:
                        match = {
                            'ingredient': ingredient,
                            'product': {
                                'id': best_match.get('id'),
                                'name': best_match.get('name'),
                                'price': best_match.get('price'),
                                'image_url': best_match.get('image_url'),
                                'unit_quantity': best_match.get('unit_quantity')
                            },
                            'confidence': self._calculate_confidence(name, best_match.get('name', '')),
                            'suggested_quantity': self._suggest_quantity(ingredient, best_match)
                        }
                        matches.append(match)
                    else:
                        not_found.append(ingredient)
                else:
                    not_found.append(ingredient)

            except Exception as e:
                logger.warning(f"Failed to search for ingredient '{name}': {e}")
                not_found.append(ingredient)

        result = {
            'matches': matches,
            'not_found': not_found,
            'total_ingredients': len(ingredients),
            'matched_count': len(matches),
            'estimated_total': sum(
                m['product']['price'] * m['suggested_quantity']
                for m in matches
                if m['product'].get('price')
            )
        }

        # Auto-add to cart if requested
        if auto_add and matches:
            items_to_add = [
                {'productId': m['product']['id'], 'count': m['suggested_quantity']}
                for m in matches
                if m['product'].get('id')
            ]

            if items_to_add:
                try:
                    add_result = self.mcp_client.bulk_add_to_cart(items_to_add)
                    result['cart_result'] = add_result
                except Exception as e:
                    logger.error(f"Failed to add items to cart: {e}")
                    result['cart_error'] = str(e)

        return result

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
