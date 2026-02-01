"""Recipe parsing API endpoints."""

import os
import re
import json
import logging
from flask import Blueprint, request, jsonify

import requests

from services.auth import require_auth, get_current_user
from services.mcp_client import get_mcp_client
from services.db import get_db

logger = logging.getLogger(__name__)

recipes_bp = Blueprint('recipes', __name__, url_prefix='/recipes')

# Home Assistant configuration for Gemini
# Use supervisor URL when running as an addon
HA_URL = os.getenv('HA_URL', 'http://supervisor/core')
HA_TOKEN = os.getenv('SUPERVISOR_TOKEN', os.getenv('HA_LONG_LIVED_TOKEN', ''))


def call_gemini(prompt: str) -> str:
    """Call Gemini via Home Assistant conversation API."""
    if not HA_TOKEN:
        logger.warning("HA_LONG_LIVED_TOKEN not set, using fallback parsing")
        return None

    try:
        response = requests.post(
            f"{HA_URL}/api/services/conversation/process",
            json={
                "text": prompt,
                "agent_id": "conversation.google_generative_ai"
            },
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()

        # Extract response text
        speech = result.get('response', {}).get('speech', {})
        if isinstance(speech, dict):
            return speech.get('plain', {}).get('speech', '')
        return str(speech)

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


def parse_ingredients_with_gemini(text: str) -> list:
    """Use Gemini to parse ingredients into structured data."""
    prompt = f"""Parse the following ingredient list into a JSON array. For each ingredient, extract:
- original_text: the exact original text
- quantity: numeric quantity (null if not specified)
- unit: measurement unit (null if not specified)
- ingredient: the ingredient name
- search_term: best search term for a Dutch grocery store (in Dutch)

Return ONLY valid JSON array, no other text.

Ingredients:
{text}"""

    response = call_gemini(prompt)

    if response:
        try:
            # Clean markdown code blocks
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

    # Fallback: simple line-by-line parsing
    lines = text.strip().split('\n')
    ingredients = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            ingredients.append({
                'original_text': line,
                'quantity': None,
                'unit': None,
                'ingredient': line,
                'search_term': line.split()[-1] if line else ''
            })
    return ingredients


def fetch_recipe_from_url(url: str) -> dict:
    """Fetch and parse recipe from URL."""
    try:
        response = requests.get(
            url,
            timeout=30,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; PicnicBot/1.0)'}
        )
        response.raise_for_status()
        html = response.text

        # Try to extract structured data (JSON-LD)
        import re
        json_ld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        matches = re.findall(json_ld_pattern, html, re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match)

                # Handle array
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'Recipe':
                            return extract_recipe_from_schema(item, url)
                elif data.get('@type') == 'Recipe':
                    return extract_recipe_from_schema(data, url)
                elif '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == 'Recipe':
                            return extract_recipe_from_schema(item, url)
            except json.JSONDecodeError:
                continue

        # Fallback: use Gemini to extract
        prompt = f"""Extract the recipe information from this webpage. Return JSON with:
- title: recipe name
- ingredients: array of ingredient strings

URL: {url}

HTML (first 10000 chars):
{html[:10000]}

Return ONLY valid JSON."""

        response = call_gemini(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                data = json.loads(response.strip())
                return {
                    'title': data.get('title', 'Recipe'),
                    'ingredients': data.get('ingredients', []),
                    'source_url': url
                }
            except:
                pass

        return {'error': 'Could not parse recipe from URL'}

    except Exception as e:
        logger.error(f"Error fetching recipe: {e}")
        return {'error': str(e)}


def extract_recipe_from_schema(data: dict, url: str) -> dict:
    """Extract recipe from schema.org JSON-LD."""
    ingredients = data.get('recipeIngredient', [])
    if isinstance(ingredients, str):
        ingredients = [ingredients]

    return {
        'title': data.get('name', 'Recipe'),
        'ingredients': ingredients,
        'servings': data.get('recipeYield'),
        'source_url': url
    }


@recipes_bp.route('/parse-url', methods=['POST'])
@require_auth
def parse_url():
    """Parse recipe from URL."""
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'url is required'}), 400

    result = fetch_recipe_from_url(url)

    if 'error' in result:
        return jsonify(result), 400

    # Parse ingredients
    if result.get('ingredients'):
        ingredient_text = '\n'.join(result['ingredients'])
        parsed = parse_ingredients_with_gemini(ingredient_text)
        result['parsed_ingredients'] = parsed

    return jsonify(result)


@recipes_bp.route('/parse-text', methods=['POST'])
@require_auth
def parse_text():
    """Parse ingredients from plain text."""
    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({'error': 'text is required'}), 400

    parsed = parse_ingredients_with_gemini(text)
    return jsonify({'parsed_ingredients': parsed})


@recipes_bp.route('/match-products', methods=['POST'])
@require_auth
def match_products():
    """Match parsed ingredients to Picnic products."""
    data = request.get_json()
    ingredients = data.get('ingredients', [])

    if not ingredients:
        return jsonify({'matches': [], 'not_found': []})

    mcp = get_mcp_client()
    matches = []
    not_found = []

    for ingredient in ingredients:
        search_term = ingredient.get('search_term') or ingredient.get('ingredient', '')

        try:
            results = mcp.search_products(search_term)

            if isinstance(results, dict):
                products = results.get('products', results.get('items', []))
            elif isinstance(results, list):
                products = results
            else:
                products = []

            if products:
                matches.append({
                    'ingredient': ingredient,
                    'matches': products[:5],
                    'selected': products[0],
                    'status': 'matched'
                })
            else:
                matches.append({
                    'ingredient': ingredient,
                    'matches': [],
                    'selected': None,
                    'status': 'not_found'
                })
                not_found.append(ingredient)

        except Exception as e:
            logger.error(f"Error searching for {search_term}: {e}")
            matches.append({
                'ingredient': ingredient,
                'matches': [],
                'selected': None,
                'status': 'not_found'
            })
            not_found.append(ingredient)

    return jsonify({
        'matches': matches,
        'not_found': not_found
    })


@recipes_bp.route('/add-to-cart', methods=['POST'])
@require_auth
def add_to_cart():
    """Add matched recipe products to cart."""
    data = request.get_json()
    matches = data.get('matches', [])

    if not matches:
        return jsonify({'added': 0, 'failed': 0})

    mcp = get_mcp_client()
    added = 0
    failed = 0

    for match in matches:
        selected = match.get('selected')
        if selected:
            try:
                mcp.add_to_cart(selected['id'], 1)
                added += 1
            except:
                failed += 1

    cart = mcp.get_cart()
    return jsonify({
        'added': added,
        'failed': failed,
        'cart': cart
    })


@recipes_bp.route('/history', methods=['GET'])
@require_auth
def get_history():
    """Get recipe import history."""
    user = get_current_user()
    limit = request.args.get('limit', 20, type=int)

    db = get_db()
    with db.get_cursor() as cursor:
        if not cursor:
            return jsonify({'recipes': []})

        cursor.execute(
            """SELECT id, source_type, source_url, recipe_title,
                      parsed_ingredients, matched_products,
                      items_added_to_cart, created_at
               FROM recipe_history
               WHERE user_id = %s
               ORDER BY created_at DESC
               LIMIT %s""",
            (user['id'], limit)
        )
        recipes = cursor.fetchall()

    return jsonify({'recipes': [dict(r) for r in recipes] if recipes else []})


@recipes_bp.route('/save-history', methods=['POST'])
@require_auth
def save_history():
    """Save a recipe to history."""
    user = get_current_user()
    data = request.get_json()

    db = get_db()
    with db.get_cursor() as cursor:
        if not cursor:
            return jsonify({'error': 'Database not available'}), 503

        try:
            import json as json_module
            cursor.execute(
                """INSERT INTO recipe_history
                   (user_id, source_type, source_url, recipe_title,
                    parsed_ingredients, matched_products, items_added_to_cart)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (
                    user['id'],
                    data.get('source_type', 'url'),
                    data.get('source_url'),
                    data.get('recipe_title'),
                    json_module.dumps(data.get('parsed_ingredients', [])),
                    json_module.dumps(data.get('matched_products', [])),
                    data.get('items_added_to_cart', 0)
                )
            )
            result = cursor.fetchone()
            return jsonify({'success': True, 'id': str(result['id'])})

        except Exception as e:
            logger.error(f"Failed to save recipe history: {e}")
            return jsonify({'error': str(e)}), 500
